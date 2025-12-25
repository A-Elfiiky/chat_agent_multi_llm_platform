from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
import time

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
from rag_client import RAGClient
from llm_provider import LLMRouter
from services.shared.config_utils import load_config
from services.shared.security import redactor
from services.shared.logger import logger as interaction_logger
from services.shared.conversation_memory import ConversationMemory
from services.shared.sentiment_analyzer import get_sentiment_analyzer
from services.shared.cache import ResponseCache
from services.shared.knowledge_gap_analyzer import KnowledgeGapAnalyzer
from services.shared.translation_service import get_translation_service
from services.shared.settings_service import get_settings_service
from services.shared.faq_answer_service import FAQAnswerService

app = FastAPI(title="Chat Orchestrator")
rag_client = RAGClient()
llm_router = LLMRouter()
config = load_config()
settings_service = get_settings_service()
memory = ConversationMemory()
sentiment_analyzer = get_sentiment_analyzer()
cache = ResponseCache(ttl_hours=24)  # Cache responses for 24 hours
gap_analyzer = KnowledgeGapAnalyzer()
translation_service = get_translation_service()
faq_answer_service = FAQAnswerService()


def _get_confidence_threshold() -> float:
    default_threshold = config['rag'].get('confidence_threshold', 0.35)
    stored = settings_service.get('confidence_threshold', default_threshold)
    try:
        threshold = float(stored)
    except (TypeError, ValueError):
        threshold = default_threshold
    return max(0.0, min(2.0, threshold))


def _calculate_response_confidence(top_score: Optional[float], threshold: float) -> float:
    if top_score is None:
        return 0.6  # default confidence when no RAG evidence
    if threshold <= 0:
        return 0.6
    ratio = threshold / max(top_score, 1e-6)
    confidence = max(0.1, min(1.0, ratio))
    return float(confidence)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class Citation(BaseModel):
    doc_id: str
    title: str
    section: str
    score: float

class AnswerEnvelope(BaseModel):
    answer_text: str
    citations: List[Citation]
    confidence: float
    model_id: str
    provider: str
    latency_ms: int
    notes: Optional[str] = None
    sentiment: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

@app.post("/chat", response_model=AnswerEnvelope)
async def chat(request: ChatRequest):
    start_time = time.time()
    
    # Detect and translate user's language
    user_message = request.message
    detected_lang, lang_confidence = translation_service.detect_language(user_message)
    user_lang = detected_lang
    print(f"🌍 Detected language: {user_lang} (confidence: {lang_confidence:.2f})")
    
    # Translate to English for processing if needed
    translated_question = user_message
    if user_lang != 'en':
        translation_result = translation_service.translate(
            text=user_message,
            target_lang='en',
            source_lang=user_lang
        )
        translated_question = translation_result['translated_text']
        print(f"🔄 Translated to English: {translated_question[:80]}...")
    
    # Create or retrieve session
    if not request.session_id:
        request.session_id = memory.create_session(client_id="anonymous")
    
    # Check cache first (only for non-conversational queries to avoid stale context)
    conversation_history = memory.get_conversation_history(request.session_id, limit=1)
    is_first_message = len(conversation_history) == 0
    
    if is_first_message:
        # Use English version for cache lookup
        cached_response = cache.get(translated_question)
        if cached_response:
            print(f"✅ Cache HIT for query: {translated_question[:50]}...")
            
            # Translate cached response back to user's language if needed
            answer_text = cached_response['answer_text']
            if user_lang != 'en':
                translation_result = translation_service.translate(
                    text=answer_text,
                    target_lang=user_lang,
                    source_lang='en'
                )
                cached_response['answer_text'] = translation_result['translated_text']
                print(f"🔄 Translated cached response to {user_lang}")
            
            end_time = time.time()
            cached_response['latency_ms'] = int((end_time - start_time) * 1000)
            cached_response['session_id'] = request.session_id
            cached_response['notes'] = f"Cached response (accessed {cached_response.get('access_count', 0)} times)"
            return AnswerEnvelope(**cached_response)
        else:
            print(f"❌ Cache MISS for query: {translated_question[:50]}...")
    else:
        print(f"⏭️  Skipping cache (conversational context)")
    
    # 0. Redact PII from Input Log (in a real app, we'd log the redacted version)
    redacted_message = redactor.redact(user_message)
    print(f"Processing query [{request.session_id}]: {redacted_message}") # Log redacted
    
    # Analyze sentiment (on original user message)
    sentiment_result = sentiment_analyzer.analyze(user_message)
    print(f"Sentiment: {sentiment_result['sentiment']} (score: {sentiment_result['score']:.2f})")
    
    if sentiment_result['needs_escalation']:
        print(f"⚠️  ESCALATION NEEDED - Flags: {', '.join(sentiment_result['flags'])}")
    
    if sentiment_result['is_urgent']:
        print(f"⏰ URGENT request detected")
    
    # Get conversation context for better follow-up handling
    conversation_context = memory.get_conversation_context(request.session_id)

    # Store user message in memory with sentiment and language info
    memory.add_message(
        session_id=request.session_id,
        role="user",
        content=user_message,
        metadata={
            "sentiment": sentiment_result['sentiment'],
            "sentiment_score": sentiment_result['score'],
            "needs_escalation": sentiment_result['needs_escalation'],
            "flags": sentiment_result['flags'],
            "language": user_lang,
            "translated_to_english": user_lang != 'en'
        }
    )

    # 1. Attempt curated FAQ answer before invoking the LLM stack
    faq_match = faq_answer_service.find_best_match(translated_question)
    if faq_match:
        faq_record = faq_match['faq']
        answer_text_en = faq_record['answer']
        answer_text = answer_text_en
        if user_lang != 'en':
            translation_result = translation_service.translate(
                text=answer_text_en,
                target_lang=user_lang,
                source_lang='en'
            )
            answer_text = translation_result['translated_text']

        latency_ms = int((time.time() - start_time) * 1000)
        faq_citation = Citation(
            doc_id=f"faq:{faq_record['id']}",
            title=faq_record['question'],
            section=faq_record.get('category') or 'FAQ',
            score=round(1.0 - faq_match['score'], 4)
        )
        faq_confidence = max(0.75, faq_match['score'])
        response_envelope = AnswerEnvelope(
            answer_text=answer_text,
            citations=[faq_citation],
            confidence=faq_confidence,
            model_id="faq-direct",
            provider="faq",
            latency_ms=latency_ms,
            notes="Answered via curated FAQ",
            sentiment=sentiment_result,
            session_id=request.session_id
        )

        memory.add_message(
            session_id=request.session_id,
            role="assistant",
            content=response_envelope.answer_text,
            confidence=response_envelope.confidence,
            metadata={
                "provider": "faq",
                "language": user_lang,
                "faq_id": faq_record['id']
            }
        )

        if is_first_message:
            cache.set(
                query=translated_question,
                response_data={
                    "answer_text": answer_text_en,
                    "citations": [faq_citation.dict()],
                    "confidence": faq_confidence,
                    "model_id": "faq-direct",
                    "provider": "faq",
                    "sentiment": sentiment_result
                },
                metadata={
                    "created_at": time.time(),
                    "source": "faq"
                }
            )

        interaction_logger.log_interaction(
            query=redacted_message,
            answer=response_envelope.answer_text,
            provider=response_envelope.provider,
            latency_ms=response_envelope.latency_ms,
            confidence=response_envelope.confidence,
            citations=response_envelope.citations
        )

        return response_envelope

    # 2. Retrieve Context (use English version for RAG)
    confidence_threshold = _get_confidence_threshold()
    rag_results = await rag_client.search(translated_question, k=config['rag']['retrieval_k'])
    filtered_results = [res for res in rag_results if res.get('score') is not None and res['score'] <= confidence_threshold]
    if filtered_results:
        rag_results = filtered_results
    elif rag_results:
        print(f"⚠️  No RAG chunks met confidence threshold ({confidence_threshold}); using best available results.")
    
    # Format context for LLM
    context_text = ""
    citations = []
    
    # Simple confidence check based on distance (lower is better for L2, but let's assume we normalize or use threshold)
    # For this prototype, we'll just take the top results.
    # In a real L2 index, distance can be > 1. Let's assume we trust the retrieval for now.
    
    for res in rag_results:
        chunk = res['chunk']
        score = res['score']
        context_text += f"Source (ID: {chunk['metadata']['id']}): {chunk['text']}\n\n"
        citations.append(Citation(
            doc_id=chunk['metadata']['id'],
            title=chunk['metadata']['title'],
            section=chunk['metadata']['section'],
            score=score
        ))

    top_score = rag_results[0]['score'] if rag_results else None
    response_confidence = _calculate_response_confidence(top_score, confidence_threshold)

    # 2. Construct Prompt with conversation context
    system_instruction = """You are a helpful customer service AI. 
    Answer the user's question strictly based on the provided context. 
    If the answer is not in the context, say "I don't have enough information to answer that."
    Do not hallucinate or make up facts.
    If the user is asking a follow-up question, use the previous conversation context to understand what they're referring to.
    """
    
    # Adjust tone based on sentiment
    tone_guidance = sentiment_analyzer.get_response_tone(sentiment_result)
    if tone_guidance == 'apologetic_professional':
        system_instruction += "\nIMPORTANT: The customer is upset. Be apologetic, professional, and offer immediate assistance."
    elif tone_guidance == 'empathetic_supportive':
        system_instruction += "\nIMPORTANT: The customer is frustrated. Show empathy and understanding."
    elif tone_guidance == 'prompt_helpful':
        system_instruction += "\nIMPORTANT: This is urgent. Provide quick, clear, and actionable answers."
    
    # Include conversation history if available
    full_prompt = ""
    if conversation_context:
        full_prompt += f"{conversation_context}\n\n"
    
    full_prompt += f"Context:\n{context_text}\n\nUser Question: {translated_question}"

    # 3. Generate Answer with Fallback
    generation_result = await llm_router.generate_answer(full_prompt, system_instruction)
    
    end_time = time.time()
    latency_ms = int((end_time - start_time) * 1000)

    response_envelope = None

    unanswered_note = None

    if generation_result['success']:
        # Translate answer back to user's language if needed
        answer_text = generation_result['answer']
        if user_lang != 'en':
            translation_result = translation_service.translate(
                text=answer_text,
                target_lang=user_lang,
                source_lang='en'
            )
            answer_text = translation_result['translated_text']
            print(f"🔄 Translated answer to {user_lang}")
        
        response_envelope = AnswerEnvelope(
            answer_text=answer_text,
            citations=citations,
            confidence=response_confidence,
            model_id="unknown",
            provider=generation_result['provider'],
            latency_ms=latency_ms,
            sentiment=sentiment_result,
            session_id=request.session_id
        )
        
        # Store assistant response in memory (translated version)
        memory.add_message(
            session_id=request.session_id,
            role="assistant",
            content=response_envelope.answer_text,  # Use the translated answer from envelope
            confidence=response_envelope.confidence,
            metadata={
                "provider": generation_result['provider'],
                "language": user_lang
            }
        )
        
        # Analyze response for knowledge gaps (using English versions)
        gap_analyzer.analyze_response(
            question=translated_question,
            answer=generation_result['answer'],  # English answer
            confidence=1.0,
            citations=citations
        )
        
        # Cache the response (only if first message in session, cache English version)
        if is_first_message:
            cache.set(
                query=translated_question,
                response_data={
                    "answer_text": generation_result['answer'],  # Cache English version
                    "citations": [c.dict() for c in response_envelope.citations],
                    "confidence": response_envelope.confidence,
                    "model_id": response_envelope.model_id,
                    "provider": response_envelope.provider,
                    "sentiment": sentiment_result
                },
                metadata={
                    "created_at": time.time(),
                    "sentiment": sentiment_result['sentiment']
                }
            )
            print(f"💾 Cached response for future use")
    else:
        # Fallback if all LLMs fail
        if rag_results:
            top_chunk = rag_results[0]['chunk']
            response_envelope = AnswerEnvelope(
                answer_text=f"I'm currently experiencing high traffic, but here is some information that might help:\n\n{top_chunk['text']}",
                citations=citations,
                confidence=0.5,
                model_id="rule-based",
                provider="fallback-rule",
                latency_ms=latency_ms,
                notes="LLM generation failed, returned raw chunk."
            )
        else:
             response_envelope = AnswerEnvelope(
                answer_text="I'm sorry, I'm currently unavailable and couldn't find relevant information.",
                citations=[],
                confidence=0.0,
                model_id="none",
                provider="none",
                latency_ms=latency_ms
            )
        unanswered_note = "llm_failure"

    if response_envelope and not unanswered_note:
        if response_envelope.confidence <= 0.4:
            unanswered_note = "low_confidence_llm"
        elif not citations:
            unanswered_note = "no_citations"

    if response_envelope and unanswered_note:
        gap_analyzer.record_unanswered_question(
            question=translated_question,
            confidence=response_envelope.confidence,
            notes=unanswered_note
        )
            
    # Log the interaction
    interaction_logger.log_interaction(
        query=redacted_message,
        answer=response_envelope.answer_text,
        provider=response_envelope.provider,
        latency_ms=response_envelope.latency_ms,
        confidence=response_envelope.confidence,
        citations=response_envelope.citations
    )
    
    return response_envelope

@app.get("/health")
async def health():
    return {"status": "healthy"}

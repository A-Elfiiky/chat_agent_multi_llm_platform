import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from .faq_repository import FAQRepository


class FAQAnswerService:
    """Lightweight matcher that routes questions to curated FAQs before hitting the LLM."""

    def __init__(
        self,
        repository: Optional[FAQRepository] = None,
        *,
        min_score: float = 0.72,
        max_candidates: int = 50,
    ) -> None:
        self.repository = repository or FAQRepository()
        self.min_score = max(0.1, min(0.95, min_score))
        self.max_candidates = max(10, min(max_candidates, 100))

    def find_best_match(self, question: str, *, status: str = "active") -> Optional[Dict[str, Any]]:
        if not question:
            return None

        normalized_question = question.strip()
        keywords = self._extract_keywords(normalized_question)

        candidates = self._fetch_candidates(normalized_question, status)
        if not candidates and keywords:
            truncated = " ".join(keywords[:4])
            candidates = self._fetch_candidates(truncated, status)
        if not candidates:
            candidates, _ = self.repository.list(
                page=1,
                page_size=self.max_candidates,
                status=status,
            )

        best_match: Optional[Dict[str, Any]] = None
        for candidate in candidates:
            score, matched_tags = self._score_candidate(normalized_question, keywords, candidate)
            payload = {
                "faq": candidate,
                "score": score,
                "matched_tags": matched_tags,
            }
            if best_match is None or score > best_match["score"]:
                best_match = payload

        if best_match and best_match["score"] >= self.min_score:
            best_match["score"] = round(best_match["score"], 4)
            return best_match
        return None

    def _fetch_candidates(self, search_term: str, status: str) -> List[Dict[str, Any]]:
        results, _ = self.repository.list(
            search=search_term,
            status=status,
            page=1,
            page_size=self.max_candidates,
        )
        return results

    def _score_candidate(
        self,
        question: str,
        keywords: List[str],
        candidate: Dict[str, Any],
    ) -> Tuple[float, List[str]]:
        candidate_question = (candidate.get("question") or "").strip()
        if not candidate_question:
            return 0.0, []

        base_score = SequenceMatcher(
            None,
            question.lower(),
            candidate_question.lower(),
        ).ratio()

        matched_tags: List[str] = []
        question_terms = set(keywords or self._extract_keywords(question))
        tags = candidate.get("tags") or []
        if tags and question_terms:
            for tag in tags:
                tag_value = str(tag).strip().lower()
                if tag_value and tag_value in question_terms:
                    matched_tags.append(tag)
        tag_bonus = min(0.12, 0.03 * len(matched_tags))

        # Encourage similar length questions but allow flexibility
        length_ratio = 1.0
        if candidate_question:
            length_ratio = len(question) / max(len(candidate_question), 1)
        length_penalty = min(0.08, abs(length_ratio - 1.0) * 0.04)

        final_score = max(0.0, min(1.0, base_score + tag_bonus - length_penalty))
        return final_score, matched_tags

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        if not text:
            return []
        return [token for token in re.findall(r"[a-z0-9']+", text.lower()) if len(token) > 2]
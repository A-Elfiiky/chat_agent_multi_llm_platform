# Multi-language Translation Setup

The AI Customer Service Platform now supports **20+ languages** with automatic detection and translation capabilities.

## Features

- ✅ **Automatic Language Detection** - Detects the user's language automatically
- ✅ **Translation Caching** - Caches translations to reduce API calls and costs
- ✅ **20+ Supported Languages** - English, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese, Arabic, Hindi, Turkish, Dutch, Polish, Swedish, Norwegian, Danish, Finnish, Greek
- ✅ **Pattern Matching Fallback** - Works even without translation libraries installed
- ✅ **Statistics Tracking** - Monitor language usage and translation performance

## Installation Options

### Option 1: googletrans (Recommended - Free, No API Key)

```powershell
pip install googletrans==4.0.0-rc1
```

This is a free library that uses Google Translate's web interface. No API key required.

### Option 2: deep-translator (Alternative)

```powershell
pip install deep-translator
```

Another free option with support for multiple translation services.

### Option 3: No Installation (Pattern Matching Fallback)

The system will still work without any translation library by using simple pattern matching for language detection. Translation will show warnings but won't break the system.

## How It Works

### 1. **Language Detection**
```python
detected_lang, confidence = translation_service.detect_language("Hola, ¿cómo estás?")
# Returns: ('es', 0.95)
```

### 2. **Automatic Translation**
When a user sends a message in Spanish:
1. System detects language: Spanish
2. Translates question to English for RAG processing
3. Retrieves relevant documents (in English knowledge base)
4. Generates answer in English
5. Translates answer back to Spanish
6. User receives answer in their language

### 3. **Translation Caching**
- Translations are cached in SQLite database
- Cache hit tracking to measure efficiency
- Automatic cleanup of old cache entries

## API Endpoints

### Get Translation Statistics
```http
GET /admin/translation/stats

Response:
{
  "total_cached_translations": 1250,
  "total_cache_hits": 3420,
  "cache_hit_rate": 0.73,
  "top_language_pairs": [
    {"source": "es", "target": "en", "count": 450},
    {"source": "en", "target": "es", "count": 420}
  ]
}
```

### Get Language Usage
```http
GET /admin/translation/languages?days=30

Response:
{
  "languages": [
    {
      "language_code": "es",
      "language_name": "Spanish",
      "detection_count": 850,
      "translation_count": 1700,
      "total_usage": 2550
    },
    {
      "language_code": "fr",
      "language_name": "French",
      "detection_count": 320,
      "translation_count": 640,
      "total_usage": 960
    }
  ],
  "total_languages": 8,
  "period_days": 30
}
```

### Get Supported Languages
```http
GET /admin/translation/supported-languages

Response:
{
  "supported_languages": {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    ...
  },
  "total": 20
}
```

### Manual Translation (Testing)
```http
POST /admin/translation/translate
Content-Type: application/json

{
  "text": "Hello, how can I help you?",
  "target_lang": "es",
  "source_lang": "en"
}

Response:
{
  "translated_text": "Hola, ¿cómo puedo ayudarte?",
  "source_lang": "en",
  "target_lang": "es",
  "method": "googletrans",
  "cached": false
}
```

### Cleanup Translation Cache
```http
POST /admin/translation/cleanup-cache?days=90

Response:
{
  "status": "success",
  "deleted_entries": 142,
  "message": "Cleaned up translation cache older than 90 days"
}
```

## Using the Chat API with Different Languages

### Example 1: Spanish User
```http
POST /chat
Content-Type: application/json

{
  "message": "¿Cuál es su política de devoluciones?",
  "session_id": "user-123"
}

Response:
{
  "answer_text": "Nuestra política de devoluciones permite...",
  "citations": [...],
  "confidence": 1.0,
  ...
}
```

The system automatically:
1. Detects Spanish
2. Translates question to English
3. Searches English knowledge base
4. Translates answer back to Spanish

### Example 2: Explicit Language Preference
```http
POST /chat
Content-Type: application/json

{
  "message": "What is your return policy?",
  "session_id": "user-456",
  "language": "fr"
}

Response:
{
  "answer_text": "Notre politique de retour permet...",
  ...
}
```

Forces answer to be in French regardless of input language.

## Performance Optimization

### Translation Cache Hit Rates
- **First request**: Translated via API/library (~100-300ms)
- **Cached requests**: Retrieved from database (~5-10ms)
- **Typical cache hit rate**: 60-80% after initial usage

### Cost Reduction
- Caching reduces translation API calls by 60-80%
- Pattern matching fallback eliminates dependency on paid services
- English-only knowledge base reduces storage and indexing costs

## Database Schema

### translation_cache Table
```sql
CREATE TABLE translation_cache (
    id INTEGER PRIMARY KEY,
    text_hash TEXT NOT NULL,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    source_text TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    translation_method TEXT,
    created_at REAL,
    hit_count INTEGER DEFAULT 0,
    UNIQUE(text_hash, source_lang, target_lang)
)
```

### language_stats Table
```sql
CREATE TABLE language_stats (
    id INTEGER PRIMARY KEY,
    language_code TEXT NOT NULL,
    detection_count INTEGER DEFAULT 0,
    translation_count INTEGER DEFAULT 0,
    last_used REAL,
    UNIQUE(language_code)
)
```

## Troubleshooting

### Translation Library Not Found
**Symptom**: Warning message about missing translation libraries

**Solution**:
```powershell
pip install googletrans==4.0.0-rc1
```

Or install alternative:
```powershell
pip install deep-translator
```

### Low Cache Hit Rate
**Symptom**: High translation costs, slow responses

**Possible Causes**:
- Users asking very diverse questions
- Cache was recently cleared
- Translation cache table not indexed properly

**Solution**:
- Let system run for a few days to build cache
- Check cache statistics: `GET /admin/translation/stats`
- Verify database indexes exist

### Incorrect Language Detection
**Symptom**: System detects wrong language

**Possible Causes**:
- Very short messages (1-2 words)
- Mixed language input
- Uncommon language variants

**Solution**:
- Use explicit `language` parameter in chat request
- Minimum 5-10 words for accurate detection
- Check supported languages list

## Best Practices

1. **Cache Management**
   - Clean up old cache entries periodically (90+ days)
   - Monitor cache hit rates
   - Keep frequently used translations

2. **Language Detection**
   - Works best with 5+ words
   - More accurate with complete sentences
   - Consider explicit language param for critical applications

3. **Knowledge Base**
   - Keep knowledge base in English only
   - Add multilingual FAQs if needed for specific markets
   - Translation handles user-facing content

4. **Monitoring**
   - Track language usage trends
   - Monitor translation performance
   - Review cache hit rates weekly

## Integration Examples

### Python Client
```python
import requests

# Spanish question
response = requests.post(
    "http://localhost:8001/chat",
    json={
        "message": "¿Cómo puedo rastrear mi pedido?",
        "session_id": "customer-789"
    }
)

print(response.json()['answer_text'])
# Output in Spanish: "Puede rastrear su pedido..."
```

### JavaScript Client
```javascript
const response = await fetch('http://localhost:8001/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Comment puis-je suivre ma commande?",
    session_id: "customer-123"
  })
});

const data = await response.json();
console.log(data.answer_text);
// Output in French: "Vous pouvez suivre votre commande..."
```

## Future Enhancements

- [ ] Add support for more languages (50+)
- [ ] Implement language-specific knowledge bases
- [ ] Add translation quality scoring
- [ ] Support for regional dialects
- [ ] Voice input translation
- [ ] Custom terminology dictionaries
- [ ] Translation memory for consistency

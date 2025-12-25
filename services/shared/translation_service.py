"""
Multi-language Translation Service
Provides language detection and translation capabilities for international customer support.

Features:
- Automatic language detection
- Translation to/from multiple languages
- Caching of translations
- Support for both Google Translate API and local models
"""

import os
from typing import Optional, Dict, List, Tuple
import sqlite3
from datetime import datetime, timedelta
import hashlib

class TranslationService:
    """
    Handles language detection and translation for customer service interactions.
    
    Supports multiple translation backends:
    - Google Translate API (recommended for production)
    - LibreTranslate (open-source alternative)
    - Local fallback using language patterns
    """
    
    # Supported languages with their codes
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'tr': 'Turkish',
        'nl': 'Dutch',
        'pl': 'Polish',
        'sv': 'Swedish',
        'no': 'Norwegian',
        'da': 'Danish',
        'fi': 'Finnish',
        'el': 'Greek'
    }
    
    def __init__(self, db_path: str = "data/copilot.db", api_key: Optional[str] = None):
        """
        Initialize translation service.
        
        Args:
            db_path: Path to SQLite database for caching translations
            api_key: Optional Google Translate API key (if None, uses fallback)
        """
        self.db_path = db_path
        self.api_key = api_key or os.getenv('GOOGLE_TRANSLATE_API_KEY')
        self.use_api = bool(self.api_key)
        self._init_database()
        
        # Try to import translation libraries
        self.translator = None
        self._init_translator()
    
    def _init_database(self):
        """Initialize database tables for translation cache."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Translation cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translation_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        """)
        
        # Language usage statistics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS language_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language_code TEXT NOT NULL,
                detection_count INTEGER DEFAULT 0,
                translation_count INTEGER DEFAULT 0,
                last_used REAL,
                UNIQUE(language_code)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_translation_hash 
            ON translation_cache(text_hash, source_lang, target_lang)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_language_stats_code 
            ON language_stats(language_code)
        """)
        
        conn.commit()
        conn.close()
    
    def _init_translator(self):
        """Initialize translation backend (Google Translate or fallback)."""
        try:
            # Try to use googletrans library (free, no API key needed)
            from googletrans import Translator
            self.translator = Translator()
            self.translation_method = 'googletrans'
            print("✓ Translation service initialized with googletrans")
        except ImportError:
            try:
                # Fallback to deep-translator
                from deep_translator import GoogleTranslator
                self.translator = GoogleTranslator
                self.translation_method = 'deep_translator'
                print("✓ Translation service initialized with deep-translator")
            except ImportError:
                print("⚠ No translation library found. Install: pip install googletrans==4.0.0-rc1")
                print("   Or: pip install deep-translator")
                self.translation_method = 'none'
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of input text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (language_code, confidence)
        """
        if not text or not text.strip():
            return ('en', 1.0)
        
        # Try using translator for detection
        if self.translator and self.translation_method == 'googletrans':
            try:
                detection = self.translator.detect(text)
                lang_code = detection.lang
                confidence = detection.confidence
                
                # Update stats
                self._update_language_stats(lang_code, detection_count=1)
                
                return (lang_code, confidence)
            except Exception as e:
                print(f"Language detection error: {e}")
        
        # Fallback: simple pattern-based detection
        lang_code = self._simple_language_detection(text)
        self._update_language_stats(lang_code, detection_count=1)
        return (lang_code, 0.7)
    
    def _simple_language_detection(self, text: str) -> str:
        """
        Simple pattern-based language detection as fallback.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language code
        """
        text_lower = text.lower()
        
        # Common word patterns for different languages
        patterns = {
            'es': ['el', 'la', 'los', 'las', 'de', 'del', 'por', 'para', 'con', 'sin', 'está', 'son', 'qué', 'cómo'],
            'fr': ['le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'est', 'sont', 'que', 'qui', 'avec'],
            'de': ['der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'und', 'ist', 'sind', 'wie', 'was'],
            'it': ['il', 'la', 'lo', 'i', 'gli', 'le', 'di', 'da', 'in', 'con', 'per', 'che', 'come', 'è'],
            'pt': ['o', 'a', 'os', 'as', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'por', 'para', 'com'],
            'ru': ['и', 'в', 'не', 'на', 'я', 'что', 'он', 'как', 'с', 'это', 'по', 'но', 'они'],
            'ar': ['من', 'في', 'على', 'إلى', 'هذا', 'هذه', 'ما', 'أن', 'كان', 'قد', 'لا'],
            'zh': ['的', '了', '是', '我', '你', '他', '她', '在', '有', '个', '这', '那', '和'],
            'ja': ['は', 'の', 'を', 'に', 'が', 'で', 'と', 'も', 'から', 'まで', 'です', 'ます'],
            'ko': ['은', '는', '이', '가', '을', '를', '에', '의', '와', '과', '도', '입니다'],
        }
        
        # Count matches for each language
        scores = {}
        words = text_lower.split()
        
        for lang, keywords in patterns.items():
            score = sum(1 for word in words if word in keywords)
            if score > 0:
                scores[lang] = score
        
        # Return language with highest score, or 'en' as default
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return 'en'
    
    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_lang: Target language code (e.g., 'es', 'fr')
            source_lang: Source language code (auto-detect if None)
            
        Returns:
            Dict with:
                - translated_text: Translated text
                - source_lang: Detected/specified source language
                - target_lang: Target language
                - method: Translation method used
                - cached: Whether result was from cache
        """
        if not text or not text.strip():
            return {
                'translated_text': text,
                'source_lang': source_lang or 'en',
                'target_lang': target_lang,
                'method': 'none',
                'cached': False
            }
        
        # Detect source language if not provided
        if not source_lang:
            source_lang, _ = self.detect_language(text)
        
        # No translation needed if source and target are the same
        if source_lang == target_lang:
            return {
                'translated_text': text,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'method': 'none',
                'cached': False
            }
        
        # Check cache first
        cached_result = self._get_cached_translation(text, source_lang, target_lang)
        if cached_result:
            return {
                'translated_text': cached_result,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'method': self.translation_method,
                'cached': True
            }
        
        # Perform translation
        translated_text = self._perform_translation(text, source_lang, target_lang)
        
        # Cache the result
        self._cache_translation(text, source_lang, target_lang, translated_text)
        
        # Update stats
        self._update_language_stats(source_lang, translation_count=1)
        self._update_language_stats(target_lang, translation_count=1)
        
        return {
            'translated_text': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'method': self.translation_method,
            'cached': False
        }
    
    def _perform_translation(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Perform actual translation using available backend.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        if not self.translator:
            # No translator available, return original text with warning
            return f"[Translation unavailable: {source_lang} → {target_lang}] {text}"
        
        try:
            if self.translation_method == 'googletrans':
                result = self.translator.translate(text, src=source_lang, dest=target_lang)
                return result.text
            
            elif self.translation_method == 'deep_translator':
                translator = self.translator(source=source_lang, target=target_lang)
                return translator.translate(text)
            
        except Exception as e:
            print(f"Translation error ({source_lang} → {target_lang}): {e}")
            return f"[Translation error] {text}"
        
        return text
    
    def _get_cached_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        """
        Retrieve cached translation if available.
        
        Args:
            text: Original text
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            Cached translation or None
        """
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT translated_text FROM translation_cache
            WHERE text_hash = ? AND source_lang = ? AND target_lang = ?
        """, (text_hash, source_lang, target_lang))
        
        result = cursor.fetchone()
        
        if result:
            # Increment hit count
            cursor.execute("""
                UPDATE translation_cache
                SET hit_count = hit_count + 1
                WHERE text_hash = ? AND source_lang = ? AND target_lang = ?
            """, (text_hash, source_lang, target_lang))
            conn.commit()
        
        conn.close()
        
        return result[0] if result else None
    
    def _cache_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translated_text: str
    ):
        """
        Cache a translation for future use.
        
        Args:
            text: Original text
            source_lang: Source language
            target_lang: Target language
            translated_text: Translated text
        """
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO translation_cache
            (text_hash, source_lang, target_lang, source_text, translated_text, 
             translation_method, created_at, hit_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            text_hash,
            source_lang,
            target_lang,
            text,
            translated_text,
            self.translation_method,
            datetime.now().timestamp()
        ))
        
        conn.commit()
        conn.close()
    
    def _update_language_stats(
        self,
        language_code: str,
        detection_count: int = 0,
        translation_count: int = 0
    ):
        """
        Update language usage statistics.
        
        Args:
            language_code: Language code
            detection_count: Number of detections to add
            translation_count: Number of translations to add
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO language_stats (language_code, detection_count, translation_count, last_used)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(language_code) DO UPDATE SET
                detection_count = detection_count + ?,
                translation_count = translation_count + ?,
                last_used = ?
        """, (
            language_code,
            detection_count,
            translation_count,
            datetime.now().timestamp(),
            detection_count,
            translation_count,
            datetime.now().timestamp()
        ))
        
        conn.commit()
        conn.close()
    
    def get_language_stats(self, days: int = 30) -> List[Dict]:
        """
        Get language usage statistics.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of language statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        
        cursor.execute("""
            SELECT 
                language_code,
                detection_count,
                translation_count,
                last_used
            FROM language_stats
            WHERE last_used >= ?
            ORDER BY (detection_count + translation_count) DESC
        """, (cutoff,))
        
        stats = []
        for row in cursor.fetchall():
            stats.append({
                'language_code': row[0],
                'language_name': self.SUPPORTED_LANGUAGES.get(row[0], 'Unknown'),
                'detection_count': row[1],
                'translation_count': row[2],
                'last_used': datetime.fromtimestamp(row[3]).isoformat(),
                'total_usage': row[1] + row[2]
            })
        
        conn.close()
        return stats
    
    def get_cache_stats(self) -> Dict:
        """
        Get translation cache statistics.
        
        Returns:
            Cache statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total cached translations
        cursor.execute("SELECT COUNT(*) FROM translation_cache")
        total_cached = cursor.fetchone()[0]
        
        # Total cache hits
        cursor.execute("SELECT SUM(hit_count) FROM translation_cache")
        total_hits = cursor.fetchone()[0] or 0
        
        # Most frequently cached translations
        cursor.execute("""
            SELECT source_lang, target_lang, COUNT(*) as count
            FROM translation_cache
            GROUP BY source_lang, target_lang
            ORDER BY count DESC
            LIMIT 10
        """)
        
        language_pairs = []
        for row in cursor.fetchall():
            language_pairs.append({
                'source': row[0],
                'target': row[1],
                'count': row[2]
            })
        
        conn.close()
        
        return {
            'total_cached_translations': total_cached,
            'total_cache_hits': total_hits,
            'cache_hit_rate': round(total_hits / max(total_cached, 1), 2),
            'top_language_pairs': language_pairs
        }
    
    def cleanup_old_cache(self, days: int = 90) -> int:
        """
        Remove old cached translations.
        
        Args:
            days: Remove cache entries older than this
            
        Returns:
            Number of entries deleted
        """
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM translation_cache
            WHERE created_at < ? AND hit_count = 0
        """, (cutoff,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted


# Singleton instance
_translation_service = None

def get_translation_service() -> TranslationService:
    """Get or create singleton translation service instance."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service

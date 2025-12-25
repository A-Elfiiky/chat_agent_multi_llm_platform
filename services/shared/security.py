import re
from typing import List

class PIIRedactor:
    def __init__(self):
        # Regex patterns for common PII
        self.patterns = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
            'ssn': r'\d{3}-\d{2}-\d{4}',
            'credit_card': r'\b(?:\d[ -]*?){13,16}\b'
        }

    def redact(self, text: str, patterns_to_redact: List[str] = None) -> str:
        if not text:
            return text
            
        if patterns_to_redact is None:
            patterns_to_redact = ['email', 'phone', 'ssn', 'credit_card']

        redacted_text = text
        for p_name in patterns_to_redact:
            if p_name in self.patterns:
                pattern = self.patterns[p_name]
                redacted_text = re.sub(pattern, f"[{p_name.upper()}_REDACTED]", redacted_text)
        
        return redacted_text

# Singleton instance
redactor = PIIRedactor()

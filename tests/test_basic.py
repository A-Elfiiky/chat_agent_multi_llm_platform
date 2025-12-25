import unittest
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.shared.security import redactor
# Note: We need to handle the import path for ingestion-indexer carefully as it has a hyphen
# For this test, we'll just test the shared module to avoid complex path hacking in the test runner
# from services.ingestion_indexer.ingestor import IngestionEngine 

class TestSecurity(unittest.TestCase):
    def test_redaction(self):
        text = "My email is test@example.com and phone is 123-456-7890"
        redacted = redactor.redact(text)
        self.assertIn("[EMAIL_REDACTED]", redacted)
        self.assertIn("[PHONE_REDACTED]", redacted)
        self.assertNotIn("test@example.com", redacted)

if __name__ == '__main__':
    unittest.main()

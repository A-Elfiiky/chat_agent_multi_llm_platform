import gc
import os
import tempfile
import unittest

from services.shared.faq_repository import FAQRepository
from services.shared.faq_answer_service import FAQAnswerService
from services.shared.knowledge_gap_analyzer import KnowledgeGapAnalyzer


class FAQAnswerServiceTestCase(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.repo = FAQRepository(self.db_path)
        self.answer_service = FAQAnswerService(self.repo, min_score=0.55, max_candidates=25)

        self.password_faq = self.repo.create(
            question="How can I reset my password?",
            answer="Visit the profile page and click \"Reset password\".",
            category="Accounts",
            tags=["password", "login"],
            status="active"
        )
        self.refund_faq = self.repo.create(
            question="How do I request a refund for an order?",
            answer="Contact support with your order ID within 30 days.",
            category="Billing",
            tags=["refund", "orders"],
            status="active"
        )

    def tearDown(self):
        self.answer_service = None
        self.repo = None
        gc.collect()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def test_best_match_returns_expected_faq(self):
        result = self.answer_service.find_best_match("How can I reset my password?")
        self.assertIsNotNone(result)
        self.assertEqual(result["faq"]["id"], self.password_faq["id"])
        self.assertGreaterEqual(result["score"], 0.55)

    def test_match_respects_threshold(self):
        strict_service = FAQAnswerService(self.repo, min_score=0.9, max_candidates=10)
        result = strict_service.find_best_match("Tell me about loyalty rewards")
        self.assertIsNone(result)


class KnowledgeGapAnalyzerTestCase(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.analyzer = KnowledgeGapAnalyzer(db_path=self.db_path, confidence_threshold=0.5)

    def tearDown(self):
        self.analyzer = None
        gc.collect()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def test_record_unanswered_question_tracks_frequency(self):
        question = "How do I upgrade my subscription plan?"
        self.analyzer.record_unanswered_question(question, confidence=0.2, notes="llm_failure")
        self.analyzer.record_unanswered_question(question, confidence=0.6)

        gaps = self.analyzer.get_knowledge_gaps(min_frequency=1, days=30)
        matching = next((gap for gap in gaps if gap['question'] == question), None)
        self.assertIsNotNone(matching)
        self.assertEqual(matching['ask_count'], 2)
        self.assertAlmostEqual(matching['avg_confidence'], 0.4, places=2)


if __name__ == "__main__":
    unittest.main()

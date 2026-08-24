"""Regression tests không cần API key cho toàn bộ bốn bước của lab."""
import importlib
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from utils.data_loader import build_vectorstore, load_knowledge_base, split_text


step1 = importlib.import_module("01_langsmith_rag_pipeline")
step2 = importlib.import_module("02_prompt_hub_ab_routing")
step3 = importlib.import_module("03_ragas_evaluation")
step4 = importlib.import_module("04_guardrails_validator")


class TestDataAndRag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = load_knowledge_base()
        cls.chunks = split_text(text, chunk_size=500, chunk_overlap=50)
        cls.vectorstore = build_vectorstore(
            cls.chunks, DeterministicFakeEmbedding(size=64)
        )

    def test_knowledge_base_is_chunked_and_searchable(self):
        self.assertGreater(len(self.chunks), 10)
        docs = self.vectorstore.similarity_search("What is RAG?", k=3)
        self.assertEqual(len(docs), 3)
        self.assertTrue(all(doc.page_content for doc in docs))

    def test_step1_lcel_chain(self):
        original = step1.get_llm
        step1.get_llm = lambda: FakeListChatModel(responses=["grounded answer"])
        try:
            chain, retriever = step1.build_rag_chain(self.vectorstore)
            self.assertEqual(chain.invoke("What is RAG?"), "grounded answer")
            self.assertEqual(len(retriever.invoke("What is RAG?")), 3)
        finally:
            step1.get_llm = original

    def test_step2_router_and_query(self):
        ids = [f"req-{i:04d}" for i in range(50)]
        versions = [step2.get_prompt_version(request_id) for request_id in ids]
        self.assertIn(step2.PROMPT_V1_NAME, versions)
        self.assertIn(step2.PROMPT_V2_NAME, versions)
        self.assertEqual(
            step2.get_prompt_version(ids[0]), step2.get_prompt_version(ids[0])
        )

        result = step2.ask_ab(
            self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            FakeListChatModel(responses=["A/B answer"]),
            step2.PROMPT_V1,
            "What is FAISS?",
            "v1",
        )
        self.assertEqual(result["answer"], "A/B answer")
        self.assertEqual(result["version"], "v1")

    def test_step3_output_and_dataset_mapping(self):
        out = step3.run_rag(
            self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            FakeListChatModel(responses=["evaluation answer"]),
            step3.PROMPT_V1,
            "What is LangSmith?",
        )
        self.assertEqual(out["answer"], "evaluation answer")
        self.assertEqual(len(out["contexts"]), 3)

        dataset = step3.build_ragas_dataset([{
            "question": "question",
            "answer": "answer",
            "contexts": ["context"],
            "reference": "reference",
        }])
        sample = dataset[0]
        self.assertEqual(sample.user_input, "question")
        self.assertEqual(sample.retrieved_contexts, ["context"])


class TestGuardrails(unittest.TestCase):
    def test_pii_redaction(self):
        result = step4.PIIDetector().validate(
            "Email a@example.com or call (555) 867-5309.", {}
        )
        self.assertEqual(
            result.value_override,
            "Email [EMAIL_REDACTED] or call [PHONE_REDACTED].",
        )

    def test_json_repair_and_invalid_input(self):
        validator = step4.JSONFormatter()
        repaired = validator.validate("```json\n{'name': 'Alice',}\n```", {})
        self.assertEqual(repaired.value_override, '{\n  "name": "Alice"\n}')
        invalid = validator.validate("not JSON {]", {})
        self.assertEqual(invalid.outcome.value, "fail")


if __name__ == "__main__":
    unittest.main()

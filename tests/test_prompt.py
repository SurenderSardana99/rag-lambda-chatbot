import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rag.prompt import build_prompt  # noqa: E402


def test_build_prompt_includes_question():
    chunks = [{"text": "Refunds are processed within 14 days.", "source": "policy.txt"}]
    prompt = build_prompt("What is the refund window?", chunks)
    assert "What is the refund window?" in prompt


def test_build_prompt_includes_all_sources():
    chunks = [
        {"text": "Chunk A", "source": "doc_a.txt"},
        {"text": "Chunk B", "source": "doc_b.txt"},
    ]
    prompt = build_prompt("question", chunks)
    assert "doc_a.txt" in prompt
    assert "doc_b.txt" in prompt


def test_build_prompt_instructs_grounding():
    prompt = build_prompt("q", [{"text": "t", "source": "s"}])
    assert "ONLY the context" in prompt

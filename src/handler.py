"""
RAG Chatbot - AWS Lambda Handler
---------------------------------
Author: Surender Sardana

Entry point for a Retrieval-Augmented Generation chatbot deployed on AWS Lambda.

Flow:
  1. API Gateway invokes this Lambda with a user question.
  2. We embed the question and retrieve relevant chunks from a vector store.
  3. We build a grounded prompt (context + question) and call the LLM.
  4. We return the answer plus the source chunks used (for traceability /
     hallucination mitigation).
"""

import json
import logging
import os

from rag.retriever import Retriever
from rag.llm_client import LLMClient
from rag.prompt import build_prompt

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# Cold-start init: reused across warm invocations
retriever = Retriever(
    index_path=os.environ.get("VECTOR_INDEX_PATH", "index/faiss_index"),
    top_k=int(os.environ.get("TOP_K", "4")),
)
llm_client = LLMClient(
    model=os.environ.get("LLM_MODEL", "claude-sonnet-4-6"),
    temperature=float(os.environ.get("LLM_TEMPERATURE", "0.2")),
    max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "800")),
)


def lambda_handler(event, context):
    """
    Expected event body (API Gateway proxy integration):
        { "question": "What is our refund policy?" }
    """
    try:
        body = json.loads(event.get("body") or "{}")
        question = (body.get("question") or "").strip()

        if not question:
            return _response(400, {"error": "Field 'question' is required."})

        logger.info("Received question: %s", question)

        # 1. Retrieve relevant context
        retrieved_chunks = retriever.retrieve(question)

        if not retrieved_chunks:
            return _response(
                200,
                {
                    "answer": "I couldn't find anything relevant to answer that.",
                    "sources": [],
                },
            )

        # 2. Build a grounded prompt
        prompt = build_prompt(question=question, chunks=retrieved_chunks)

        # 3. Call the LLM
        answer = llm_client.generate(prompt)

        # 4. Return answer + sources (helps catch/verify hallucinations)
        return _response(
            200,
            {
                "answer": answer,
                "sources": [c["source"] for c in retrieved_chunks],
            },
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled error processing request")
        return _response(500, {"error": "Internal server error", "detail": str(exc)})


def _response(status_code: int, payload: dict):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }

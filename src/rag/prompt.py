"""
Prompt construction for the RAG chatbot.

Design notes:
  - Explicitly instructs the model to answer ONLY from provided context,
    and to say so if the answer isn't in it — this is the main lever for
    reducing hallucination in a RAG system.
  - Keeps context chunks clearly delimited and numbered so the model (and a
    human reviewer) can trace which chunk supports which claim.
"""

from typing import List, Dict

SYSTEM_INSTRUCTIONS = """You are a helpful assistant that answers questions \
using ONLY the context provided below. If the context does not contain \
enough information to answer confidently, say so explicitly rather than \
guessing. Keep answers concise and cite which source number you used."""


def build_prompt(question: str, chunks: List[Dict]) -> str:
    context_blocks = "\n\n".join(
        f"[Source {i+1}: {c['source']}]\n{c['text']}" for i, c in enumerate(chunks)
    )

    return f"""{SYSTEM_INSTRUCTIONS}

Context:
{context_blocks}

Question: {question}

Answer:"""

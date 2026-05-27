"""
DAY 4 — SCRIPT 1: rag_agent.py
================================
What this does:
  Wraps your Day 2 Pinecone RAG into a proper Agent class.
  Takes a question + company → searches annual report → returns cited answer.

This is Agent 3 of your 4 agents.

HOW TO RUN:
  python rag_agent.py

MAKE SURE:
  - You ran ingest.py on Day 2 (vectors must be in Pinecone)
"""

import os
from dotenv import load_dotenv
from fastembed import TextEmbedding

from pinecone import Pinecone
from groq import Groq

load_dotenv()

embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
pc          = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index       = pc.Index("alpharesearch")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL       = "llama-3.3-70b-versatile"


def retrieve_from_annual_report(question: str, company: str, top_k: int = 4) -> list[dict]:
    """Search Pinecone for chunks relevant to the question."""
    query_vec = list(embedder.embed([question]))[0].tolist()

    results = index.query(
        vector=query_vec,
        top_k=top_k,
        filter={"company": company.lower()},
        include_metadata=True
    )

    return [
        {
            "score": round(m["score"], 3),
            "text":  m["metadata"]["text"],
            "chunk": m["metadata"].get("chunk_index", 0)
        }
        for m in results["matches"]
    ]


def generate_rag_answer(question: str, company: str, chunks: list[dict]) -> dict:
    """Pass retrieved chunks to LLM → get cited answer."""
    if not chunks:
        return {
            "answer":  "No relevant information found in the annual report.",
            "sources": [],
            "confidence": "low"
        }

    context = "\n\n---\n\n".join([c["text"] for c in chunks])

    prompt = f"""You are a senior financial analyst reading {company}'s annual report.
Answer the question using ONLY the context below.
Be specific — reference exact numbers and facts from the context.
If the context doesn't contain enough info, say so.

CONTEXT FROM {company.upper()} ANNUAL REPORT:
{context}

QUESTION: {question}

ANSWER (be specific and cite figures):"""

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0
    )

    answer = response.choices[0].message.content

    # Confidence based on retrieval scores
    avg_score = sum(c["score"] for c in chunks) / len(chunks)
    confidence = "high" if avg_score > 0.7 else "medium" if avg_score > 0.5 else "low"

    return {
        "answer":     answer,
        "sources":    chunks,
        "confidence": confidence,
        "avg_score":  round(avg_score, 3)
    }


def run_rag_agent(question: str, company: str) -> dict:
    """
    Full RAG agent pipeline.
    This is the function the LangGraph orchestrator calls on Day 7.
    """
    print(f"\n📚 RAG Agent running for: {company}")
    print(f"   Question: {question}")

    chunks = retrieve_from_annual_report(question, company)
    result = generate_rag_answer(question, company, chunks)
    result["company"]  = company
    result["question"] = question
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("AlphaResearch — Day 4: RAG Agent")
    print("=" * 60)

    test_cases = [
        ("What are the key risks Infosys faces?",        "infosys"),
        ("What is Infosys revenue and profit for FY2024?", "infosys"),
        ("What is Infosys AI strategy?",                  "infosys"),
    ]

    for question, company in test_cases:
        result = run_rag_agent(question, company)

        print(f"\n{'─' * 60}")
        print(f"❓ {result['question']}")
        print(f"📊 Confidence: {result['confidence']} (avg score: {result['avg_score']})")
        print(f"\n💬 Answer:\n{result['answer']}")
        print(f"\n📎 Sources used: {len(result['sources'])} chunks from annual report")
"""
    print("\n✅ RAG Agent working!")
    print("➡️  Now run: python risk_agent.py")
    """
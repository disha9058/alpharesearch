"""
DAY 2 — SCRIPT 2: query.py
============================
What this does:
  1. Takes a user question
  2. Embeds it (converts to vector)
  3. Searches Pinecone for the most relevant chunks
  4. Passes those chunks to Groq LLM
  5. Returns a grounded, cited answer

This is your REAL RAG pipeline — production grade.
The difference from yesterday: vectors live in Pinecone (cloud),
not in memory. This works even after you restart your laptop.

HOW TO RUN:
  python query.py

MAKE SURE:
  - You ran ingest.py first (vectors must be in Pinecone)
"""

import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from groq import Groq

load_dotenv()

# ── Setup ──────────────────────────────────────────────────────
embedder   = SentenceTransformer("all-MiniLM-L6-v2")
pc         = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index      = pc.Index("alpharesearch")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL      = "llama-3.3-70b-versatile"


# ── Retrieval ─────────────────────────────────────────────────

def retrieve(question: str, company: str = "infosys", top_k: int = 4) -> list[dict]:
    """
    Convert question to vector → search Pinecone → return top chunks.

    We filter by company so that when we later add TCS, Reliance etc.,
    a question about Infosys only retrieves Infosys chunks.
    """
    query_vector = embedder.encode(question).tolist()

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        filter={"company": company},   # only get this company's chunks
        include_metadata=True           # include the original text
    )

    return [
        {
            "score": round(match["score"], 3),
            "text":  match["metadata"]["text"],
            "chunk": match["metadata"]["chunk_index"]
        }
        for match in results["matches"]
    ]


# ── Generation ────────────────────────────────────────────────

def generate_answer(question: str, chunks: list[dict]) -> str:
    """
    Pass retrieved chunks to Groq → get a grounded answer.
    The LLM reads the context and answers from it only.
    temperature=0 = no creativity, just reading.
    """
    context = "\n\n---\n\n".join([c["text"] for c in chunks])

    prompt = f"""You are a senior financial analyst reviewing company documents.
Answer the question using ONLY the context provided below.
If the context doesn't contain enough information, say so honestly.
Be specific and reference numbers/facts from the context when available.

CONTEXT FROM ANNUAL REPORT:
{context}

QUESTION: {question}

ANSWER:"""

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0
    )
    return response.choices[0].message.content


# ── Full RAG pipeline ─────────────────────────────────────────

def ask(question: str, company: str = "infosys") -> dict:
    """
    One function that does the complete RAG:
    question → retrieve → generate → return answer + sources
    """
    chunks = retrieve(question, company=company)
    answer = generate_answer(question, chunks)

    return {
        "question": question,
        "answer":   answer,
        "sources":  chunks
    }


# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("AlphaResearch — Day 2, Script 2: Real RAG with Pinecone")
    print("=" * 60)

    questions = [
        "What are the key risks Infosys faces in FY2025?",
        "How did Infosys perform financially this year?",
        "What is Infosys's AI strategy?",
        "What is Infosys's revenue guidance for FY2026?",
        "How many employees does Infosys have and what happened to headcount?",
    ]

    for question in questions:
        print("\n" + "─" * 60)
        print(f" Ques. {question}")

        result = ask(question)

        print(f"\n📎 Retrieved {len(result['sources'])} chunks from Pinecone:")
        for src in result["sources"]:
            print(f"   [{src['score']}] chunk #{src['chunk']}: {src['text'][:70]}...")

        print(f"\n  Answer:\n{result['answer']}")

    print("\n" + "=" * 60)
    print("✅ Day 2 complete! Real RAG with Pinecone is working.")
    print("=" * 60)
    #print("""
#What changed from Day 1:
 # Yesterday: fake text → in-memory storage → lost on restart
 # Today:     real PDF  → Pinecone cloud    → persists forever

#Tomorrow — Day 3:
 # → Build the yfinance agent (live stock data)
 # → Build the NewsAPI agent (live news + sentiment)
 # → Two of your four agents will be done
#""")
#"""
 
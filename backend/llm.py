"""
DAY 1 — SCRIPT 1: Your First LLM Call (using Groq — free)
==========================================================
Groq is free, fast, and uses the same code style as OpenAI.
We switched from OpenAI to Groq — only 3 lines changed.
Everything else in this project stays the same.

HOW TO RUN:
  python llm.py
"""

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Groq client — same idea as OpenAI client, just different provider
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Model we use: llama-3.3-70b — free, fast, very capable
MODEL = "llama-3.3-70b-versatile"


def ask_llm(question: str) -> str:
    """
    Send a question to the LLM and return the response.
    This function is the same as before — only the client changed.
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a financial research assistant. Be concise and factual."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        max_tokens=300
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    print("=" * 50)
    print("AlphaResearch — Day 1, Script 1: First LLM Call")
    print("=" * 50)

    question = "What are the 3 most important financial ratios an investor should check before buying a stock? Keep it brief."

    print(f"\nSending question to Groq (free tier)...\n")
    answer = ask_llm(question)

    print(f"Answer:\n{answer}")
    #print("\n✅ Script 1 done. Groq is working.")
  #  print("➡️  Now run: python embedding.py")
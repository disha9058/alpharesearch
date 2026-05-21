"""
DAY 3 — SCRIPT 1: sentiment_agent.py
======================================
What this does:
  1. Fetches real live news articles about any company
  2. Passes them to Groq LLM to read and analyze
  3. Returns a structured sentiment score + key themes + notable events

This is Agent 1 of your 4 agents.

HOW TO RUN:
  python sentiment_agent.py

INSTALLS NEEDED:
  pip install requests
"""

import os
import json
import requests
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
MODEL = "llama-3.1-8b-instant"


# ── Step 1: Fetch news articles ───────────────────────────────

def fetch_news(company: str, days_back: int = 30) -> list[dict]:
    """
    Fetch recent news articles about a company using NewsAPI.
    Returns a list of article dicts with title, description, url, publishedAt.
    """
    print(f"  📰 Fetching news for '{company}'...")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q":        company,
        "language": "en",
        "sortBy":   "publishedAt",
        "pageSize": 15,            # fetch 15 articles
        "apiKey":   NEWS_API_KEY,
    }

    response = requests.get(url, params=params)
    data     = response.json()

    if data.get("status") != "ok":
        print(f"  ❌ NewsAPI error: {data.get('message')}")
        return []

    articles = data.get("articles", [])
    print(f"  ✅ Fetched {len(articles)} articles")
    return articles


# ── Step 2: Analyze sentiment with LLM ───────────────────────

def analyze_sentiment(company: str, articles: list[dict]) -> dict:
    """
    Pass article headlines and descriptions to Groq.
    LLM reads them and returns structured sentiment analysis.
    We ask for JSON output so we can use the data programmatically.
    """
    if not articles:
        return {
            "score":       0.0,
            "label":       "neutral",
            "themes":      [],
            "events":      [],
            "summary":     "No recent news found.",
            "article_count": 0
        }

    # Build a readable list of articles for the LLM
    article_text = ""
    for i, article in enumerate(articles[:10], 1):   # use top 10
        title = article.get("title", "")
        desc  = article.get("description", "")
        date  = article.get("publishedAt", "")[:10]  # just the date
        if title:
            article_text += f"{i}. [{date}] {title}\n"
            if desc:
                article_text += f"   {desc}\n"

    prompt = f"""You are a financial sentiment analyst. Analyze the following news articles about {company}.

NEWS ARTICLES:
{article_text}

Return a JSON object with EXACTLY this structure (no other text, just JSON):
{{
  "score": <float between -1.0 (very negative) and 1.0 (very positive)>,
  "label": <"positive" or "negative" or "neutral">,
  "themes": [<list of 3 key themes in the news, each max 5 words>],
  "events": [<list of 2-3 notable specific events mentioned>],
  "summary": <2-3 sentence summary of overall market sentiment>
}}"""

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0
    )

    raw = response.choices[0].message.content.strip()

    # Parse JSON safely
    try:
        # Sometimes LLM wraps in ```json ... ``` — strip that
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "score":   0.0,
            "label":   "neutral",
            "themes":  [],
            "events":  [],
            "summary": raw[:200]
        }

    result["article_count"] = len(articles)
    return result


# ── Main agent function ───────────────────────────────────────

def run_sentiment_agent(company: str) -> dict:
    """
    Full sentiment agent pipeline:
    company name → fetch news → analyze → return structured result

    This is the function the LangGraph orchestrator will call on Day 7.
    """
    print(f"\n🔍 Sentiment Agent running for: {company}")
    articles = fetch_news(company)
    result   = analyze_sentiment(company, articles)
    result["company"] = company
    return result


# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("AlphaResearch — Day 3: Sentiment Agent")
    print("=" * 60)

    # Test with multiple companies
    companies = ["Infosys", "Tata Motors", "Zomato"]

    for company in companies:
        result = run_sentiment_agent(company)

        print(f"\n{'─' * 60}")
        print(f"📊 Results for {result['company']}")
        print(f"{'─' * 60}")
        print(f"  Sentiment Score : {result['score']:+.2f}  ({result['label'].upper()})")
        print(f"  Articles Read   : {result['article_count']}")
        print(f"  Key Themes      : {', '.join(result['themes'])}")
        print(f"\n  Notable Events:")
        for event in result.get('events', []):
            print(f"    • {event}")
        print(f"\n  Summary: {result['summary']}")

    print("\n" + "=" * 60)
    #print("✅ Sentiment Agent working!")
    #print("➡️  Now run: python quant_agent.py")
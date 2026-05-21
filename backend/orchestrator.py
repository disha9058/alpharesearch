"""
DAY 5 — orchestrator.py
========================
This is the brain of AlphaResearch.

LangGraph lets us define a pipeline as a graph:
  - Nodes  = each agent (sentiment, quant, rag, risk, synthesis)
  - State  = shared data that flows between agents
  - Edges  = who runs after whom

Flow:
  User question
      ↓
  [Sentiment Agent] ──┐
  [Quant Agent]    ──┤→ [Risk Agent] → [Synthesis Agent] → Final Brief
  [RAG Agent]      ──┘

Sentiment, Quant, and RAG run first (they're independent).
Risk Agent runs after Quant (needs the numbers).
Synthesis runs last (needs everything).

HOW TO RUN:
  pip install langgraph
  python orchestrator.py
"""

import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from groq import Groq

# LangGraph imports
from langgraph.graph import StateGraph, END

# Your 4 agents
from sentiment_agent import run_sentiment_agent
from quant_agent     import run_quant_agent
from rag_agent       import run_rag_agent
from risk_agent      import run_risk_agent

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL       = "llama-3.1-8b-instant"


# ─────────────────────────────────────────────────────────────
# STEP 1: Define the State
#
# State is the shared "whiteboard" that all agents read from
# and write to. Every agent adds its results here.
# LangGraph passes this state from node to node automatically.
# ─────────────────────────────────────────────────────────────

class ResearchState(TypedDict):
    # Input
    question:   str
    company:    str

    # Agent outputs (filled in as agents run)
    sentiment:  dict     # from sentiment_agent
    quant:      dict     # from quant_agent
    rag:        dict     # from rag_agent
    risk:       dict     # from risk_agent

    # Final output
    brief:      str      # synthesized research brief


# ─────────────────────────────────────────────────────────────
# STEP 2: Define the Nodes (one per agent)
#
# Each node is a function that receives the state,
# does its job, and returns ONLY the keys it changed.
# LangGraph merges those changes back into the state.
# ─────────────────────────────────────────────────────────────

def sentiment_node(state: ResearchState) -> dict:
    """Node 1: Run sentiment agent, store result in state."""
    print("\n[1/5] Sentiment Agent running...")
    result = run_sentiment_agent(state["company"])
    print(f"      Score: {result['score']:+.2f} ({result['label']})")
    return {"sentiment": result}

def quant_node(state: ResearchState) -> dict:
    import time
    time.sleep(3)
    print("\n[2/5] 📈 Quant Agent running...")
    result = run_quant_agent(state["company"])
    print(f"      Price: {result.get('currency')} {result.get('current_price')}")
    print(f"      P/E: {result.get('pe_ratio')} | Growth: {result.get('revenue_growth')}%")
    return {"quant": result}

def rag_node(state: ResearchState) -> dict:
    import time
    time.sleep(3)
    print("\n[3/5] 📚 RAG Agent running...")
    result = run_rag_agent(state["question"], state["company"])
    print(f"      Confidence: {result['confidence']} | Sources: {len(result['sources'])} chunks")
    return {"rag": result}


def risk_node(state: ResearchState) -> dict:
    """
    Node 4: Run risk agent.
    Runs AFTER quant and sentiment — needs their data.
    """
    print("\n[4/5]  Risk Agent running...")
    sentiment_score = state["sentiment"].get("score", 0.0)
    result = run_risk_agent(state["quant"], sentiment_score)
    print(f"      Risk level: {result['overall_risk']} | Flags: {result['flag_count']}")
    return {"risk": result}


def synthesis_node(state: ResearchState) -> dict:
    """Node 5: Synthesis Agent — the final step."""
    print("\n[5/5] 🧠 Synthesis Agent writing research brief...")
    
    # DELETE these two lines:
    # import time
    # time.sleep(10)
    
    s = state["sentiment"]  # keep everything from here# wait 10 seconds to reset Groq token window
    
    s = state["sentiment"]
    q = state["quant"]
    # ... rest stays exactly the same
    r = state["rag"]
    k = state["risk"]

    # Build a rich context from all agents for the LLM to synthesize
    prompt = f"""You are a senior equity research analyst at a top investment bank.
Write a structured research brief for {state['company']} based on the data below.

USER QUESTION: {state['question']}

─── SENTIMENT ANALYSIS ───
Score: {s.get('score', 'N/A')} ({s.get('label', 'N/A')})
Articles analyzed: {s.get('article_count', 0)}
Key themes: {', '.join(s.get('themes', []))}
Notable events: {', '.join(s.get('events', []))}
News summary: {s.get('summary', 'N/A')}

─── FINANCIAL METRICS (LIVE) ───
Current Price: {q.get('currency')} {q.get('current_price')}
1-Year Return: {q.get('price_change_1y')}%
P/E Ratio: {q.get('pe_ratio')} | Forward P/E: {q.get('forward_pe')}
Revenue Growth (YoY): {q.get('revenue_growth')}%
Operating Margin: {q.get('operating_margin')}%
Debt/Equity: {q.get('debt_to_equity')}
Analyst Rating: {q.get('analyst_rating', 'N/A').upper()}
Quant insights: {'; '.join(q.get('insights', []))}

─── FROM ANNUAL REPORT (RAG) ───
{r.get('answer', 'No data retrieved')}
Retrieval confidence: {r.get('confidence', 'N/A')}

─── RISK ASSESSMENT ───
Overall Risk Level: {k.get('overall_risk')}
Risk flags: {k.get('flag_count')} issues found
{chr(10).join(['• ' + f['flag'] for f in k.get('flags', [])])}
Risk summary: {k.get('summary')}

─── INSTRUCTIONS ───
Write the research brief in this EXACT format:

ALPHARESEARCH BRIEF: {state['company'].upper()}
{'=' * 50}

BOTTOM LINE
[1-2 sentences directly answering the user's question]

SENTIMENT [{s.get('label', '').upper()}]
[2-3 sentences on market mood and news themes]

FINANCIALS
[3-4 bullet points on key financial metrics with actual numbers]

DOCUMENT INSIGHTS
[2-3 sentences from the annual report, cite specific figures]

RISK ASSESSMENT [{k.get('overall_risk')}]
[List the risk flags, then 1-2 sentences on overall risk]

ANALYST VIEW
[Your 2-3 sentence professional opinion based on all the data]

Sources: Live market data (yfinance) · NewsAPI · Annual Report (RAG)"""

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.1    # slight creativity for natural writing
    )

    brief = response.choices[0].message.content
    return {"brief": brief}


# ─────────────────────────────────────────────────────────────
# STEP 3: Build the Graph
#
# This is where you define WHO runs WHEN.
# ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Assemble the LangGraph pipeline.

    Graph structure:
      START → sentiment_node ──┐
      START → quant_node    ──┤
      START → rag_node      ──┘→ risk_node → synthesis_node → END
    """
    graph = StateGraph(ResearchState)

    # Add all 5 nodes
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("quant",     quant_node)
    graph.add_node("rag",       rag_node)
    graph.add_node("risk",      risk_node)
    graph.add_node("synthesis", synthesis_node)

    # Define edges — who runs after whom
    # Sentiment, quant, and RAG all run from START (independent)
    graph.set_entry_point("sentiment")   # first node to run

    # After sentiment → quant → rag → risk (sequential for simplicity)
    # On Day 8 we can parallelize these; sequential works fine now
    graph.add_edge("sentiment", "quant")
    graph.add_edge("quant",     "rag")
    graph.add_edge("rag",       "risk")
    graph.add_edge("risk",      "synthesis")
    graph.add_edge("synthesis", END)

    return graph.compile()


# ─────────────────────────────────────────────────────────────
# STEP 4: The main run function
# This is what the FastAPI backend will call on Day 8
# ─────────────────────────────────────────────────────────────

def run_research(question: str, company: str) -> dict:
    """
    Run the full AlphaResearch pipeline.
    Input:  user's question + company name
    Output: complete research brief + all agent data
    """
    print(f"\n{'═' * 60}")
    print(f"  AlphaResearch Pipeline Starting")
    print(f"  Company  : {company}")
    print(f"  Question : {question}")
    print(f"{'═' * 60}")

    # Initial state — only question and company are set
    # All agent outputs start empty
    initial_state: ResearchState = {
        "question":  question,
        "company":   company,
        "sentiment": {},
        "quant":     {},
        "rag":       {},
        "risk":      {},
        "brief":     "",
    }

    # Build and run the graph
    app = build_graph()
    final_state = app.invoke(initial_state)

    return final_state


# ─────────────────────────────────────────────────────────────
# MAIN — Test the full pipeline
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("AlphaResearch — Day 5: Full LangGraph Pipeline")
    print("=" * 60)

    # Test question
    question = "Is Infosys a good investment right now?"
    company  = "Infosys"

    result = run_research(question, company)

    # Print the final research brief
    print(f"\n\n{'═' * 60}")
    print("FINAL RESEARCH BRIEF")
    print(f"{'═' * 60}")
    print(result["brief"])
    print(f"\n{'═' * 60}")
    print(" Full pipeline complete!")
    print(f"{'═' * 60}")
    #print("""
#What just happened (the full flow):
 # 1. Your question entered the LangGraph state
  #2. Sentiment Agent fetched 15 live news articles → scored them
  #3. Quant Agent pulled live stock price, P/E, margins from Yahoo
  #4. RAG Agent searched the Infosys annual report in Pinecone
  #5. Risk Agent flagged anomalies in the financial data
  #6. Synthesis Agent combined everything → research brief

#This is AlphaResearch working end-to-end.

#Next — Day 6:
 # → Wrap this in a FastAPI backend (POST /research endpoint)
 # → Frontend can now trigger the full pipeline via HTTP
#""")

"""
DAY 4 — SCRIPT 2: risk_agent.py
=================================
What this does:
  Takes the quant data from quant_agent.py and flags anything unusual.
  Uses simple statistical thresholds — no ML needed.
  Returns a list of risk flags with severity levels.

This is Agent 4 of your 4 agents. After this, all 4 agents are done.

HOW TO RUN:
  python risk_agent.py
"""

from dotenv import load_dotenv
from groq import Groq
import json

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY") if False else __import__('os').environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

import os
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── Risk thresholds ───────────────────────────────────────────
# These are the boundaries we use to flag anomalies.
# Based on general financial analysis guidelines.

THRESHOLDS = {
    "pe_ratio": {
        "very_high": 50,    # above 50 = extremely overvalued signal
        "high":      35,    # above 35 = elevated valuation
        "low":       8,     # below 8  = potentially distressed
    },
    "debt_to_equity": {
        "very_high": 200,   # above 200 = high leverage risk
        "high":      100,   # above 100 = elevated debt
        "moderate":  50,
    },
    "revenue_growth": {
        "negative":  0,     # below 0 = shrinking revenue
        "weak":      3,     # below 3% = very slow growth
    },
    "operating_margin": {
        "low":       5,     # below 5% = thin margins
        "very_low":  0,     # below 0  = operating at a loss
    },
    "price_change_1y": {
        "big_drop":  -30,   # fell more than 30% in a year
        "moderate_drop": -15,
    }
}


def check_statistical_risks(quant_data: dict) -> list[dict]:
    """
    Compare financial metrics against thresholds.
    Returns a list of flagged risks with severity and explanation.
    """
    flags = []

    pe = quant_data.get("pe_ratio")
    if pe is not None:
        if pe > THRESHOLDS["pe_ratio"]["very_high"]:
            flags.append({
                "metric":   "P/E Ratio",
                "value":    pe,
                "severity": "high",
                "flag":     f"P/E of {pe} is extremely elevated (>50). Stock may be significantly overvalued."
            })
        elif pe > THRESHOLDS["pe_ratio"]["high"]:
            flags.append({
                "metric":   "P/E Ratio",
                "value":    pe,
                "severity": "medium",
                "flag":     f"P/E of {pe} is elevated (>35). High growth expectations already priced in."
            })
        elif pe < THRESHOLDS["pe_ratio"]["low"]:
            flags.append({
                "metric":   "P/E Ratio",
                "value":    pe,
                "severity": "medium",
                "flag":     f"P/E of {pe} is very low (<8). Could signal distress or deep undervaluation."
            })

    de = quant_data.get("debt_to_equity")
    if de is not None:
        if de > THRESHOLDS["debt_to_equity"]["very_high"]:
            flags.append({
                "metric":   "Debt/Equity",
                "value":    de,
                "severity": "high",
                "flag":     f"Debt/Equity of {de} is very high (>200). Significant leverage risk."
            })
        elif de > THRESHOLDS["debt_to_equity"]["high"]:
            flags.append({
                "metric":   "Debt/Equity",
                "value":    de,
                "severity": "medium",
                "flag":     f"Debt/Equity of {de} is elevated (>100). Monitor debt servicing capacity."
            })

    rev_growth = quant_data.get("revenue_growth")
    if rev_growth is not None:
        if rev_growth < THRESHOLDS["revenue_growth"]["negative"]:
            flags.append({
                "metric":   "Revenue Growth",
                "value":    rev_growth,
                "severity": "high",
                "flag":     f"Revenue is DECLINING ({rev_growth}% YoY). Serious business health concern."
            })
        elif rev_growth < THRESHOLDS["revenue_growth"]["weak"]:
            flags.append({
                "metric":   "Revenue Growth",
                "value":    rev_growth,
                "severity": "low",
                "flag":     f"Revenue growth of {rev_growth}% is very slow. Business may be stagnating."
            })

    margin = quant_data.get("operating_margin")
    if margin is not None:
        if margin < THRESHOLDS["operating_margin"]["very_low"]:
            flags.append({
                "metric":   "Operating Margin",
                "value":    margin,
                "severity": "high",
                "flag":     f"Operating margin is NEGATIVE ({margin}%). Company is losing money on operations."
            })
        elif margin < THRESHOLDS["operating_margin"]["low"]:
            flags.append({
                "metric":   "Operating Margin",
                "value":    margin,
                "severity": "medium",
                "flag":     f"Operating margin of {margin}% is thin (<5%). Limited buffer against cost increases."
            })

    price_change = quant_data.get("price_change_1y")
    if price_change is not None:
        if price_change < THRESHOLDS["price_change_1y"]["big_drop"]:
            flags.append({
                "metric":   "1Y Price Change",
                "value":    price_change,
                "severity": "high",
                "flag":     f"Stock fell {abs(price_change)}% in past year. Significant market concern."
            })
        elif price_change < THRESHOLDS["price_change_1y"]["moderate_drop"]:
            flags.append({
                "metric":   "1Y Price Change",
                "value":    price_change,
                "severity": "medium",
                "flag":     f"Stock down {abs(price_change)}% in past year. Underperforming market."
            })

    return flags


def generate_risk_summary(company: str, flags: list[dict], sentiment_score: float = 0.0) -> str:
    """
    Use Groq to write a plain-English risk summary combining
    statistical flags with sentiment signal.
    """
    if not flags:
        return f"No significant risk flags detected for {company} based on current financial metrics."

    flags_text = "\n".join([
        f"- [{f['severity'].upper()}] {f['flag']}"
        for f in flags
    ])

    prompt = f"""You are a risk analyst. Based on these risk flags for {company}, write a 2-3 sentence plain English risk assessment.
Be direct. Don't soften the language if risks are real.

RISK FLAGS:
{flags_text}

CURRENT NEWS SENTIMENT: {'negative' if sentiment_score < -0.2 else 'positive' if sentiment_score > 0.2 else 'neutral'} (score: {sentiment_score})

RISK ASSESSMENT (2-3 sentences):"""

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0
    )
    return response.choices[0].message.content


def run_risk_agent(quant_data: dict, sentiment_score: float = 0.0) -> dict:
    """
    Full risk agent pipeline.
    Takes quant_data from quant_agent + sentiment_score from sentiment_agent.
    This is the function the LangGraph orchestrator calls on Day 7.
    """
    company = quant_data.get("company", "Unknown")
    print(f"\n⚠️  Risk Agent running for: {company}")

    flags   = check_statistical_risks(quant_data)
    summary = generate_risk_summary(company, flags, sentiment_score)

    # Overall risk level based on flag count and severity
    high_flags   = [f for f in flags if f["severity"] == "high"]
    medium_flags = [f for f in flags if f["severity"] == "medium"]

    if len(high_flags) >= 2:
        overall_risk = "HIGH"
    elif len(high_flags) == 1 or len(medium_flags) >= 2:
        overall_risk = "MEDIUM"
    elif flags:
        overall_risk = "LOW"
    else:
        overall_risk = "MINIMAL"

    return {
        "company":      company,
        "overall_risk": overall_risk,
        "flag_count":   len(flags),
        "flags":        flags,
        "summary":      summary
    }


if __name__ == "__main__":
    print("=" * 60)
    print("AlphaResearch — Day 4: Risk Agent")
    print("=" * 60)

    # Import and run quant agent to get real data
    from quant_agent import run_quant_agent
    from sentiment_agent import run_sentiment_agent

    companies = ["Infosys", "Tata Motors"]

    for company in companies:
        print(f"\n{'═' * 60}")
        print(f"Running full pipeline for: {company}")
        print(f"{'═' * 60}")

        quant_data     = run_quant_agent(company)
        sentiment_data = run_sentiment_agent(company)
        risk_result    = run_risk_agent(quant_data, sentiment_data["score"])

        print(f"\n{'─' * 60}")
        print(f"⚠️  Risk Report: {company}")
        print(f"{'─' * 60}")
        print(f"  Overall Risk Level : {risk_result['overall_risk']}")
        print(f"  Total Flags        : {risk_result['flag_count']}")

        if risk_result["flags"]:
            print(f"\n  Flagged Issues:")
            for flag in risk_result["flags"]:
                severity_icon = "🔴" if flag["severity"] == "high" else "🟡" if flag["severity"] == "medium" else "🟢"
                print(f"  {severity_icon} {flag['flag']}")

        print(f"\n  Risk Summary:\n  {risk_result['summary']}")

    print("\n" + "=" * 60)
    print("✅ All 4 agents are done!")
    print("=" * 60)
    #print("""
  #Agent 1 ✅  Sentiment Agent  — live news → sentiment score
 # Agent 2 ✅  Quant Agent      — live stock data → financial metrics
  #Agent 3 ✅  RAG Agent        — annual report → cited answers
  #Agent 4 ✅  Risk Agent       — metrics → anomaly flags

#Tomorrow — Day 5:
#  → Wire all 4 agents with LangGraph
#  → One question in → all agents run → one research brief out
#  → The full AlphaResearch pipeline working end to end
#""")
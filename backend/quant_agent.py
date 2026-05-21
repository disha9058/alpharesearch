"""
DAY 3 — SCRIPT 2: quant_agent.py
==================================
What this does:
  1. Takes a company ticker symbol (e.g. "INFY" for Infosys)
  2. Pulls live stock price, P/E ratio, revenue, margins, debt
  3. Compares metrics against sector averages
  4. Returns structured financial data

This is Agent 2 of your 4 agents.
No API key needed — yfinance scrapes Yahoo Finance for free.

HOW TO RUN:
  python quant_agent.py

INSTALLS NEEDED:
  pip install yfinance
"""

import yfinance as yf
from dotenv import load_dotenv

load_dotenv()


# ── Ticker map: company name → stock ticker ───────────────────
# Users type company names — we look up the right ticker
TICKER_MAP = {

    # Indian IT / Placement Companies
    "infosys":        "INFY",
    "tcs":            "TCS.NS",
    "wipro":          "WIPRO.NS",
    "hcl tech":       "HCLTECH.NS",
    "accenture":      "ACN",

    # Indian Finance
    "hdfc bank":      "HDFCBANK.NS",

    # Indian Other
    "reliance":       "RELIANCE.NS",
    "tata motors":    "TATAMOTORS.NS",
    "zomato":         "ZOMATO.NS",

    # Global Tech
    "microsoft":      "MSFT",
    "apple":          "AAPL",
    "amazon":         "AMZN",
    "tesla":          "TSLA",

    # Global Finance / Consulting
    "wells fargo":    "WFC",
    "msci":           "MSCI",

    # Global Banking
    "ubs":            "UBS",
    "barclays":       "BCS",
    "bny":            "BK",
}

"""
TICKER_MAP = {
    "infosys":      "INFY",
    "tcs":          "TCS.NS",
    "wipro":        "WIPRO.NS",
    "hcl":          "HCLTECH.NS",
    "reliance":     "RELIANCE.NS",
    "hdfc bank":    "HDFCBANK.NS",
    "tata motors":  "TATAMOTORS.BO",
    "zomato":       "ZOMATO.NS",
    "bajaj finance":"BAJFINANCE.NS",
    "apple":        "AAPL",
    "microsoft":    "MSFT",
    "tesla":        "TSLA",
    "amazon":       "AMZN",
    "google":       "GOOGL",
}
"""

def get_ticker(company: str) -> str:
    """Convert company name to ticker symbol — case insensitive."""
    return TICKER_MAP.get(company.lower().strip(), company.upper())


# ── Fetch financial data ──────────────────────────────────────

def fetch_financials(company: str) -> dict:
    """
    Pull live financial metrics from Yahoo Finance via yfinance.

    Key metrics we fetch:
    - currentPrice    : live stock price
    - trailingPE      : Price-to-Earnings ratio (valuation)
    - revenueGrowth   : YoY revenue growth rate
    - operatingMargins: profitability
    - debtToEquity    : financial risk
    - returnOnEquity  : how efficiently they use shareholder money
    - freeCashflow    : cash generated after expenses
    """
    ticker_symbol = get_ticker(company)
    print(f"  📈 Fetching financials for {company} ({ticker_symbol})...")

    ticker = yf.Ticker(ticker_symbol)
    info   = ticker.info

    def safe_get(key, multiplier=1):
        val = info.get(key)
        if val is None:
            return None
        try:
            return round(float(val) * multiplier, 2)
        except (TypeError, ValueError, OverflowError):
            return None

    # Get 1-year price history for trend
    hist = ticker.history(period="1y")
    price_1y_ago = None
    price_change_1y = None

    if not hist.empty:
        price_1y_ago    = round(hist["Close"].iloc[0], 2)
        current_price   = round(hist["Close"].iloc[-1], 2)
        price_change_1y = round(
            ((current_price - price_1y_ago) / price_1y_ago) * 100, 2
        )
    else:
        current_price = safe_get("currentPrice")

    result = {
        "company":          company,
        "ticker":           ticker_symbol,
        "current_price":    current_price,
        "currency":         info.get("currency", "USD"),
        "market_cap":       safe_get("marketCap"),
        "pe_ratio":         safe_get("trailingPE"),
        "forward_pe":       safe_get("forwardPE"),
        "revenue_growth":   safe_get("revenueGrowth", 100),    # as percentage
        "earnings_growth":  safe_get("earningsGrowth", 100),   # as percentage
        "operating_margin": safe_get("operatingMargins", 100), # as percentage
        "profit_margin":    safe_get("profitMargins", 100),    # as percentage
        "debt_to_equity":   safe_get("debtToEquity"),
        "return_on_equity": safe_get("returnOnEquity", 100),   # as percentage
        "free_cashflow":    safe_get("freeCashflow"),
        "price_change_1y":  price_change_1y,
        "52_week_high":     safe_get("fiftyTwoWeekHigh"),
        "52_week_low":      safe_get("fiftyTwoWeekLow"),
        "analyst_rating":   info.get("recommendationKey", "N/A"),
        "sector":           info.get("sector", "N/A"),
        "industry":         info.get("industry", "N/A"),
    }

    print(f"  ✅ Financials fetched successfully")
    return result


# ── Interpret the data ────────────────────────────────────────

def interpret_financials(data: dict) -> list[str]:
    """
    Generate plain English interpretations of the financial metrics.
    These become part of the final research brief.
    """
    insights = []

    # P/E ratio interpretation
    pe = data.get("pe_ratio")
    if pe:
        if pe < 15:
            insights.append(f"P/E ratio of {pe} suggests the stock may be undervalued vs market average (~20-25)")
        elif pe > 35:
            insights.append(f"P/E ratio of {pe} is elevated — market expects high future growth")
        else:
            insights.append(f"P/E ratio of {pe} is within a reasonable range")

    # Revenue growth
    rev_growth = data.get("revenue_growth")
    if rev_growth is not None:
        if rev_growth > 15:
            insights.append(f"Strong revenue growth of {rev_growth}% YoY")
        elif rev_growth > 5:
            insights.append(f"Moderate revenue growth of {rev_growth}% YoY")
        elif rev_growth < 0:
            insights.append(f"⚠️ Revenue declined {abs(rev_growth)}% YoY — watch closely")

    # Debt to equity
    de = data.get("debt_to_equity")
    if de is not None:
        if de > 150:
            insights.append(f"⚠️ High debt-to-equity ratio of {de} — elevated financial risk")
        elif de < 30:
            insights.append(f"Low debt-to-equity of {de} — healthy balance sheet")

    # 1-year price performance
    change = data.get("price_change_1y")
    if change is not None:
        direction = "gained" if change > 0 else "lost"
        insights.append(f"Stock has {direction} {abs(change)}% over the past year")

    return insights


# ── Main agent function ───────────────────────────────────────

def run_quant_agent(company: str) -> dict:
    """
    Full quant agent pipeline:
    company → fetch live data → interpret → return structured result

    This is the function the LangGraph orchestrator will call on Day 7.
    """
    print(f"\n📊 Quant Agent running for: {company}")
    data     = fetch_financials(company)
    insights = interpret_financials(data)
    data["insights"] = insights
    return data


# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("AlphaResearch — Day 3: Quant Agent")
    print("=" * 60)

    companies = ["Infosys", "Tata Motors", "Apple"]

    for company in companies:
        result = run_quant_agent(company)

        print(f"\n{'─' * 60}")
        print(f"📈 {result['company']} ({result['ticker']})")
        print(f"{'─' * 60}")
        print(f"  Sector          : {result['sector']}")
        print(f"  Current Price   : {result['currency']} {result['current_price']}")
        print(f"  1Y Price Change : {result['price_change_1y']}%")
        print(f"  P/E Ratio       : {result['pe_ratio']}")
        print(f"  Revenue Growth  : {result['revenue_growth']}%")
        print(f"  Operating Margin: {result['operating_margin']}%")
        print(f"  Debt/Equity     : {result['debt_to_equity']}")
        print(f"  Analyst Rating  : {result['analyst_rating'].upper()}")
        print(f"\n  Insights:")
        for insight in result["insights"]:
            print(f"    • {insight}")

    print("\n" + "=" * 60)
    print("✅ Quant Agent working! Live data from Yahoo Finance.")
    print("=" * 60)
    #print("\nTomorrow — Day 4:")
    #print("  → Build the RAG Agent (wraps your Pinecone query into an agent)")
    #print("  → Build the Risk Agent (flags anomalies in the quant data)")
    #print("  → Both agents done = all 4 agents ready for Day 5 wiring")
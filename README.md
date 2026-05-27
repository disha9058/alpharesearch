AlphaResearch — Multi-Agent Financial Research System
Video:https://www.loom.com/share/c452e03d9aea4fb3af352b83f4662ff6

Live demo: https://researchalpha.vercel.app/

## What it does
Ask any financial question about 25+ listed companies. 
4 AI agents run in parallel — sentiment analysis from live news, 
quantitative data from Yahoo Finance, document insights from annual 
reports via RAG, and statistical risk flagging — synthesized into 
a professional research brief.

## Tech Stack
Python · LangGraph · FastAPI · Pinecone · Groq · 
Supabase · React · Vite · Render · Vercel

## Architecture
- Sentiment Agent → NewsAPI → Groq LLM
- Quant Agent → yfinance (live market data)  
- RAG Agent → Pinecone vector DB (annual reports)
- Risk Agent → statistical anomaly detection
- Synthesis Agent → LangGraph orchestration → research brief

## Companies supported
Infosys, TCS, Wipro, HCL Tech, Reliance, HDFC Bank, 
ICICI Bank, Tata Motors, Zomato, Wells Fargo, Barclays, 
BNY, UBS, MSCI, Apple, Microsoft, Tesla, Amazon + more

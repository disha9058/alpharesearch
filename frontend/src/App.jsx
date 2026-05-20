// AlphaResearch — Complete React Frontend
// Drop this file into frontend/src/App.jsx
// Replace everything that was there before

import { useState, useEffect, useRef } from "react";

const API_BASE = "https://alpharesearch.onrender.com";

// ── Supported companies (matches backend) ─────────────────────
const COMPANIES = [

  // Indian IT / Placement Companies
  "Infosys",
  "TCS",
  "Wipro",
  "HCL Tech",
  "Accenture",

  // Indian Finance
  "HDFC Bank",

  // Indian Other
  "Reliance",
  "Tata Motors",
  "Zomato",

  // Global Tech
  "Microsoft",
  "Apple",
  "Amazon",
  "Tesla",

  // Global Finance / Consulting
  "Wells Fargo",
  "MSCI",

  // Global Banking
  "UBS",
  "Barclays",
  "BNY",
];

// ── Helper: sentiment color ───────────────────────────────────
function sentimentColor(score) {
  if (score > 0.2)  return "#22c55e";
  if (score < -0.2) return "#ef4444";
  return "#f59e0b";
}

function sentimentLabel(score) {
  if (score > 0.2)  return "POSITIVE";
  if (score < -0.2) return "NEGATIVE";
  return "NEUTRAL";
}

// ── Helper: risk color ────────────────────────────────────────
function riskColor(level) {
  if (level === "HIGH")    return "#ef4444";
  if (level === "MEDIUM")  return "#f59e0b";
  if (level === "LOW")     return "#22c55e";
  return "#6b7280";
}

// ── Metric card component ─────────────────────────────────────
function MetricCard({ label, value, sub }) {
  return (
    <div style={{
      background: "#1a1a2e",
      border: "1px solid #2d2d44",
      borderRadius: 10,
      padding: "14px 16px",
      flex: 1,
      minWidth: 120,
    }}>
      <p style={{ fontSize: 11, color: "#6b7280", margin: "0 0 4px", textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</p>
      <p style={{ fontSize: 18, fontWeight: 600, color: "#f1f5f9", margin: "0 0 2px" }}>{value ?? "N/A"}</p>
      {sub && <p style={{ fontSize: 11, color: "#6b7280", margin: 0 }}>{sub}</p>}
    </div>
  );
}

// ── Agent status indicator ────────────────────────────────────
function AgentStatus({ name, icon, done }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      padding: "8px 12px",
      background: done ? "#0f2027" : "#111118",
      border: `1px solid ${done ? "#22c55e33" : "#2d2d44"}`,
      borderRadius: 8,
      transition: "all 0.4s",
    }}>
      <span style={{ fontSize: 16 }}>{icon}</span>
      <span style={{ fontSize: 12, color: done ? "#22c55e" : "#6b7280" }}>{name}</span>
      {done && <span style={{ fontSize: 10, color: "#22c55e", marginLeft: "auto" }}>✓</span>}
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────
export default function App() {
  const [company,    setCompany]    = useState("");
  const [question,   setQuestion]   = useState("");
  const [status,     setStatus]     = useState("idle"); // idle | loading | done | error
  const [result,     setResult]     = useState(null);
  const [jobId,      setJobId]      = useState(null);
  const [elapsed,    setElapsed]    = useState(0);
  const [history,    setHistory]    = useState([]);
  const [activeTab,  setActiveTab]  = useState("brief");
  const pollRef  = useRef(null);
  const timerRef = useRef(null);

  // Load research history on mount
  useEffect(() => {
    fetch(`${API_BASE}/research`)
      .then(r => r.json())
      .then(d => setHistory(d.jobs || []))
      .catch(() => {});
  }, []);

  // Poll for result
  useEffect(() => {
    if (!jobId) return;
    pollRef.current = setInterval(async () => {
      try {
        const res  = await fetch(`${API_BASE}/research/${jobId}`);
        const data = await res.json();
        if (data.status === "completed") {
          clearInterval(pollRef.current);
          clearInterval(timerRef.current);
          setResult(data);
          setStatus("done");
          setHistory(prev => [data, ...prev.filter(j => j.id !== data.id)]);
        } else if (data.status === "failed") {
          clearInterval(pollRef.current);
          clearInterval(timerRef.current);
          setStatus("error");
        }
      } catch (e) {
        clearInterval(pollRef.current);
        setStatus("error");
      }
    }, 3000);
    return () => clearInterval(pollRef.current);
  }, [jobId]);

  async function handleSubmit() {
    if (!company || !question.trim()) return;
    setStatus("loading");
    setResult(null);
    setElapsed(0);
    setActiveTab("brief");

    // Start elapsed timer
    timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);

    try {
      const res  = await fetch(`${API_BASE}/research`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ company, question }),
      });
      const data = await res.json();
      setJobId(data.id);
    } catch (e) {
      setStatus("error");
      clearInterval(timerRef.current);
    }
  }

  function loadHistoryItem(item) {
    setResult(item);
    setStatus("done");
    setActiveTab("brief");
    setCompany(item.company);
    setQuestion(item.question);
  }

  // ── Render ──────────────────────────────────────────────────
  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0a14",
      color: "#f1f5f9",
      fontFamily: "'Inter', -apple-system, sans-serif",
      display: "flex",
    }}>

      {/* ── Sidebar ── */}
      <div style={{
        width: 240, flexShrink: 0,
        background: "#111118",
        borderRight: "1px solid #1e1e2e",
        padding: "20px 0",
        display: "flex", flexDirection: "column",
      }}>
        {/* Logo */}
        <div style={{ padding: "0 20px 20px", borderBottom: "1px solid #1e1e2e" }}>
          <p style={{ fontSize: 16, fontWeight: 700, margin: 0, color: "#818cf8" }}>α AlphaResearch</p>
          <p style={{ fontSize: 11, color: "#4b5563", margin: "4px 0 0" }}>Multi-agent AI research</p>
        </div>

        {/* History */}
        <div style={{ padding: "16px 20px 8px" }}>
          <p style={{ fontSize: 10, fontWeight: 500, color: "#4b5563", letterSpacing: "0.06em", textTransform: "uppercase", margin: "0 0 10px" }}>Recent Research</p>
          {history.length === 0 && (
            <p style={{ fontSize: 11, color: "#374151", margin: 0 }}>No research yet</p>
          )}
          {history.slice(0, 8).map(item => (
            <div key={item.id}
              onClick={() => loadHistoryItem(item)}
              style={{
                padding: "8px 10px", borderRadius: 7, cursor: "pointer",
                marginBottom: 4,
                background: result?.id === item.id ? "#1a1a2e" : "transparent",
                border: `1px solid ${result?.id === item.id ? "#2d2d44" : "transparent"}`,
              }}>
              <p style={{ fontSize: 12, color: "#9ca3af", margin: "0 0 2px", fontWeight: 500 }}>{item.company}</p>
              <p style={{ fontSize: 10, color: "#4b5563", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {item.question}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Main content ── */}
      <div style={{ flex: 1, padding: "32px 40px", overflowY: "auto", maxWidth: 900 }}>

        {/* Header */}
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 6px", color: "#f1f5f9" }}>
            Financial Research
          </h1>
          <p style={{ fontSize: 14, color: "#6b7280", margin: 0 }}>
            Ask anything about any listed company — powered by 4 AI agents
          </p>
        </div>

        {/* Search box */}
        <div style={{
          background: "#111118",
          border: "1px solid #2d2d44",
          borderRadius: 12,
          padding: 20,
          marginBottom: 24,
        }}>
          {/* Company selector */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 11, color: "#6b7280", display: "block", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Company
            </label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {COMPANIES.map(c => (
                <button key={c} onClick={() => setCompany(c)}
                  style={{
                    padding: "5px 12px", borderRadius: 20, fontSize: 12, cursor: "pointer",
                    background: company === c ? "#818cf8" : "#1a1a2e",
                    color:      company === c ? "#fff"    : "#9ca3af",
                    border:     `1px solid ${company === c ? "#818cf8" : "#2d2d44"}`,
                    transition: "all 0.2s",
                  }}>
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* Question input */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 11, color: "#6b7280", display: "block", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Your Question
            </label>
            <textarea
              value={question}
              onChange={e => setQuestion(e.target.value)}
              placeholder="e.g. Is Infosys a good investment right now? What are the key risks?"
              rows={2}
              style={{
                width: "100%", background: "#0a0a14", border: "1px solid #2d2d44",
                borderRadius: 8, padding: "10px 12px", color: "#f1f5f9",
                fontSize: 13, resize: "none", outline: "none", boxSizing: "border-box",
              }}
            />
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={!company || !question.trim() || status === "loading"}
            style={{
              padding: "10px 24px", background: "#818cf8", color: "#fff",
              border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600,
              cursor: status === "loading" ? "not-allowed" : "pointer",
              opacity: !company || !question.trim() ? 0.5 : 1,
            }}>
            {status === "loading" ? `Researching... ${elapsed}s` : "Run Research"}
          </button>
        </div>

        {/* Loading state — agent progress */}
        {status === "loading" && (
          <div style={{
            background: "#111118", border: "1px solid #2d2d44",
            borderRadius: 12, padding: 20, marginBottom: 24,
          }}>
            <p style={{ fontSize: 13, color: "#9ca3af", margin: "0 0 14px" }}>
              🤖 Agents working on <strong style={{ color: "#818cf8" }}>{company}</strong>...
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <AgentStatus name="Sentiment Agent"  icon="📰" done={elapsed > 8}  />
              <AgentStatus name="Quant Agent"      icon="📈" done={elapsed > 15} />
              <AgentStatus name="RAG Agent"        icon="📚" done={elapsed > 22} />
              <AgentStatus name="Risk Agent"       icon="⚠️"  done={elapsed > 30} />
            </div>
            <p style={{ fontSize: 11, color: "#4b5563", margin: "12px 0 0" }}>
              Fetching live news, stock data, annual report insights, and risk flags...
            </p>
          </div>
        )}

        {/* Error state */}
        {status === "error" && (
          <div style={{
            background: "#1a0a0a", border: "1px solid #ef444444",
            borderRadius: 12, padding: 16, marginBottom: 24,
          }}>
            <p style={{ color: "#ef4444", margin: 0, fontSize: 13 }}>
               ❌ Research failed. The AI agents are rate limited — please wait 60 seconds and try again.
            </p>
          </div>
        )}

        {/* Results */}
        {status === "done" && result && (
          <div>
            {/* Company header */}
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              marginBottom: 16,
            }}>
              <div>
                <h2 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>
                  {result.company}
                </h2>
                <p style={{ fontSize: 12, color: "#6b7280", margin: 0 }}>
                  {result.question}
                </p>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                {result.sentiment && (
                  <span style={{
                    padding: "4px 12px", borderRadius: 20, fontSize: 11, fontWeight: 600,
                    background: sentimentColor(result.sentiment.score) + "22",
                    color: sentimentColor(result.sentiment.score),
                    border: `1px solid ${sentimentColor(result.sentiment.score)}44`,
                  }}>
                    {sentimentLabel(result.sentiment.score)}
                  </span>
                )}
                {result.risk && (
                  <span style={{
                    padding: "4px 12px", borderRadius: 20, fontSize: 11, fontWeight: 600,
                    background: riskColor(result.risk.overall_risk) + "22",
                    color: riskColor(result.risk.overall_risk),
                    border: `1px solid ${riskColor(result.risk.overall_risk)}44`,
                  }}>
                    {result.risk.overall_risk} RISK
                  </span>
                )}
              </div>
            </div>

            {/* Key metrics row */}
            {result.quant && (
              <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
                <MetricCard
                  label="Price"
                  value={`${result.quant.currency} ${result.quant.current_price}`}
                  sub={`${result.quant.price_change_1y > 0 ? "+" : ""}${result.quant.price_change_1y}% (1Y)`}
                />
                <MetricCard
                  label="P/E Ratio"
                  value={result.quant.pe_ratio}
                  sub="Trailing"
                />
                <MetricCard
                  label="Revenue Growth"
                  value={`${result.quant.revenue_growth}%`}
                  sub="Year over year"
                />
                <MetricCard
                  label="Op. Margin"
                  value={`${result.quant.operating_margin}%`}
                  sub="Operating"
                />
                <MetricCard
                  label="Rating"
                  value={result.quant.analyst_rating?.toUpperCase()}
                  sub="Analyst consensus"
                />
              </div>
            )}

            {/* Tabs */}
            <div style={{ display: "flex", gap: 4, marginBottom: 16, borderBottom: "1px solid #1e1e2e", paddingBottom: 0 }}>
              {["brief", "sentiment", "risk", "sources"].map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)}
                  style={{
                    padding: "8px 16px", background: "transparent", border: "none",
                    borderBottom: `2px solid ${activeTab === tab ? "#818cf8" : "transparent"}`,
                    color: activeTab === tab ? "#818cf8" : "#6b7280",
                    fontSize: 13, fontWeight: 500, cursor: "pointer",
                    textTransform: "capitalize",
                  }}>
                  {tab === "brief" ? "Research Brief" : tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div style={{
              background: "#111118", border: "1px solid #2d2d44",
              borderRadius: 12, padding: 24,
            }}>

              {/* Brief tab */}
              {activeTab === "brief" && (
                <pre style={{
                  margin: 0, whiteSpace: "pre-wrap", fontSize: 13,
                  color: "#d1d5db", lineHeight: 1.8, fontFamily: "inherit",
                }}>
                  {result.brief}
                </pre>
              )}

              {/* Sentiment tab */}
              {activeTab === "sentiment" && result.sentiment && (
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
                    <div style={{
                      width: 80, height: 80, borderRadius: "50%",
                      background: sentimentColor(result.sentiment.score) + "22",
                      border: `3px solid ${sentimentColor(result.sentiment.score)}`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      flexDirection: "column",
                    }}>
                      <span style={{ fontSize: 18, fontWeight: 700, color: sentimentColor(result.sentiment.score) }}>
                        {result.sentiment.score > 0 ? "+" : ""}{result.sentiment.score?.toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <p style={{ fontSize: 16, fontWeight: 600, color: sentimentColor(result.sentiment.score), margin: "0 0 4px" }}>
                        {result.sentiment.label?.toUpperCase()}
                      </p>
                      <p style={{ fontSize: 12, color: "#6b7280", margin: 0 }}>
                        Based on {result.sentiment.article_count} news articles
                      </p>
                    </div>
                  </div>
                  {result.sentiment.themes?.length > 0 && (
                    <div style={{ marginBottom: 16 }}>
                      <p style={{ fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", margin: "0 0 8px" }}>Key Themes</p>
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                        {result.sentiment.themes.map((t, i) => (
                          <span key={i} style={{
                            padding: "4px 10px", background: "#1a1a2e",
                            border: "1px solid #2d2d44", borderRadius: 20,
                            fontSize: 12, color: "#9ca3af",
                          }}>{t}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  <p style={{ fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", margin: "0 0 8px" }}>Summary</p>
                  <p style={{ fontSize: 13, color: "#d1d5db", lineHeight: 1.7, margin: 0 }}>{result.sentiment.summary}</p>
                </div>
              )}

              {/* Risk tab */}
              {activeTab === "risk" && result.risk && (
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
                    <span style={{
                      padding: "6px 18px", borderRadius: 20, fontSize: 14, fontWeight: 700,
                      background: riskColor(result.risk.overall_risk) + "22",
                      color: riskColor(result.risk.overall_risk),
                      border: `1px solid ${riskColor(result.risk.overall_risk)}44`,
                    }}>
                      {result.risk.overall_risk} RISK
                    </span>
                    <span style={{ fontSize: 12, color: "#6b7280" }}>
                      {result.risk.flag_count} flag{result.risk.flag_count !== 1 ? "s" : ""} detected
                    </span>
                  </div>
                  {result.risk.flags?.map((flag, i) => (
                    <div key={i} style={{
                      padding: "10px 14px", borderRadius: 8, marginBottom: 8,
                      background: riskColor(flag.severity) + "11",
                      border: `1px solid ${riskColor(flag.severity)}33`,
                    }}>
                      <p style={{ fontSize: 11, color: riskColor(flag.severity), margin: "0 0 3px", fontWeight: 600 }}>
                        {flag.severity.toUpperCase()} — {flag.metric}
                      </p>
                      <p style={{ fontSize: 12, color: "#d1d5db", margin: 0 }}>{flag.flag}</p>
                    </div>
                  ))}
                  {result.risk.flags?.length === 0 && (
                    <p style={{ fontSize: 13, color: "#22c55e" }}>✓ No significant risk flags detected</p>
                  )}
                  <p style={{ fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", margin: "16px 0 6px" }}>Risk Summary</p>
                  <p style={{ fontSize: 13, color: "#d1d5db", lineHeight: 1.7, margin: 0 }}>{result.risk.summary}</p>
                </div>
              )}

              {/* Sources tab */}
              {activeTab === "sources" && (
                <div>
                  <p style={{ fontSize: 13, color: "#9ca3af", margin: "0 0 16px" }}>
                    Every claim in the research brief is sourced from these live data feeds and documents.
                  </p>
                  {[
                    { icon: "📈", name: "Yahoo Finance (yfinance)", desc: "Live stock price, P/E ratio, margins, debt ratios — pulled in real time" },
                    { icon: "📰", name: "NewsAPI",                  desc: `${result.sentiment?.article_count || 0} recent articles analyzed for market sentiment` },
                    { icon: "📚", name: "Annual Report (Pinecone RAG)", desc: `Retrieved from vector database with ${result.rag?.confidence || "medium"} confidence` },
                    { icon: "⚠️",  name: "Statistical Risk Engine",  desc: `${result.risk?.flag_count || 0} anomalies checked against financial thresholds` },
                  ].map((src, i) => (
                    <div key={i} style={{
                      display: "flex", gap: 12, padding: "12px 14px",
                      background: "#0a0a14", borderRadius: 8, marginBottom: 8,
                      border: "1px solid #1e1e2e",
                    }}>
                      <span style={{ fontSize: 20 }}>{src.icon}</span>
                      <div>
                        <p style={{ fontSize: 13, fontWeight: 500, color: "#f1f5f9", margin: "0 0 3px" }}>{src.name}</p>
                        <p style={{ fontSize: 12, color: "#6b7280", margin: 0 }}>{src.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
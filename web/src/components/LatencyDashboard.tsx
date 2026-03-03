import { useCallback, useEffect, useState } from "react";
import { type MetricBucket, type MetricsSummary, clearMetrics, fetchMetrics } from "../api";

const POLL_INTERVAL = 5000;

function getColor(ms: number): string {
  if (ms < 500) return "#16a34a";
  if (ms < 800) return "#ca8a04";
  return "#dc2626";
}

function getLabel(ms: number): string {
  if (ms < 500) return "Excellent";
  if (ms < 800) return "Acceptable";
  if (ms < 1500) return "Slow";
  return "Critical";
}

function fmt(ts: number): string {
  return new Date(ts * 1000).toLocaleTimeString();
}

function ms(v: number | null): string {
  if (v === null) return "—";
  return `${v % 1 === 0 ? v : v.toFixed(1)}ms`;
}

export default function LatencyDashboard() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [error, setError] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setMetrics(await fetchMetrics());
      setError(false);
    } catch {
      setError(true);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [refresh]);

  if (error) {
    return (
      <section style={sectionStyle}>
        <h2>Latency Metrics</h2>
        <p style={errorStyle}>Could not load metrics. Is the API server running?</p>
      </section>
    );
  }

  if (!metrics) {
    return (
      <section style={sectionStyle}>
        <h2>Latency Metrics</h2>
        <p style={hintStyle}>Loading...</p>
      </section>
    );
  }

  if (metrics.count === 0) {
    return (
      <section style={sectionStyle}>
        <h2>Latency Metrics</h2>
        <p style={hintStyle}>
          No data yet. Start a conversation in the playground and latency will appear here automatically.
        </p>
      </section>
    );
  }

  const maxBar = Math.max(...metrics.recent.map((r) => r.end_to_end_ms), 1);

  return (
    <section style={sectionStyle}>
      <div style={headerRowStyle}>
        <h2>Latency Metrics</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={refresh} style={refreshBtnStyle}>Refresh</button>
          <button
            onClick={async () => { await clearMetrics(); refresh(); }}
            style={clearBtnStyle}
          >
            Clear
          </button>
        </div>
      </div>
      <p style={hintStyle}>
        Measures from the moment the user stops speaking. Updates every 5s.
      </p>

      <div style={metricGroupsStyle}>
        <MetricGroup label="TTFT (STT + Turn Detection)" bucket={metrics.ttft} description="User speech end to LLM start" />
        <MetricGroup label="Processing (LLM + TTS)" bucket={metrics.processing} description="LLM start to first audio" />
        <MetricGroup label="End-to-End" bucket={metrics.end_to_end} description="User speech end to agent audio" />
      </div>

      <p style={{ ...hintStyle, marginTop: 4, fontSize: 11 }}>
        {metrics.count} total samples
      </p>

      <h3 style={{ fontSize: 14, marginTop: 20, marginBottom: 10 }}>Recent Responses</h3>
      <div style={chartStyle}>
        {metrics.recent.map((r, i) => {
          const ttftW = r.ttft_ms !== null ? Math.max((r.ttft_ms / maxBar) * 100, 2) : 0;
          const procW = r.processing_ms !== null ? Math.max((r.processing_ms / maxBar) * 100, 2) : 0;
          const fallbackW = (ttftW === 0 && procW === 0) ? Math.max((r.end_to_end_ms / maxBar) * 100, 4) : 0;

          return (
            <div key={i} style={barEntryStyle}>
              <div style={barRowStyle}>
                <span style={barTimeStyle}>{fmt(r.timestamp)}</span>
                <div style={barTrackStyle}>
                  {fallbackW > 0 ? (
                    <div style={{ ...barSegStyle, width: `${fallbackW}%`, background: getColor(r.end_to_end_ms) }} />
                  ) : (
                    <>
                      <div style={{ ...barSegStyle, width: `${ttftW}%`, background: "#3b82f6" }} />
                      <div style={{ ...barSegStyle, width: `${procW}%`, background: "#8b5cf6" }} />
                    </>
                  )}
                </div>
                <span style={{ ...barValueStyle, color: getColor(r.end_to_end_ms) }}>
                  {ms(r.end_to_end_ms)}
                </span>
              </div>
              <div style={barSubLabelStyle}>
                {r.ttft_ms !== null && (
                  <span style={{ color: "#3b82f6" }}>TTFT {ms(r.ttft_ms)}</span>
                )}
                {r.processing_ms !== null && (
                  <span style={{ color: "#8b5cf6" }}>Proc {ms(r.processing_ms)}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div style={legendStyle}>
        <span><span style={{ ...dotStyle, background: "#3b82f6" }} /> TTFT</span>
        <span><span style={{ ...dotStyle, background: "#8b5cf6" }} /> LLM+TTS</span>
        <span style={{ marginLeft: 16 }}><span style={{ ...dotStyle, background: "#16a34a" }} /> &lt; 500ms</span>
        <span><span style={{ ...dotStyle, background: "#ca8a04" }} /> 500-800ms</span>
        <span><span style={{ ...dotStyle, background: "#dc2626" }} /> &gt; 800ms</span>
      </div>
    </section>
  );
}

function MetricGroup({ label, bucket, description }: { label: string; bucket: MetricBucket; description: string }) {
  return (
    <div style={groupStyle}>
      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 2, whiteSpace: "nowrap" }}>{label}</div>
      <div style={{ fontSize: 10, color: "#94a3b8", marginBottom: 6 }}>{description}</div>
      <div style={miniGridStyle}>
        <MiniStat label="Avg" value={bucket.avg} />
        <MiniStat label="Min" value={bucket.min} />
        <MiniStat label="Max" value={bucket.max} />
      </div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: number }) {
  const color = value > 0 ? getColor(value) : "#94a3b8";
  const tag = value > 0 ? getLabel(value) : "—";
  return (
    <div style={{ textAlign: "center", minWidth: 0 }}>
      <div style={{ fontSize: 10, color: "#94a3b8" }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 700, color, whiteSpace: "nowrap" }}>
        {value > 0 ? (value % 1 === 0 ? value : value.toFixed(1)) : "—"}
        {value > 0 && <span style={{ fontSize: 10, fontWeight: 400, marginLeft: 1 }}>ms</span>}
      </div>
      <div style={{ fontSize: 9, color }}>{tag}</div>
    </div>
  );
}

const sectionStyle: React.CSSProperties = {
  background: "#fff",
  borderRadius: 8,
  padding: 24,
  boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
  overflow: "hidden",
};

const headerRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
};

const refreshBtnStyle: React.CSSProperties = {
  padding: "6px 14px",
  fontSize: 12,
  fontWeight: 600,
  background: "#f1f5f9",
  border: "1px solid #e2e8f0",
  borderRadius: 6,
  cursor: "pointer",
};

const clearBtnStyle: React.CSSProperties = {
  padding: "6px 14px",
  fontSize: 12,
  fontWeight: 600,
  background: "#fef2f2",
  border: "1px solid #fecaca",
  borderRadius: 6,
  cursor: "pointer",
  color: "#dc2626",
};

const hintStyle: React.CSSProperties = {
  fontSize: 13,
  color: "#666",
  marginBottom: 16,
};

const errorStyle: React.CSSProperties = {
  fontSize: 13,
  color: "#dc2626",
};

const metricGroupsStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(3, 1fr)",
  gap: 12,
  marginBottom: 8,
};

const groupStyle: React.CSSProperties = {
  background: "#f8fafc",
  borderRadius: 8,
  padding: "12px 12px",
  border: "1px solid #e2e8f0",
  overflow: "hidden",
  minWidth: 0,
};

const miniGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(3, 1fr)",
  gap: 4,
};

const chartStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 6,
};

const barEntryStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 2,
};

const barRowStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
};

const barTimeStyle: React.CSSProperties = {
  fontSize: 11,
  color: "#94a3b8",
  minWidth: 62,
  textAlign: "right",
  fontFamily: "monospace",
  flexShrink: 0,
};

const barTrackStyle: React.CSSProperties = {
  flex: 1,
  height: 18,
  background: "#f1f5f9",
  borderRadius: 4,
  overflow: "hidden",
  display: "flex",
  minWidth: 0,
};

const barSegStyle: React.CSSProperties = {
  height: "100%",
  transition: "width 0.3s ease",
};

const barValueStyle: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  fontFamily: "monospace",
  minWidth: 65,
  textAlign: "right",
  flexShrink: 0,
};

const barSubLabelStyle: React.CSSProperties = {
  display: "flex",
  gap: 12,
  fontSize: 11,
  fontFamily: "monospace",
  paddingLeft: 70,
};

const legendStyle: React.CSSProperties = {
  display: "flex",
  gap: 12,
  marginTop: 14,
  fontSize: 12,
  color: "#64748b",
};

const dotStyle: React.CSSProperties = {
  display: "inline-block",
  width: 8,
  height: 8,
  borderRadius: "50%",
  marginRight: 4,
};

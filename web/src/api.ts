const BASE = "/api";

export interface ToolConfig {
  enabled: boolean;
  description: string;
}

export interface PersonaConfig {
  name: string;
  greeting: string;
  voice: string;
}

export interface AgentConfig {
  system_prompt: string;
  persona: PersonaConfig;
  tools: Record<string, ToolConfig>;
}

export interface LatencyRecord {
  timestamp: number;
  ttft_ms: number | null;
  processing_ms: number | null;
  end_to_end_ms: number;
}

export interface MetricBucket {
  avg: number;
  min: number;
  max: number;
}

export interface MetricsSummary {
  count: number;
  ttft: MetricBucket;
  processing: MetricBucket;
  end_to_end: MetricBucket;
  recent: LatencyRecord[];
}

export async function fetchConfig(): Promise<AgentConfig> {
  const res = await fetch(`${BASE}/config`);
  if (!res.ok) throw new Error("Failed to fetch config");
  return res.json();
}

export async function saveConfig(config: AgentConfig): Promise<void> {
  const res = await fetch(`${BASE}/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error("Failed to save config");
}

export async function fetchMetrics(): Promise<MetricsSummary> {
  const res = await fetch(`${BASE}/metrics`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export async function clearMetrics(): Promise<void> {
  const res = await fetch(`${BASE}/metrics`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to clear metrics");
}

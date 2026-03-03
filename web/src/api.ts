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

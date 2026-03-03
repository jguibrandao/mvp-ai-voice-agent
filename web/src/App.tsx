import { useCallback, useEffect, useState } from "react";
import { type AgentConfig, fetchConfig, saveConfig } from "./api";
import PersonaConfig from "./components/PersonaConfig";
import SystemPromptEditor from "./components/SystemPromptEditor";
import ToolsManager from "./components/ToolsManager";

export default function App() {
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchConfig()
      .then(setConfig)
      .catch(() => setError("Failed to load config. Is the API server running?"));
  }, []);

  const handleSave = useCallback(async () => {
    if (!config) return;
    setSaving(true);
    setStatus(null);
    try {
      await saveConfig(config);
      setStatus("Saved! Changes will apply to the next conversation.");
    } catch {
      setStatus("Failed to save.");
    } finally {
      setSaving(false);
    }
  }, [config]);

  if (error) {
    return (
      <div style={containerStyle}>
        <div style={{ ...statusBarStyle, background: "#fef2f2", color: "#b91c1c" }}>
          {error}
        </div>
      </div>
    );
  }

  if (!config) {
    return <div style={containerStyle}>Loading...</div>;
  }

  return (
    <div style={containerStyle}>
      <header style={headerStyle}>
        <h1 style={{ fontSize: 22 }}>SmileLine Dental — Agent Admin</h1>
        <button onClick={handleSave} disabled={saving} style={saveButtonStyle}>
          {saving ? "Saving..." : "Save Config"}
        </button>
      </header>

      {status && <div style={statusBarStyle}>{status}</div>}

      <div style={gridStyle}>
        <SystemPromptEditor
          value={config.system_prompt}
          onChange={(v) => setConfig({ ...config, system_prompt: v })}
        />
        <PersonaConfig
          persona={config.persona}
          onChange={(p) => setConfig({ ...config, persona: p })}
        />
        <ToolsManager
          tools={config.tools}
          onChange={(t) => setConfig({ ...config, tools: t })}
        />
      </div>
    </div>
  );
}

const containerStyle: React.CSSProperties = {
  maxWidth: 800,
  margin: "0 auto",
  padding: "32px 20px",
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: 24,
};

const saveButtonStyle: React.CSSProperties = {
  padding: "10px 24px",
  fontSize: 14,
  fontWeight: 600,
  background: "#2563eb",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
};

const statusBarStyle: React.CSSProperties = {
  padding: "10px 16px",
  background: "#f0fdf4",
  color: "#166534",
  borderRadius: 6,
  fontSize: 14,
  marginBottom: 16,
};

const gridStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 20,
};

import type { ToolConfig } from "../api";

interface Props {
  tools: Record<string, ToolConfig>;
  onChange: (tools: Record<string, ToolConfig>) => void;
}

export default function ToolsManager({ tools, onChange }: Props) {
  const toggle = (name: string) => {
    onChange({
      ...tools,
      [name]: { ...tools[name], enabled: !tools[name].enabled },
    });
  };

  return (
    <section style={sectionStyle}>
      <h2>Tools</h2>
      <p style={hintStyle}>
        Enable or disable tools available to the agent during calls.
      </p>

      <div style={listStyle}>
        {Object.entries(tools).map(([name, config]) => (
          <div key={name} style={toolRowStyle}>
            <label style={toggleLabelStyle}>
              <input
                type="checkbox"
                checked={config.enabled}
                onChange={() => toggle(name)}
                style={{ marginRight: 10 }}
              />
              <span>
                <strong>{name.replace(/_/g, " ")}</strong>
                <span style={descStyle}> — {config.description}</span>
              </span>
            </label>
          </div>
        ))}
      </div>
    </section>
  );
}

const sectionStyle: React.CSSProperties = {
  background: "#fff",
  borderRadius: 8,
  padding: 24,
  boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
};

const hintStyle: React.CSSProperties = {
  fontSize: 13,
  color: "#666",
  marginBottom: 16,
};

const listStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 10,
};

const toolRowStyle: React.CSSProperties = {
  padding: "10px 14px",
  border: "1px solid #eee",
  borderRadius: 6,
};

const toggleLabelStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  cursor: "pointer",
  fontSize: 14,
};

const descStyle: React.CSSProperties = {
  color: "#888",
  fontWeight: 400,
};

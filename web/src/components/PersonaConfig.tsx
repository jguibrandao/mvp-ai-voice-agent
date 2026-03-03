import type { PersonaConfig as PersonaType } from "../api";

const VOICE_OPTIONS = [
  "alloy",
  "ash",
  "coral",
  "echo",
  "fable",
  "nova",
  "onyx",
  "sage",
  "shimmer",
];

interface Props {
  persona: PersonaType;
  onChange: (persona: PersonaType) => void;
}

export default function PersonaConfig({ persona, onChange }: Props) {
  const update = (field: keyof PersonaType, value: string) => {
    onChange({ ...persona, [field]: value });
  };

  return (
    <section style={sectionStyle}>
      <h2>Persona</h2>
      <p style={hintStyle}>Configure the agent's identity and voice.</p>

      <div style={fieldStyle}>
        <label style={labelStyle}>Name</label>
        <input
          type="text"
          value={persona.name}
          onChange={(e) => update("name", e.target.value)}
          style={inputStyle}
        />
      </div>

      <div style={fieldStyle}>
        <label style={labelStyle}>Greeting</label>
        <input
          type="text"
          value={persona.greeting}
          onChange={(e) => update("greeting", e.target.value)}
          style={inputStyle}
        />
      </div>

      <div style={fieldStyle}>
        <label style={labelStyle}>Voice</label>
        <select
          value={persona.voice}
          onChange={(e) => update("voice", e.target.value)}
          style={inputStyle}
        >
          {VOICE_OPTIONS.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
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

const fieldStyle: React.CSSProperties = {
  marginBottom: 14,
};

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: 13,
  fontWeight: 600,
  marginBottom: 4,
  color: "#333",
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "8px 12px",
  fontSize: 14,
  border: "1px solid #ddd",
  borderRadius: 6,
  fontFamily: "inherit",
};

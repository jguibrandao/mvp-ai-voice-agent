interface Props {
  value: string;
  onChange: (value: string) => void;
}

export default function SystemPromptEditor({ value, onChange }: Props) {
  return (
    <section style={sectionStyle}>
      <h2>System Prompt</h2>
      <p style={hintStyle}>
        This is the core instruction set for the agent. Changes take effect on
        the next conversation.
      </p>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={8}
        style={textareaStyle}
      />
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
  marginBottom: 12,
};

const textareaStyle: React.CSSProperties = {
  width: "100%",
  fontFamily: "inherit",
  fontSize: 14,
  padding: 12,
  border: "1px solid #ddd",
  borderRadius: 6,
  resize: "vertical",
  lineHeight: 1.5,
};

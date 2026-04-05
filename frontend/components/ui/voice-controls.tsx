export function VoiceControls() {
  return (
    <div className="card">
      <strong>Voice Controls</strong>
      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
        <button type="button">Start recording</button>
        <button type="button">Stop</button>
      </div>
    </div>
  );
}

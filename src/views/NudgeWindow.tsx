import { invoke } from "@tauri-apps/api/core";

interface Props {
  confidence: number;
}
function NudgeWindow({ confidence }: Props) {
  async function handleContinue() {
    await invoke("close_nudge");
  }

  return (
    <main className="nudge-container">
      <h2>Hey, you're slouching!</h2>
      <p className="nudge-score">
        Distraction confidence: {(confidence * 100).toFixed(0)}%
      </p>
      <button onClick={handleContinue}>Continue</button>
    </main>
  );
}
export default NudgeWindow
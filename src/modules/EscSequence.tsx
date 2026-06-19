import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import "../App.css";

interface DetectionResult {
  distracted: boolean;
  confidence: number;
}

export function EscSequence() {
  const [status, setStatus] = useState("Not running");
  const [error, setError] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  async function handleStartClick() {
    setError("");

    if (!isRunning) {
      setIsRunning(true);
      setStatus("Monitoring started...");
      runCheckIn();
    } else {
      setIsRunning(false);
      setIsChecking(false);
      setStatus("Not running");
      try {
        await invoke("stop_detector");
      } catch (_) {
        // already stopped, fine
      }
    }
  }

  async function runCheckIn() {
    setIsChecking(true);
    setStatus("Analyzing posture...");
    try {
      const result = await invoke<DetectionResult>("start_detector");
      setIsChecking(false);

      if (result.distracted) {
        setStatus(`Distracted! (confidence: ${(result.confidence * 100).toFixed(0)}%)`);
      } else {
        setStatus(`Focused! (confidence: ${(result.confidence * 100).toFixed(0)}%)`);
      }
    } catch (err) {
      setIsChecking(false);
      setError(String(err));
      setIsRunning(false);
    }
  }

  return (
    <main className="container">
      <div className="row">
        <img
          src="/cat.png"
          className="logo vite"
          alt="click to start detector"
          onClick={handleStartClick}
        />
      </div>
      <p>Click to (esc)ape your bad habits.</p>
      <p>Status: {isChecking ? "Analyzing posture..." : status}</p>
      {error && <p style={{ color: "#d9784f" }}>{error}</p>}
    </main>
  );
}
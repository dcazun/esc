import { useState, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import "../App.css";

interface DetectionResult {
  distracted: boolean;
  confidence: number;
}

export function EscSequence() {
  // User-defined variables for module
  const [checkInTimer, setcheckInTimer] = useState(1);

  // Check if sequence is running, if so display status
  const [isChecking, setIsChecking] = useState(false);
  const [status, setStatus] = useState("Not running");
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");

  // Inside component, at the top alongside other state:
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function handleStartClick(minutes: number = checkInTimer) {
    setError("");

    // Check running status
    if (!isRunning) {
      setIsRunning(true);
      setStatus("Monitoring started...");
      intervalRef.current = setInterval(() => runCheckIn(), minutes * 60 * 1000);
    } else {
      // Stop Sequence
      // Stop Interval
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }

      // Set Status to Stop
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

      // Check if distracted
      if (result.distracted) {
        setStatus(`Distracted! (confidence: ${(result.confidence * 100).toFixed(0)}%)`);
      } else {
        // Confidence tweaked for user to percieve confidence on result rather than just distractedness
        setStatus(`Focused! (confidence: ${(100 - result.confidence * 100).toFixed(0)}%)`);
      }
      setTimeout(() => {
        setStatus("Monitoring...");
      }, 5000)

    } catch (err) {
      setIsChecking(false);
      setError(String(err));
      setIsRunning(false);
    }
  }

  return (
    <main className="container">
      <div className="iconContainter"
      />
      <div className="row">
        <img
          src="/cat.png"
          className="logo vite"
          alt="click to start detector"
          onClick={() => handleStartClick(checkInTimer)}
        />
      </div>
      <p>{checkInTimer} min</p>
      <p>Click to (esc)ape your bad habits.</p>
      <p>Status: {isChecking ? "Analyzing posture..." : status}</p>
      {error && <p style={{ color: "#d9784f" }}>{error}</p>}
    </main>
  );
}
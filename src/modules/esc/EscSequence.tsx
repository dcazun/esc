import { useState, useEffect, useRef } from "react";
import { load } from "@tauri-apps/plugin-store";
import { useEscController } from "./useEscController";
import "./EscSequence.css";

export function EscSequence() {
  const { isRunning, isChecking, status, error, toggle } = useEscController();
  const [checkInTimer, setCheckInTimer] = useState(5);
  const [elapsed, setElapsed] = useState(0);
  const startTimeRef = useRef<number | null>(null);

  useEffect(() => {
    load("settings.json", { autoSave: true, defaults: { checkInTimer: 5 } })
      .then(async s => {
        const timer = await s.get<number>("checkInTimer");
        if (timer != null) setCheckInTimer(timer);
      });
  }, []);

  // Stopwatch
  useEffect(() => {
    if (isRunning) {
      if (startTimeRef.current === null) {
        startTimeRef.current = Date.now();
      }
      const tick = setInterval(() => {
        setElapsed(Math.floor((Date.now() - (startTimeRef.current ?? Date.now())) / 1000));
      }, 1000);
      return () => clearInterval(tick);
    } else {
      startTimeRef.current = null;
      setElapsed(0);
    }
  }, [isRunning]);

  function formatElapsed(s: number) {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60).toString().padStart(2, "0");
    const sec = (s % 60).toString().padStart(2, "0");
    return h > 0 ? `${h}:${m}:${sec}` : `${m}:${sec}`;
  }

  return (
    <main className="container">
      <img
        src="/cat.png"
        className="logo vite"
        alt={isRunning ? "Stop monitoring" : "Start monitoring"}
        onClick={() => void toggle(checkInTimer)}
      />

      {isRunning
        ? <p className="esc-elapsed">{formatElapsed(elapsed)}</p>
        : <p>{checkInTimer} min</p>
      }
      <p>Status: {isChecking ? "Analyzing posture..." : status}</p>


      {error && <p style={{ color: "#d9784f" }}>{error}</p>}
    </main>
  );
}
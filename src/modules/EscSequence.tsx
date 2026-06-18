import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import "../App.css";

function EscSequence() {
  const [status, setStatus] = useState("Not running!")
  const [error, setError] = useState("")
  const [isRunning, setIsRunning] = useState(false)


  async function handleStartClick() {
    setError("")
    try {
      if (!isRunning) {
        const result = await invoke<string>("start_detector");
        setStatus(result);
        setIsRunning(true);
      }
      else {
        const result = await invoke<string>("stop_detector");
        setStatus(result);
        setIsRunning(false);
      }
    }
    catch (err) {
      setError(String(err));
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

      <p>Status: {status}</p>
      {error && <p style={{ color: "#d9784f" }}>{error}</p>}
    </main>
  );
}

export { EscSequence };

import { useState, useEffect } from "react";
import { View } from "../Shell";
import { load, Store } from "@tauri-apps/plugin-store";
import "./Settings.css";

interface Props {
  onNavigate: (to: View) => void;
}

// Placeholder settings state — will be persisted later
const DEFAULT_SETTINGS = {
  automaticMode: true,
  checkInTimer: 5,
  runAtStartup: true,
};

export function Settings({ onNavigate }: Props) {
  const [automaticMode, setAutomaticMode] = useState(DEFAULT_SETTINGS.automaticMode)
  const [checkInTimer, setCheckInTimer] = useState(DEFAULT_SETTINGS.checkInTimer)
  const [runAtStartup, setRunAtStartup] = useState(DEFAULT_SETTINGS.runAtStartup)
  const [store, setStore] = useState<Store | null>(null);

useEffect(() => {
  load("settings.json", { 
    autoSave: true,
    defaults: {
      automaticMode: DEFAULT_SETTINGS.automaticMode,
      checkInTimer: DEFAULT_SETTINGS.checkInTimer,
      runAtStartup: DEFAULT_SETTINGS.runAtStartup,
    }
    }).then(async s => {
    setStore(s);
    const auto = await s.get<boolean>("automaticMode");
    const timer = await s.get<number>("checkInTimer");
    const startup = await s.get<boolean>("runAtStartup");

    if (auto !== null && auto !== undefined) setAutomaticMode(auto);
    if (timer !== null && timer !== undefined) setCheckInTimer(timer);
    if (startup !== null && startup !== undefined) setRunAtStartup(startup);
  });
}, []);

  // Save a value whenever it changes
  async function saveSetting(key: string, value: boolean | number) {
    if (!store) return;
    await store.set(key, value);
  }

  return (
    <main className="container settings-container">
      <div className="settings-header">
        <button className="back-btn" onClick={() => onNavigate("home")}>
          ← Back
        </button>
        <h2>Settings</h2>
      </div>

      <div className="settings-group">
        <div className="settings-row">
          <div className="settings-label">
            <span>Automatic Mode</span>
            <span className="settings-description">Start check-ins automatically on launch</span>
          </div>
          <input
            type="checkbox"
            checked={automaticMode}
            onChange={e => {
              setAutomaticMode(e.target.checked);
              saveSetting("automaticMode", e.target.checked);
            }}
          />
        </div>

        <div className="settings-row">
          <div className="settings-label">
            <span>Run at Startup</span>
            <span className="settings-description">Launch ESC when you log in</span>
          </div>
          <input
            type="checkbox"
            checked={runAtStartup}
            onChange={e => {
              setRunAtStartup(e.target.checked);
              saveSetting("runAtStartup", e.target.checked);
            }}
          />
        </div>

        <div className="settings-row">
          <div className="settings-label">
            <span>Check-in Interval</span>
            <span className="settings-description">How often to check your posture</span>
          </div>
          <select
            value={checkInTimer}
            onChange={e => {
              const val = Number(e.target.value);
              setCheckInTimer(val);
              saveSetting("checkInTimer", val);
            }}
          >
            <option value={3}>3 min</option>
            <option value={5}>5 min</option>
            <option value={10}>10 min</option>
            <option value={15}>Custom</option>
          </select>
        </div>
      </div>

      <div className="settings-group">
        <div className="settings-row">
          <div className="settings-label">
            <span>Account</span>
            <span className="settings-description">Coming soon</span>
          </div>
        </div>
      </div>
    </main>
  );
}

export default Settings;
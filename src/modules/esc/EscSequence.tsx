import { useState } from "react";
import { useEscController } from "./useEscController";
import "./EscSequence.css";
import "../../App.css";

interface CardItem {
  label: string;
  minutes: number;
  icon: string;
}

const ITEMS: CardItem[] = [
  { label: "3 min", minutes: 3, icon: "/cat.png" },
  { label: "5 min", minutes: 5, icon: "/cat1.png" },
  { label: "10 min", minutes: 10, icon: "/cat2.jpg" },
  { label: "Custom", minutes: 15, icon: "/cat3.jpg" },
];

export function EscSequence() {
  const [current, setCurrent] = useState(0);
  const [customMinutes, setCustomMinutes] = useState(15);

  const {
    isRunning,
    isChecking,
    status,
    error,
    toggle,
  } = useEscController();

  const selectedMinutes =
    current === 3
      ? customMinutes
      : ITEMS[current].minutes;

  function goLeft() {
    if (isRunning) {
      return;
    }

    setCurrent(
      (current - 1 + ITEMS.length) % ITEMS.length
    );
  }

  function goRight() {
    if (isRunning) {
      return;
    }

    setCurrent(
      (current + 1) % ITEMS.length
    );
  }

  return (
    <main className="container">
      <div
        className="row"
        style={{
          alignItems: "center",
          gap: 10,
        }}
      >
        <button
          onClick={goLeft}
          disabled={isRunning}
        >
          ⟨
        </button>

        <img
          src={ITEMS[current].icon}
          className="logo vite"
          alt={
            isRunning
              ? "Stop monitoring"
              : "Start monitoring"
          }
          onClick={() => {
            void toggle(selectedMinutes);
          }}
        />

        <button
          onClick={goRight}
          disabled={isRunning}
        >
          ⟩
        </button>
      </div>

      {current === 3 ? (
        <div>
          <input
            type="number"
            min={1}
            max={60}
            value={customMinutes}
            disabled={isRunning}
            onChange={(event) => {
              const value = Math.max(
                1,
                Number.parseInt(event.target.value) || 1
              );

              setCustomMinutes(value);
            }}
          />
          <span>min</span>
        </div>
      ) : (
        <p>{ITEMS[current].label}</p>
      )}

      <p>
        Status:{" "}
        {isChecking
          ? "Analyzing posture..."
          : status}
      </p>

      {error && (
        <p style={{ color: "#d9784f" }}>
          {error}
        </p>
      )}
    </main>
  );
}
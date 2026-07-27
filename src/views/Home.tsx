import { View } from "../Shell";
import { EscSequence } from "../modules/esc/EscSequence"
import Sessions from "../modules/sessions/Sessions";

interface Props {
  onNavigate: (to: View) => void;
}

function Home({ onNavigate }: Props) {
  return (
    <main className="container" style={{ position: "relative" }}>
      <button
        onClick={() => onNavigate("settings")}
        style={{
          position: "absolute",
          top: 12,
          right: 12,
          background: "none",
          border: "none",
          fontSize: "1.2rem",
          cursor: "pointer",
          opacity: 0.6,
          boxShadow: "none",
        }}>
        ⚙
      </button>
      <h1>ESC</h1>

      <div
        style={{
          display: "flex",
          gap: "0.0001rem",
          alignItems: "center",
          width: "100%",
        }}
      >
        <div style={{ flex: 1 }}>
          <Sessions />
        </div>

        <div style={{ flex: 1 }}>
          <EscSequence />
        </div>
      </div>
    </main>
  );
}

export default Home;

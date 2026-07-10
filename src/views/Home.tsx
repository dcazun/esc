import { View } from "../Shell";
import { EscSequence } from "../modules/esc/EscSequence"

interface Props {
  onNavigate: (to: View) => void;
}

function Home({ onNavigate }: Props) {
  return (
    <main className="container">
      <div style={{ display: "flex", justifyContent: "flex-end", width: "100%" }}>
        <button
          onClick={() => onNavigate("settings")}
          style={{ background: "none", border: "none", fontSize: "1.2rem",
                   cursor: "pointer", opacity: 0.6, boxShadow: "none" }}>
          ⚙
        </button>
      </div>
      <h1>ESC</h1>
      <EscSequence />
    </main>
  );
}

export default Home;

import "../App.css";
import { EscSequence } from "../modules/EscSequence"

function Home() {
  return (
    <main className="container">
      <h1>Welcome to ESC</h1>
      <EscSequence />
    </main>
  );
}

export default Home;

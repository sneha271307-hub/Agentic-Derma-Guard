import { useState } from "react";
import Header from "./components/Header.jsx";
import ScreenPage from "./pages/ScreenPage.jsx";
import BatchPage from "./pages/BatchPage.jsx";
import AgentsPage from "./pages/AgentsPage.jsx";
import { IS_DEMO } from "./config";

export default function App() {
  const [tab, setTab] = useState("screen");

  return (
    <div className="app">
      <a className="skip" href="#main">Skip to content</a>
      <Header tab={tab} onTab={setTab} demo={IS_DEMO} />
      <main id="main" className="main">
        {/* ScreenPage stays mounted so a result is not lost when you switch tabs */}
        <div hidden={tab !== "screen"}><ScreenPage /></div>
        {tab === "batch" && <BatchPage />}
        {tab === "agents" && <AgentsPage />}
      </main>
      <footer className="footer">
        <p>
          DermaGuard is a hackathon research prototype built on the HAM10000 dataset. It is not a medical device and
          does not replace a doctor.
        </p>
      </footer>
    </div>
  );
}

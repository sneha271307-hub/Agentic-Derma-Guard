const TABS = [
  { id: "screen", label: "Screen a photo" },
  { id: "batch", label: "Batch results" },
  { id: "agents", label: "How the agents work" },
];

function Logo() {
  return (
    <svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true">
      <circle cx="32" cy="32" r="29" fill="var(--lens)" />
      <circle cx="32" cy="32" r="20" fill="none" stroke="var(--blush)" strokeWidth="3" />
      <circle cx="32" cy="32" r="7" fill="var(--teal-bright)" />
      <path d="M32 3v8M32 53v8M3 32h8M53 32h8" stroke="var(--blush)" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export default function Header({ tab, onTab, demo, theme, onThemeChange }) {
  return (
    <header className="header">
      <div className="header__inner">
        <div className="brand">
          <Logo />
          <div>
            <p className="brand__name">DermaGuard</p>
            <p className="brand__sub">Three agents, one triage decision</p>
          </div>
        </div>

        <nav className="tabs" aria-label="Main">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={"tab" + (tab === t.id ? " tab--on" : "")}
              aria-current={tab === t.id ? "page" : undefined}
              onClick={() => onTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <span className={"mode " + (demo ? "mode--demo" : "mode--live")}>
          {demo ? "Demo mode" : "Live models"}
        </span>
        <button
          className="theme-toggle"
          type="button"
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          aria-pressed={theme === "dark"}
          onClick={() => onThemeChange(theme === "dark" ? "light" : "dark")}
        >
          <span aria-hidden="true">{theme === "dark" ? "☀" : "◐"}</span>
          <span>{theme === "dark" ? "Light" : "Dark"}</span>
        </button>
      </div>
    </header>
  );
}

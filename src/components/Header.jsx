const TABS = [
  { id: "screen", label: "Screen a photo" },
  { id: "batch", label: "Batch results" },
  { id: "agents", label: "How the agents work" },
];

function Logo() {
  return (
    <svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true">
      <circle cx="32" cy="32" r="29" fill="#10292B" />
      <circle cx="32" cy="32" r="20" fill="none" stroke="#E9CDBB" strokeWidth="3" />
      <circle cx="32" cy="32" r="7" fill="#2FA38F" />
      <path d="M32 3v8M32 53v8M3 32h8M53 32h8" stroke="#E9CDBB" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export default function Header({ tab, onTab, demo }) {
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
      </div>
    </header>
  );
}

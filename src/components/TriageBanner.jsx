const LOOK = {
  AUTO_TRIAGE: { cls: "triage--auto", label: "AUTO_TRIAGE", icon: "✓" },
  REFER: { cls: "triage--refer", label: "REFER", icon: "→" },
  RE_IMAGE: { cls: "triage--re", label: "RE_IMAGE", icon: "↻" },
};

export default function TriageBanner({ triage }) {
  if (!triage) {
    return (
      <article className="triage triage--idle">
        <p className="triage__tag">Final decision</p>
        <p className="triage__headline">Waiting for the agents</p>
        <p className="triage__summary">The Triage Agent will choose AUTO_TRIAGE, REFER or RE_IMAGE after the other two agents report.</p>
      </article>
    );
  }
  const look = LOOK[triage.decision] || LOOK.REFER;

  return (
    <article className={"triage " + look.cls} aria-live="polite">
      <div className="triage__row">
        <span className="triage__icon" aria-hidden="true">{look.icon}</span>
        <p className="triage__tag">{look.label}</p>
      </div>
      <p className="triage__headline">{triage.headline}</p>
      <p className="triage__summary">{triage.summary}</p>
      <ul className="triage__why">
        {triage.reasons.map((r, i) => <li key={i}>{r}</li>)}
      </ul>
    </article>
  );
}

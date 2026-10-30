export default function QualityCard({ quality }) {
  if (!quality) {
    return (
      <article className="card card--empty">
        <h2 className="card__title">Image Quality Agent</h2>
        <p className="empty">Add a photo and run the agents. This card will show a quality score and the reason behind it.</p>
      </article>
    );
  }

  const good = quality.status === "GOOD";
  const R = 34;
  const C = 2 * Math.PI * R;
  const offset = C * (1 - quality.score / 100);

  return (
    <article className="card">
      <div className="card__head">
        <h2 className="card__title">Image Quality Agent</h2>
        <span className={"chip " + (good ? "chip--good" : "chip--bad")}>{good ? "Good photo" : "Poor photo"}</span>
      </div>

      <div className="quality">
        <div className="gauge" role="img" aria-label={`Quality score ${quality.score} out of 100`}>
          <svg viewBox="0 0 88 88">
            <circle cx="44" cy="44" r={R} fill="none" stroke="var(--line)" strokeWidth="8" />
            <circle
              cx="44" cy="44" r={R} fill="none" strokeWidth="8" strokeLinecap="round"
              stroke={good ? "var(--green)" : "var(--coral)"}
              strokeDasharray={C} strokeDashoffset={offset}
              transform="rotate(-90 44 44)"
            />
          </svg>
          <span className="gauge__num">{quality.score}</span>
        </div>

        <ul className="checks">
          {quality.checks.map((c) => (
            <li key={c.key} className="check">
              <span className={"check__icon " + (c.pass ? "check__icon--ok" : "check__icon--no")} aria-hidden="true">
                {c.pass ? "✓" : "!"}
              </span>
              <span className="check__body">
                <span className="check__label">{c.label} <span className="check__val">{c.value}</span></span>
                <span className="check__detail">{c.detail}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
    </article>
  );
}

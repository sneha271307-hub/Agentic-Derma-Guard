import { LESION_CLASSES, CLASS_BY_CODE } from "../data/classes";

export default function DiagnosisCard({ diagnosis, demo }) {
  if (!diagnosis) {
    return (
      <article className="card card--empty">
        <h2 className="card__title">Diagnosis Agent</h2>
        <p className="empty">It predicts one of seven lesion classes and shows how sure it is for each one.</p>
      </article>
    );
  }

  const top = CLASS_BY_CODE[diagnosis.predicted_class];
  const rows = LESION_CLASSES
    .map((c) => ({ ...c, p: diagnosis.probabilities[c.code] ?? 0 }))
    .sort((a, b) => b.p - a.p);

  return (
    <article className="card">
      <div className="card__head">
        <h2 className="card__title">Diagnosis Agent</h2>
        {demo && <span className="chip chip--note">Simulated result</span>}
      </div>

      <p className="dx__top">
        <span className="dx__name">{top.name}</span>
        <span className="dx__conf">{Math.round(diagnosis.confidence * 100)}% sure</span>
      </p>
      <p className="dx__note">{top.note}</p>

      <ul className="bars">
        {rows.map((r, i) => (
          <li key={r.code} className="bar">
            <span className="bar__label">
              {r.name}
              {r.risk === "high" && <span className="bar__risk">needs a doctor</span>}
            </span>
            <span className="bar__track">
              <span
                className={"bar__fill" + (r.risk === "high" ? " bar__fill--high" : "") + (i === 0 ? " bar__fill--top" : "")}
                style={{ width: `${Math.max(1.5, r.p * 100)}%` }}
              />
            </span>
            <span className="bar__pct">{(r.p * 100).toFixed(1)}%</span>
          </li>
        ))}
      </ul>
    </article>
  );
}

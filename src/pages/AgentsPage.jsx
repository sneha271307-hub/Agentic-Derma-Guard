import { QUALITY_THRESHOLDS as Q, TRIAGE_RULES as R } from "../config";

const AGENTS = [
  {
    name: "Image Quality Agent",
    role: "Gatekeeper",
    does: "Looks at the photo before anyone tries to diagnose it.",
    rows: [
      ["Reads", "The raw image pixels"],
      ["Checks", "Blur, lighting, glare, obstruction"],
      ["Returns", "A 0 to 100 score, GOOD or POOR, and the reasons"],
    ],
  },
  {
    name: "Diagnosis Agent",
    role: "Specialist",
    does: "Predicts which of the seven lesion classes the photo shows.",
    rows: [
      ["Reads", "The same image"],
      ["Model", "Deep learning model trained on 7,815 images"],
      ["Returns", "Predicted class and a probability for each class"],
    ],
  },
  {
    name: "Triage Agent",
    role: "Decision maker",
    does: "Combines the first two reports into one explained decision.",
    rows: [
      ["Reads", "Quality report and diagnosis report"],
      ["Rules", "Plain-language rules, listed below"],
      ["Returns", "AUTO_TRIAGE, REFER or RE_IMAGE, with reasons"],
    ],
  },
];

export default function AgentsPage() {
  const rules = [
    ["1", "RE_IMAGE", "Photo is poor, or its quality score is below " + R.minQualityScore + "."],
    ["2", "REFER", "Predicted class is melanoma, basal cell carcinoma or actinic keratosis."],
    ["3", "REFER", "Melanoma probability is " + Math.round(R.melWatch * 100) + "% or more, even if another class is on top."],
    ["4", "REFER", "Confidence is below " + Math.round(R.minConfidence * 100) + "%, so a human decides."],
    ["5", "AUTO_TRIAGE", "None of the above. Clear photo, confident, low-risk result."],
  ];

  return (
    <div className="page">
      <div className="page__head">
        <div>
          <h1 className="h1">How the agents work</h1>
          <p className="lead">Each agent has its own job. None of them can make the final call alone.</p>
        </div>
      </div>

      <div className="three">
        {AGENTS.map((a) => (
          <article key={a.name} className="card agent">
            <p className="agent__role">{a.role}</p>
            <h2 className="card__title">{a.name}</h2>
            <p className="agent__does">{a.does}</p>
            <dl className="agent__list">
              {a.rows.map(([k, v]) => (
                <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
              ))}
            </dl>
          </article>
        ))}
      </div>

      <div className="card">
        <h2 className="card__title">Triage rules, checked in this order</h2>
        <ol className="rules">
          {rules.map(([n, d, text]) => (
            <li key={n} className="rule">
              <span className="rule__n">{n}</span>
              <span className={"dec dec--" + d.toLowerCase()}>{d}</span>
              <span className="rule__text">{text}</span>
            </li>
          ))}
        </ol>
      </div>

      <div className="card">
        <h2 className="card__title">Photo quality limits</h2>
        <div className="limits">
          <p><strong>Sharpness</strong> at least {Q.blurMin}</p>
          <p><strong>Brightness</strong> between {Q.darkMean} and {Q.brightMean}</p>
          <p><strong>Glare</strong> up to {Q.glareMax * 100}% bright pixels</p>
          <p><strong>Obstruction</strong> up to {Q.obstructionMax * 100}% dark pixels</p>
        </div>
        <p className="muted">Change these in <code>src/config.js</code>. Every page updates automatically.</p>
      </div>
    </div>
  );
}

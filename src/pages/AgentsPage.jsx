import { QUALITY_THRESHOLDS as Q, TRIAGE_RULES as R } from "../config";

const AGENTS = [
  { name: "Image Quality Agent", role: "A1 · Image gate", does: "Checks whether the uploaded photo can support review.", rows: [["Reads", "Image pixels"], ["Checks", "Blur, lighting, glare and obstruction"], ["Returns", "Quality score, PASS/RE-IMAGE cues and reliability reasons"]] },
  { name: "Diagnosis Agent", role: "A2 · Classifier", does: "Predicts one of the seven supported lesion classes.", rows: [["Reads", "The same lesion photo"], ["Model", "Configured live model or clearly marked demo simulation"], ["Returns", "Predicted label, confidence and class probabilities"]] },
  { name: "Lesion Analysis Agent", role: "A3 · Visual evidence", does: "Surfaces approximate asymmetry, border and color variation cues.", rows: [["Reads", "Image pixels and A1 quality result"], ["Checks", "Asymmetry, border variation and color spread"], ["Returns", "Feature evidence, suspicion score and reliability flags"]] },
  { name: "Reasoning / Context Agent", role: "A4 · Context", does: "Uses only optional age, gender and lesion location supplied by the user.", rows: [["Reads", "User-provided context"], ["Checks", "Context risk indicators and missing fields"], ["Returns", "Context evidence, risk indicator and missing-field flags"]] },
  { name: "Safety Agent", role: "A5 · Safety review", does: "Checks image quality, diagnosis, visual evidence and context for conflicts.", rows: [["Reads", "A1–A4 reports"], ["Checks", "Conflicts and unsafe automatic decisions"], ["Returns", "Safety flag, veto, trigger and justification"]] },
  { name: "Coordinator Agent", role: "A6 · Decision policy", does: "Applies the documented policy to all five upstream reports.", rows: [["Reads", "A1–A5 outputs"], ["Checks", "RE_IMAGE / REFER / AUTO_TRIAGE rules"], ["Returns", "Predicted label, final disposition and traceable rationale"]] },
];

export default function AgentsPage() {
  const rules = [
    ["1", "RE_IMAGE", "Image quality is poor or the quality score is below " + R.minQualityScore + "."],
    ["2", "REFER", "Safety Agent flags a conflict, reliability concern or context risk."],
    ["3", "REFER", "The diagnosis is a high-risk class or melanoma probability is at least " + Math.round(R.melWatch * 100) + "%."],
    ["4", "REFER", "Diagnosis confidence is below " + Math.round(R.minConfidence * 100) + "%, or lesion analysis raises suspicion."],
    ["5", "AUTO_TRIAGE", "No earlier rule applies: quality passes and evidence supports a confident, low-risk screening disposition."],
  ];

  return (
    <div className="page">
      <div className="page__head"><div><h1 className="h1">How the six agents work</h1><p className="lead">Each image receives a diagnosis prediction and a separate triage decision. Every report is shown so the final policy can be traced.</p></div></div>
      <div className="agent-grid">
        {AGENTS.map((a) => <article key={a.name} className="card agent">
          <p className="agent__role">{a.role}</p><h2 className="card__title">{a.name}</h2><p className="agent__does">{a.does}</p>
          <dl className="agent__list">{a.rows.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
        </article>)}
      </div>
      <div className="card">
        <h2 className="card__title">Coordinator decision rules, checked in this order</h2>
        <ol className="rules">{rules.map(([n, d, text]) => <li key={n} className="rule"><span className="rule__n">{n}</span><span className={"dec dec--" + d.toLowerCase()}>{d}</span><span className="rule__text">{text}</span></li>)}</ol>
      </div>
      <div className="card">
        <h2 className="card__title">Image quality limits</h2>
        <div className="limits"><p><strong>Sharpness</strong> at least {Q.blurMin}</p><p><strong>Brightness</strong> between {Q.darkMean} and {Q.brightMean}</p><p><strong>Glare</strong> up to {Q.glareMax * 100}% bright pixels</p><p><strong>Obstruction</strong> up to {Q.obstructionMax * 100}% dark pixels</p></div>
        <p className="muted">Lesion visual cues and context flags are screening heuristics. They are not clinical diagnoses or validated risk estimates.</p>
      </div>
    </div>
  );
}

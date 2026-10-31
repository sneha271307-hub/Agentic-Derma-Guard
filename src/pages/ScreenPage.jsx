import { useEffect, useState } from "react";
import DermoLens from "../components/DermoLens.jsx";
import Pipeline from "../components/Pipeline.jsx";
import QualityCard from "../components/QualityCard.jsx";
import DiagnosisCard from "../components/DiagnosisCard.jsx";
import TriageBanner from "../components/TriageBanner.jsx";
import { runPipeline } from "../api/dermaguard";
import { IS_DEMO } from "../config";

const MAX_MB = 15;

export default function ScreenPage() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [stage, setStage] = useState("idle");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [patientContext, setPatientContext] = useState({ age: "", gender: "", location: "" });

  useEffect(() => () => previewUrl && URL.revokeObjectURL(previewUrl), [previewUrl]);

  const busy = stage !== "idle" && stage !== "done";

  const handleFile = (f) => {
    if (!f.type.startsWith("image/")) return setError("That file is not an image. Choose a JPG or PNG.");
    if (f.size > MAX_MB * 1024 * 1024) return setError(`That image is larger than ${MAX_MB} MB. Choose a smaller one.`);
    setError("");
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
    setResult(null);
    setStage("idle");
  };

  const clear = () => {
    setFile(null);
    setPreviewUrl("");
    setResult(null);
    setStage("idle");
    setError("");
  };

  const analyze = async () => {
    if (!file) return;
    setError("");
    setResult(null);
    try {
      const out = await runPipeline(file, patientContext, setStage);
      setResult(out);
      setStage("done");
    } catch (e) {
      setError(e.message || "Something went wrong. Try again.");
      setStage("idle");
    }
  };

  return (
    <div className="screen">
      <DermoLens
        previewUrl={previewUrl}
        busy={busy}
        scanning={busy}
        onFile={handleFile}
        onClear={clear}
        onAnalyze={analyze}
      />

      <div className="results">
        <div className="results__top">
          <h1 className="h1">Screen a skin lesion photo</h1>
          <p className="lead">
            Six agents check photo quality, predict the lesion, inspect visual cues, consider optional context, review safety, and record a final triage decision.
          </p>
          <Pipeline stage={stage} />
        </div>

        {error && <p className="alert" role="alert">{error}</p>}

        <section className="card context-form" aria-labelledby="context-title">
          <div className="card__head">
            <h2 className="card__title" id="context-title">Optional patient context</h2>
            <span className="chip chip--note">A4 Reasoning / Context</span>
          </div>
          <p className="muted">Context can flag uncertainty for review. Missing fields are recorded and never guessed.</p>
          <div className="context-fields">
            <label>Age
              <input type="number" min="0" max="120" value={patientContext.age} onChange={(e) => setPatientContext({ ...patientContext, age: e.target.value })} placeholder="e.g. 42" />
            </label>
            <label>Gender
              <select value={patientContext.gender} onChange={(e) => setPatientContext({ ...patientContext, gender: e.target.value })}>
                <option value="">Not provided</option><option>Female</option><option>Male</option><option>Another identity</option><option>Prefer not to say</option>
              </select>
            </label>
            <label>Lesion location
              <input type="text" value={patientContext.location} onChange={(e) => setPatientContext({ ...patientContext, location: e.target.value })} placeholder="e.g. forearm" />
            </label>
          </div>
        </section>

        <TriageBanner triage={result?.triage} />
        <div className="two">
          <QualityCard quality={result?.quality} />
          <DiagnosisCard diagnosis={result?.diagnosis} demo={IS_DEMO} />
        </div>
        <div className="two">
          <article className="card agent-report">
            <div className="card__head"><h2 className="card__title">A3 · Lesion Analysis Agent</h2><span className="chip chip--note">Heuristic cues</span></div>
            {!result?.lesionAnalysis ? <p className="empty">Checks asymmetry, border and color variation after analysis.</p> : <>
              <p><strong>{result.lesionAnalysis.suspicion}</strong> · suspicion score {result.lesionAnalysis.suspicionScore}/100</p>
              <ul className="report-list">{result.lesionAnalysis.featureEvidence.map((item) => <li key={item.label}><strong>{item.label}: {item.value}</strong><span>{item.detail}</span></li>)}</ul>
              {result.lesionAnalysis.reliabilityFlags.map((flag) => <p className="report-flag" key={flag}>{flag}</p>)}
              <p className="muted">Approximate image-pixel cues; not a clinical lesion detector.</p>
            </>}
          </article>
          <article className="card agent-report">
            <div className="card__head"><h2 className="card__title">A4 · Reasoning / Context Agent</h2><span className="chip chip--note">Context review</span></div>
            {!result?.context ? <p className="empty">Uses only the age, gender and lesion location you provide.</p> : <>
              <p><strong>{result.context.riskLevel}</strong></p>
              <ul className="report-list">{result.context.evidence.map((item) => <li key={item}>{item}</li>)}</ul>
              {result.context.riskIndicators.map((item) => <p className="report-flag" key={item}>{item}</p>)}
              {result.context.missingFields.map((item) => <p className="muted" key={item}>{item}</p>)}
            </>}
          </article>
          <article className="card agent-report">
            <div className="card__head"><h2 className="card__title">A5 · Safety Agent</h2><span className={"chip " + (result?.safety?.flag === "SAFETY_FLAG" ? "chip--bad" : "chip--good")}>{result?.safety?.flag || "Waiting"}</span></div>
            {!result?.safety ? <p className="empty">Checks evidence conflicts and blocks automatic decisions when warranted.</p> : <>
              <p><strong>Trigger:</strong> {result.safety.trigger}</p>
              <p>{result.safety.justification}</p>
              {result.safety.conflicts.map((item) => <p className="report-flag" key={item}>{item}</p>)}
            </>}
          </article>
          <article className="card agent-report">
            <div className="card__head"><h2 className="card__title">A6 · Coordinator Agent</h2><span className="chip chip--good">Traceable policy</span></div>
            {!result?.coordinator ? <p className="empty">Combines all five agent reports into the diagnosis label and final triage.</p> : <>
              <p><strong>Predicted label:</strong> {result.coordinator.predictedLabel}</p>
              <p><strong>Final disposition:</strong> {result.coordinator.decision}</p>
              <p>{result.coordinator.rationale}</p>
            </>}
          </article>
        </div>
      </div>
    </div>
  );
}

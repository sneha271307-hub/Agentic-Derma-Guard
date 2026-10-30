import { useMemo, useRef, useState } from "react";
import { makeSampleBatch } from "../data/sampleBatch";
import { CLASS_BY_CODE } from "../data/classes";

const DECISIONS = ["ALL", "AUTO_TRIAGE", "REFER", "RE_IMAGE"];
const nameOf = (code) => CLASS_BY_CODE[code]?.name || code;

export default function BatchPage() {
  const [rows, setRows] = useState(() => makeSampleBatch(30));
  const [isSample, setIsSample] = useState(true);
  const [filter, setFilter] = useState("ALL");
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  const stats = useMemo(() => {
    const labelled = rows.filter((r) => r.true_label);
    const correct = labelled.filter((r) => r.true_label === r.predicted_class).length;
    const count = (d) => rows.filter((r) => r.decision === d).length;
    return {
      total: rows.length,
      accuracy: labelled.length ? correct / labelled.length : null,
      auto: count("AUTO_TRIAGE"),
      refer: count("REFER"),
      re: count("RE_IMAGE"),
      poor: rows.filter((r) => r.quality_status === "POOR").length,
    };
  }, [rows]);

  const shown = filter === "ALL" ? rows : rows.filter((r) => r.decision === filter);

  const loadJson = async (file) => {
    setError("");
    try {
      const data = JSON.parse(await file.text());
      if (!Array.isArray(data) || data.length === 0) throw new Error("empty");
      const ok = data.every((r) => r.id && r.predicted_class);
      if (!ok) throw new Error("fields");
      setRows(data);
      setIsSample(false);
      setFilter("ALL");
    } catch {
      setError("Could not read that file. It must be a JSON list where every item has at least an id and a predicted_class.");
    }
  };

  const pct = (v) => `${Math.round(v * 100)}%`;
  const split = [
    { k: "AUTO_TRIAGE", n: stats.auto, cls: "split__seg--auto" },
    { k: "REFER", n: stats.refer, cls: "split__seg--refer" },
    { k: "RE_IMAGE", n: stats.re, cls: "split__seg--re" },
  ];

  return (
    <div className="page">
      <div className="page__head">
        <div>
          <h1 className="h1">Batch results</h1>
          <p className="lead">
            See how the agents did across many images, such as the 2,000 validation images.
            {isSample && " You are looking at sample data until you load real results."}
          </p>
        </div>
        <div className="page__actions">
          <button className="btn btn--primary" onClick={() => inputRef.current?.click()}>Load results (JSON)</button>
          {!isSample && (
            <button className="btn btn--ghost" onClick={() => { setRows(makeSampleBatch(30)); setIsSample(true); }}>
              Back to sample data
            </button>
          )}
          <input ref={inputRef} type="file" accept="application/json,.json" hidden
            onChange={(e) => { const f = e.target.files?.[0]; if (f) loadJson(f); e.target.value = ""; }} />
        </div>
      </div>

      {error && <p className="alert" role="alert">{error}</p>}

      <div className="stats">
        <div className="stat"><p className="stat__num">{stats.total}</p><p className="stat__label">Images</p></div>
        <div className="stat"><p className="stat__num">{stats.accuracy === null ? "n/a" : pct(stats.accuracy)}</p><p className="stat__label">Diagnosis accuracy</p></div>
        <div className="stat"><p className="stat__num">{stats.poor}</p><p className="stat__label">Poor-quality photos</p></div>
        <div className="stat"><p className="stat__num">{stats.refer}</p><p className="stat__label">Sent to a doctor</p></div>
      </div>

      <div className="card">
        <h2 className="card__title">Where the decisions went</h2>
        <div className="split" role="img" aria-label={`${stats.auto} auto triage, ${stats.refer} refer, ${stats.re} re-image`}>
          {split.map((s) => s.n > 0 && (
            <span key={s.k} className={"split__seg " + s.cls} style={{ flexGrow: s.n }}>{s.n}</span>
          ))}
        </div>
        <div className="legend">
          <span><i className="dot dot--auto" />AUTO_TRIAGE</span>
          <span><i className="dot dot--refer" />REFER</span>
          <span><i className="dot dot--re" />RE_IMAGE</span>
        </div>
      </div>

      <div className="card">
        <div className="card__head">
          <h2 className="card__title">Image by image</h2>
          <label className="select">
            <span className="select__label">Show</span>
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              {DECISIONS.map((d) => <option key={d} value={d}>{d === "ALL" ? "All decisions" : d}</option>)}
            </select>
          </label>
        </div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Image</th><th>Quality</th><th>Predicted</th><th>Actual</th><th>Confidence</th><th>Decision</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((r) => {
                const wrong = r.true_label && r.true_label !== r.predicted_class;
                return (
                  <tr key={r.id}>
                    <td className="mono">{r.id}</td>
                    <td>
                      <span className={"chip " + (r.quality_status === "POOR" ? "chip--bad" : "chip--good")}>
                        {r.quality_score ?? "-"} {r.quality_status === "POOR" ? "poor" : "good"}
                      </span>
                      {r.quality_reason && <span className="table__sub">{r.quality_reason}</span>}
                    </td>
                    <td className={wrong ? "wrong" : ""}>{nameOf(r.predicted_class)}</td>
                    <td>{r.true_label ? nameOf(r.true_label) : "-"}</td>
                    <td className="mono">{r.confidence != null ? pct(r.confidence) : "-"}</td>
                    <td><span className={"dec dec--" + String(r.decision).toLowerCase()}>{r.decision}</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="table__foot">Highlighted predicted classes did not match the actual label.</p>
      </div>
    </div>
  );
}

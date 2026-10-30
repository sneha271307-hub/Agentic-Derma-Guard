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
      const out = await runPipeline(file, setStage);
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
            Three agents read the same photo. The first checks it is usable, the second predicts the lesion, the third
            decides what happens next.
          </p>
          <Pipeline stage={stage} />
        </div>

        {error && <p className="alert" role="alert">{error}</p>}

        <TriageBanner triage={result?.triage} />
        <div className="two">
          <QualityCard quality={result?.quality} />
          <DiagnosisCard diagnosis={result?.diagnosis} demo={IS_DEMO} />
        </div>
      </div>
    </div>
  );
}

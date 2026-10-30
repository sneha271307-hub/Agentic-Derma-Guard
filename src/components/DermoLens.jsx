import { useRef, useState } from "react";

// The signature element: the photo sits inside a dermoscope-style lens.
export default function DermoLens({ previewUrl, busy, onFile, onClear, onAnalyze, scanning }) {
  const inputRef = useRef(null);
  const [over, setOver] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onFile(f);
  };

  return (
    <section className="lens-panel" aria-label="Photo upload">
      <div
        className={"lens" + (over ? " lens--over" : "") + (scanning ? " lens--scan" : "")}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={handleDrop}
      >
        <svg className="lens__ring" viewBox="0 0 200 200" aria-hidden="true">
          <circle cx="100" cy="100" r="96" fill="none" stroke="var(--blush)" strokeWidth="2" />
          <circle cx="100" cy="100" r="88" fill="none" stroke="var(--teal-bright)" strokeWidth="1" strokeDasharray="2 5" />
          {Array.from({ length: 36 }).map((_, i) => {
            const a = (i * 10 * Math.PI) / 180;
            const long = i % 3 === 0;
            const r1 = long ? 80 : 84;
            return (
              <line
                key={i}
                x1={100 + r1 * Math.cos(a)} y1={100 + r1 * Math.sin(a)}
                x2={100 + 88 * Math.cos(a)} y2={100 + 88 * Math.sin(a)}
                stroke="var(--blush)" strokeWidth={long ? 1.5 : 0.8} opacity={long ? 0.9 : 0.5}
              />
            );
          })}
        </svg>

        <div className="lens__glass">
          {previewUrl ? (
            <img src={previewUrl} alt="Skin lesion photo you uploaded" className="lens__img" />
          ) : (
            <button className="lens__empty" onClick={() => inputRef.current?.click()}>
              <span className="lens__plus" aria-hidden="true">+</span>
              <span className="lens__hint">Drop a dermoscopic photo here</span>
              <span className="lens__sub">or click to choose a JPG or PNG</span>
            </button>
          )}
          <span className="lens__cross lens__cross--h" aria-hidden="true" />
          <span className="lens__cross lens__cross--v" aria-hidden="true" />
          <span className="lens__sweep" aria-hidden="true" />
        </div>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        hidden
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); e.target.value = ""; }}
      />

      <div className="lens-actions">
        <button className="btn btn--primary" disabled={!previewUrl || busy} onClick={onAnalyze}>
          {busy ? "Agents are working" : "Diagnosis"}
        </button>
        <button className="btn btn--ghost" disabled={busy} onClick={() => (previewUrl ? onClear() : inputRef.current?.click())}>
          {previewUrl ? "Remove photo" : "Choose photo"}
        </button>
      </div>

      <p className="lens-tip">
        Best results: lesion centered, even light, no hair or ruler across it, photo in focus.
      </p>
    </section>
  );
}

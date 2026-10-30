// SAMPLE validation results so the Batch page looks alive before the real model is ready.
// Replace this with your teammates' real output (see README, "Loading real batch results").
import { LESION_CLASSES } from "./classes";

function rng(seed) {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

const prior = [0.033, 0.051, 0.11, 0.011, 0.111, 0.669, 0.014];
const reasons = ["Blur", "Glare", "Too dark", "Obstruction"];

function pick(rand, weights) {
  const total = weights.reduce((a, b) => a + b, 0);
  let x = rand() * total;
  for (let i = 0; i < weights.length; i++) {
    x -= weights[i];
    if (x <= 0) return i;
  }
  return weights.length - 1;
}

export function makeSampleBatch(n = 30) {
  const rand = rng(2026);
  const rows = [];
  for (let i = 0; i < n; i++) {
    const t = pick(rand, prior);
    const correct = rand() < 0.78;
    const p = correct ? t : pick(rand, prior);
    const conf = correct ? 0.55 + rand() * 0.42 : 0.35 + rand() * 0.4;
    const poor = rand() < 0.13;
    const quality = poor ? Math.round(25 + rand() * 30) : Math.round(68 + rand() * 30);
    const predicted = LESION_CLASSES[p];
    let decision = "AUTO_TRIAGE";
    if (poor) decision = "RE_IMAGE";
    else if (predicted.risk === "high" || conf < 0.6) decision = "REFER";
    rows.push({
      id: "ISIC_00" + (24300 + i * 7),
      true_label: LESION_CLASSES[t].code,
      predicted_class: predicted.code,
      confidence: Number(conf.toFixed(2)),
      quality_score: quality,
      quality_status: poor ? "POOR" : "GOOD",
      quality_reason: poor ? reasons[Math.floor(rand() * reasons.length)] : "",
      decision,
    });
  }
  return rows;
}

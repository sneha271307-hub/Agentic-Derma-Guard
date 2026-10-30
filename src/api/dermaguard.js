// The ONE place where the frontend talks to the models.
//
// DEMO mode (no VITE_API_URL): quality is measured for real in the browser,
//                              diagnosis is a clearly-labelled mock.
// LIVE mode (VITE_API_URL set): the image is sent to your teammates' backend.
//
// Expected backend response for POST {API_URL}/analyze  (field name: "image"):
// {
//   "quality":   { "score": 82, "status": "GOOD", "reasons": [], "checks": [] },   // optional
//   "diagnosis": { "predicted_class": "nv", "confidence": 0.91,
//                  "probabilities": { "akiec":0.01, "bcc":0.01, "bkl":0.03, "df":0.01, "mel":0.02, "nv":0.91, "vasc":0.01 } },
//   "triage":    { "decision": "AUTO_TRIAGE", "headline": "...", "summary": "...", "reasons": [] } // optional
// }
// Anything marked optional is filled in by this frontend if the backend leaves it out.

import { API_URL, IS_DEMO } from "../config";
import { LESION_CLASSES } from "../data/classes";
import { assessQuality } from "../utils/quality";
import { decideTriage } from "../utils/triage";

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

function seedFrom(text) {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function rng(seed) {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

// MOCK model: same file always gives the same answer, so demos are repeatable.
function mockDiagnosis(file) {
  const rand = rng(seedFrom(file.name + file.size));
  const prior = [0.033, 0.051, 0.11, 0.011, 0.111, 0.669, 0.014];
  const logits = prior.map((p) => Math.log(p) + (rand() - 0.5) * 2.4);
  if (rand() < 0.55) logits[Math.floor(rand() * 7)] += 2.6;
  const max = Math.max(...logits);
  const exps = logits.map((l) => Math.exp(l - max));
  const total = exps.reduce((a, b) => a + b, 0);
  const probabilities = {};
  let best = 0;
  LESION_CLASSES.forEach((c, i) => {
    probabilities[c.code] = exps[i] / total;
    if (exps[i] > exps[best]) best = i;
  });
  return {
    predicted_class: LESION_CLASSES[best].code,
    confidence: probabilities[LESION_CLASSES[best].code],
    probabilities,
  };
}

async function callBackend(file) {
  const body = new FormData();
  body.append("image", file);
  let res;
  try {
    res = await fetch(`${API_URL}/analyze`, { method: "POST", body });
  } catch {
    throw new Error("Could not reach the model server. Check that it is running and the URL in .env is correct.");
  }
  if (!res.ok) throw new Error(`The model server returned an error (${res.status}). Try again.`);
  return res.json();
}

/**
 * Runs the three agents one after another.
 * onStage("quality" | "diagnosis" | "triage") lets the UI show which agent is working.
 */
export async function runPipeline(file, onStage = () => {}) {
  if (IS_DEMO) {
    onStage("quality");
    const quality = await assessQuality(file);
    await wait(600);

    onStage("diagnosis");
    await wait(900);
    const diagnosis = mockDiagnosis(file);

    onStage("triage");
    await wait(500);
    const triage = decideTriage(quality, diagnosis);
    return { quality, diagnosis, triage, source: "demo" };
  }

  onStage("quality");
  const [clientQuality, remote] = await Promise.all([assessQuality(file), callBackend(file)]);
  const quality = remote.quality || clientQuality;
  await wait(300);

  onStage("diagnosis");
  await wait(300);
  const diagnosis = remote.diagnosis;
  if (!diagnosis) throw new Error("The model server did not send a diagnosis.");

  onStage("triage");
  await wait(300);
  const triage = remote.triage || decideTriage(quality, diagnosis);
  return { quality, diagnosis, triage, source: "live" };
}

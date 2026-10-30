// Triage Agent: reads the Quality Agent and the Diagnosis Agent, then makes the final decision.
// Rules are simple and written in plain words so a doctor (or a judge) can read them.
import { TRIAGE_RULES as R } from "../config";
import { CLASS_BY_CODE } from "../data/classes";

export function decideTriage(quality, diagnosis) {
  const top = CLASS_BY_CODE[diagnosis.predicted_class];
  const pct = (v) => `${Math.round(v * 100)}%`;
  const melProb = diagnosis.probabilities?.mel ?? 0;

  // Rule 1: a bad photo cannot be trusted, so ask for a new one.
  if (quality.status === "POOR" || quality.score < R.minQualityScore) {
    return {
      decision: "RE_IMAGE",
      headline: "Take a new photo",
      summary: "The photo quality is too low for a reliable result.",
      reasons: quality.reasons.length ? quality.reasons : ["Quality score is below the safe limit."],
    };
  }

  // Rule 2: cancerous or pre-cancerous lesions always go to a doctor.
  if (top.risk === "high") {
    return {
      decision: "REFER",
      headline: "Refer to a dermatologist",
      summary: `The most likely class is ${top.name}, which needs a specialist.`,
      reasons: [`${top.name} predicted with ${pct(diagnosis.confidence)} confidence.`, top.note],
    };
  }

  // Rule 3: even if the top class looks harmless, a noticeable melanoma chance is not ignored.
  if (melProb >= R.melWatch) {
    return {
      decision: "REFER",
      headline: "Refer to a dermatologist",
      summary: "The top class looks harmless, but melanoma is still a real possibility.",
      reasons: [`Melanoma probability is ${pct(melProb)} (limit ${pct(R.melWatch)}).`],
    };
  }

  // Rule 4: if the model is unsure, a human decides.
  if (diagnosis.confidence < R.minConfidence) {
    return {
      decision: "REFER",
      headline: "Refer to a dermatologist",
      summary: "The system is not confident enough to decide alone.",
      reasons: [`Confidence is ${pct(diagnosis.confidence)} (needs ${pct(R.minConfidence)}).`],
    };
  }

  return {
    decision: "AUTO_TRIAGE",
    headline: "Routine follow-up",
    summary: `Clear photo and a confident, low-risk result: ${top.name}.`,
    reasons: [`${top.name} predicted with ${pct(diagnosis.confidence)} confidence.`, "Photo quality passed every check."],
  };
}

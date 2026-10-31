import { TRIAGE_RULES as R } from "../config";
import { CLASS_BY_CODE } from "../data/classes";

export function coordinateDecision({ quality, diagnosis, lesionAnalysis, context, safety }) {
  const top = CLASS_BY_CODE[diagnosis.predicted_class];
  const reasons = [];
  let decision;
  if (quality.status === "POOR" || quality.score < R.minQualityScore) {
    decision = "RE_IMAGE";
    reasons.push("Image Quality Agent flagged the photo as inadequate.");
  } else if (safety.flag === "SAFETY_FLAG") {
    decision = "REFER";
    reasons.push(...(safety.conflicts.length ? safety.conflicts : context.riskIndicators));
  } else if (top?.risk === "high") {
    decision = "REFER";
    reasons.push(`${top.name} is a high-risk predicted class.`);
  } else if ((diagnosis.probabilities?.mel ?? 0) >= R.melWatch) {
    decision = "REFER";
    reasons.push(`Melanoma probability is ${Math.round(diagnosis.probabilities.mel * 100)}%, above the watch threshold.`);
  } else if (diagnosis.confidence < R.minConfidence) {
    decision = "REFER";
    reasons.push(`Diagnosis confidence (${Math.round(diagnosis.confidence * 100)}%) is below the threshold.`);
  } else if (lesionAnalysis.suspicionScore >= 25) {
    decision = "REFER";
    reasons.push(`Lesion Analysis Agent reported ${lesionAnalysis.suspicion} visual cues (score ${lesionAnalysis.suspicionScore}/100).`);
  } else {
    decision = "AUTO_TRIAGE";
    reasons.push(`Clear photo and confident, low-risk prediction: ${top?.name || diagnosis.predicted_class}.`);
  }
  if (decision === "REFER" && reasons.length === 0) reasons.push("Uncertainty warrants expert review.");
  const headline = decision === "AUTO_TRIAGE" ? "Routine follow-up" : decision === "RE_IMAGE" ? "Take a new photo" : "Refer to a dermatologist";
  const summary = decision === "AUTO_TRIAGE" ? "The available evidence passed the documented screening policy." : decision === "RE_IMAGE" ? "Image quality is inadequate; another photo is needed." : "Suspicion, uncertainty, or conflicting evidence warrants expert review.";
  return {
    predictedLabel: diagnosis.predicted_class,
    decision,
    headline,
    summary,
    reasons,
    rationale: `A6 reviewed A1 quality (${quality.status}, ${quality.score}/100), A2 diagnosis (${diagnosis.predicted_class}, ${Math.round(diagnosis.confidence * 100)}%), A3 visual suspicion (${lesionAnalysis.suspicionScore}/100), A4 context (${context.riskLevel}), and A5 safety (${safety.flag}). Policy: poor quality → RE_IMAGE; otherwise safety/conflict, high-risk label, melanoma watch probability, low confidence, or suspicious visual cues → REFER; otherwise AUTO_TRIAGE.`,
  };
}

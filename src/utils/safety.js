export function reviewSafety({ quality, diagnosis, lesionAnalysis, context }) {
  const conflicts = [];
  if (quality.status === "POOR") conflicts.push("Diagnosis and image-based cues are limited by poor image quality.");
  if (lesionAnalysis.suspicionScore >= 45 && diagnosis.confidence >= 0.6 && diagnosis.predicted_class !== "mel") {
    conflicts.push("Visual feature cues are suspicious while the diagnosis model's top class is not melanoma.");
  }
  if (diagnosis.confidence < 0.6) conflicts.push("Diagnosis confidence is below the minimum decision threshold.");
  if (lesionAnalysis.reliabilityFlags.length) conflicts.push(...lesionAnalysis.reliabilityFlags);
  const flag = conflicts.length > 0 || context.riskIndicators.length > 0;
  return {
    flag: flag ? "SAFETY_FLAG" : "CLEAR",
    veto: quality.status === "POOR",
    trigger: conflicts.length ? "Evidence conflict or reliability concern" : context.riskIndicators.length ? "Context risk indicator" : "No conflict trigger",
    conflicts,
    justification: flag ? "The coordinator must not auto-triage while safety concerns or contextual risk indicators remain." : "Available reports have no detected safety conflict under the current policy.",
  };
}

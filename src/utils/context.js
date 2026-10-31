export function assessContext(context = {}) {
  const age = context.age === "" || context.age == null ? null : Number(context.age);
  const gender = context.gender || "";
  const location = context.location || "";
  const missingFields = [];
  if (age == null || !Number.isFinite(age)) missingFields.push("Age not provided.");
  if (!gender) missingFields.push("Gender not provided.");
  if (!location) missingFields.push("Lesion location not provided.");
  const riskIndicators = [];
  if (age != null && age >= 60) riskIndicators.push("Age 60 or above is a contextual risk indicator.");
  if (location && /face|ear|scalp|neck|hand|arm/i.test(location)) riskIndicators.push("Sun-exposed location may increase concern.");
  return {
    evidence: [age == null ? "Age unavailable." : `Age provided: ${age}.`, gender ? `Gender provided: ${gender}.` : "Gender unavailable.", location ? `Lesion location: ${location}.` : "Lesion location unavailable."],
    riskIndicators,
    missingFields,
    riskLevel: riskIndicators.length ? "CONTEXT_FLAG" : "NO_ADDED_FLAG",
  };
}

// All the numbers that decide "good image / bad image" and "refer / auto-triage" live here.
// Change them in one place and the whole portal follows.

export const QUALITY_THRESHOLDS = {
  blurMin: 60,        // Laplacian variance below this = blurry
  darkMean: 55,       // average brightness below this = too dark
  brightMean: 205,    // average brightness above this = overexposed
  glareMax: 0.04,     // more than 4% near-white pixels = glare
  obstructionMax: 0.3 // more than 30% very dark pixels = vignette / frame / heavy obstruction
};

export const TRIAGE_RULES = {
  minConfidence: 0.6,   // below this the system will not decide alone
  melWatch: 0.25,       // melanoma probability at or above this always goes to a doctor
  minQualityScore: 60,  // below this score the photo is retaken
};

export const API_URL = import.meta.env.VITE_API_URL || "";
export const IS_DEMO = !API_URL;

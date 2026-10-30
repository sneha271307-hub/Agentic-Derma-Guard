// The seven HAM10000 lesion classes.
// risk: "high" lesions are cancerous or pre-cancerous, so they always go to a doctor.

export const LESION_CLASSES = [
  { code: "akiec", name: "Actinic keratosis", risk: "high", note: "Pre-cancerous scaly patch caused by sun damage." },
  { code: "bcc", name: "Basal cell carcinoma", risk: "high", note: "Most common skin cancer. Grows slowly but needs treatment." },
  { code: "bkl", name: "Benign keratosis", risk: "low", note: "Harmless growth such as a sun spot or seborrheic keratosis." },
  { code: "df", name: "Dermatofibroma", risk: "low", note: "Small, firm, harmless bump in the skin." },
  { code: "mel", name: "Melanoma", risk: "high", note: "Most dangerous skin cancer. Early detection saves lives." },
  { code: "nv", name: "Melanocytic nevus", risk: "low", note: "A common mole." },
  { code: "vasc", name: "Vascular lesion", risk: "low", note: "Blood-vessel marks such as angiomas." },
];

export const CLASS_BY_CODE = Object.fromEntries(LESION_CLASSES.map((c) => [c.code, c]));

// Lightweight visual cue extraction for the demo portal.
// These image heuristics are explainable signals, not a clinical lesion detector.
function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => { URL.revokeObjectURL(url); resolve(image); };
    image.onerror = () => { URL.revokeObjectURL(url); reject(new Error("Could not inspect lesion image cues.")); };
    image.src = url;
  });
}

export async function analyzeLesion(file, quality) {
  const image = await loadImage(file);
  const size = 96;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(image, 0, 0, size, size);
  const pixels = ctx.getImageData(0, 0, size, size).data;
  const mask = new Uint8Array(size * size);
  const luminance = new Float32Array(size * size);
  let inside = 0;
  let dark = 0;
  let red = 0;
  let bright = 0;
  for (let i = 0, j = 0; i < pixels.length; i += 4, j++) {
    const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2];
    const y = 0.299 * r + 0.587 * g + 0.114 * b;
    luminance[j] = y;
    // Broad pigment mask; background and skin tone vary widely, so this is deliberately flagged as approximate.
    const pigment = y < 145 && (Math.max(r, g, b) - Math.min(r, g, b) < 90);
    if (pigment) { mask[j] = 1; inside++; }
    if (pigment && y < 65) dark++;
    if (pigment && r > g * 1.12 && r > b * 1.08) red++;
    if (y > 220) bright++;
  }
  const area = inside / mask.length;
  let edge = 0, edgeTotal = 0;
  let colorMin = 255, colorMax = 0, colorSum = 0, count = 0;
  for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) {
    const i = y * size + x;
    if (mask[i]) {
      const yy = luminance[i]; colorMin = Math.min(colorMin, yy); colorMax = Math.max(colorMax, yy); colorSum += yy; count++;
      const neighbors = mask[i - 1] + mask[i + 1] + mask[i - size] + mask[i + size];
      if (neighbors < 4) edge++;
      edgeTotal++;
    }
  }
  let asymmetry = null;
  if (inside > 12) {
    let mismatch = 0;
    for (let y = 0; y < size; y++) for (let x = 0; x < size / 2; x++) {
      mismatch += mask[y * size + x] !== mask[y * size + (size - 1 - x)] ? 1 : 0;
    }
    asymmetry = mismatch / (size * size / 2);
  }
  const borderRatio = edgeTotal ? edge / edgeTotal : 0;
  const colorSpread = count ? colorMax - colorMin : 0;
  const cues = [
    { key: "asymmetry", label: "Asymmetry", value: asymmetry == null ? "Unavailable" : asymmetry > 0.22 ? "Elevated" : "Low", detail: asymmetry == null ? "A lesion region was not isolated reliably." : `Mirror mismatch estimate: ${Math.round(asymmetry * 100)}%.`, concern: asymmetry != null && asymmetry > 0.22 },
    { key: "border", label: "Border variation", value: borderRatio > 0.28 ? "Elevated" : "Low", detail: `Boundary complexity estimate: ${Math.round(borderRatio * 100)}%.`, concern: borderRatio > 0.28 },
    { key: "color", label: "Color variation", value: colorSpread > 90 ? "Elevated" : "Low", detail: `Pigment luminance spread estimate: ${Math.round(colorSpread)} levels.`, concern: colorSpread > 90 },
  ];
  const concernCount = cues.filter((cue) => cue.concern).length;
  const score = Math.min(100, Math.round(concernCount * 28 + (dark / Math.max(inside, 1) > 0.25 ? 10 : 0) + (red / Math.max(inside, 1) > 0.2 ? 8 : 0)));
  const reliabilityFlags = [];
  if (quality.status === "POOR") reliabilityFlags.push("Image quality is poor; visual cues may be unreliable.");
  if (area < 0.01 || area > 0.65) reliabilityFlags.push("The lesion region could not be separated confidently from surrounding skin.");
  if (bright / mask.length > 0.2) reliabilityFlags.push("Bright regions may obscure lesion boundaries or color cues.");
  return {
    cues,
    featureEvidence: cues.map(({ label, value, detail }) => ({ label, value, detail })),
    suspicionScore: score,
    suspicion: score >= 45 ? "SUSPICIOUS" : score >= 25 ? "WATCH" : "LOW_CUE_BURDEN",
    reliabilityFlags,
    method: "Approximate image-pixel heuristics",
  };
}

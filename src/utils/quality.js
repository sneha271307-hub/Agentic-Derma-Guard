// Image Quality Agent (runs fully in the browser, no backend needed).
// It looks at the pixels of the photo and checks four things: blur, lighting, glare, obstruction.
import { QUALITY_THRESHOLDS as T } from "../config";

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => resolve({ img, url });
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("This file could not be read as an image. Choose a JPG or PNG."));
    };
    img.src = url;
  });
}

const clamp = (v, lo = 0, hi = 100) => Math.max(lo, Math.min(hi, v));

export async function assessQuality(file) {
  const { img, url } = await loadImage(file);
  const maxSide = 256; // small copy is enough and keeps it fast
  const scale = maxSide / Math.max(img.naturalWidth, img.naturalHeight);
  const w = Math.max(8, Math.round(img.naturalWidth * scale));
  const h = Math.max(8, Math.round(img.naturalHeight * scale));

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, w, h);
  URL.revokeObjectURL(url);
  const { data } = ctx.getImageData(0, 0, w, h);

  const gray = new Float32Array(w * h);
  let sum = 0;
  let glare = 0;
  let dark = 0;
  for (let i = 0, p = 0; i < data.length; i += 4, p++) {
    const r = data[i], g = data[i + 1], b = data[i + 2];
    const y = 0.299 * r + 0.587 * g + 0.114 * b;
    gray[p] = y;
    sum += y;
    if (r > 240 && g > 240 && b > 240) glare++;
    if (y < 30) dark++;
  }
  const n = w * h;
  const mean = sum / n;
  const glareFrac = glare / n;
  const darkFrac = dark / n;

  // Blur: variance of the Laplacian. Sharp edges give a high number, blur gives a low one.
  let s = 0, s2 = 0, count = 0;
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = y * w + x;
      const v = 4 * gray[i] - gray[i - 1] - gray[i + 1] - gray[i - w] - gray[i + w];
      s += v;
      s2 += v * v;
      count++;
    }
  }
  const lapMean = s / count;
  const lapVar = s2 / count - lapMean * lapMean;

  const blurPass = lapVar >= T.blurMin;
  const lightPass = mean >= T.darkMean && mean <= T.brightMean;
  const glarePass = glareFrac <= T.glareMax;
  const obstrPass = darkFrac <= T.obstructionMax;

  const blurScore = clamp((lapVar / (T.blurMin * 2.5)) * 100);
  const lightScore = clamp(100 - (Math.abs(mean - 130) / 130) * 100);
  const glareScore = clamp(100 - (glareFrac / (T.glareMax * 3)) * 100);
  const obstrScore = clamp(100 - (darkFrac / (T.obstructionMax * 2)) * 100);

  const score = Math.round(0.4 * blurScore + 0.2 * lightScore + 0.2 * glareScore + 0.2 * obstrScore);

  const checks = [
    {
      key: "blur",
      label: "Sharpness",
      pass: blurPass,
      value: `${Math.round(lapVar)} (needs ${T.blurMin}+)`,
      detail: blurPass ? "Edges are crisp." : "The photo is blurry. Hold steady and refocus.",
    },
    {
      key: "light",
      label: "Lighting",
      pass: lightPass,
      value: `${Math.round(mean)} of 255`,
      detail: lightPass ? "Even brightness." : mean < T.darkMean ? "The photo is too dark." : "The photo is overexposed.",
    },
    {
      key: "glare",
      label: "Glare",
      pass: glarePass,
      value: `${(glareFrac * 100).toFixed(1)}% bright spots`,
      detail: glarePass ? "No reflections on the skin." : "Reflections hide detail. Tilt the camera or use polarized light.",
    },
    {
      key: "obstruction",
      label: "Obstruction",
      pass: obstrPass,
      value: `${(darkFrac * 100).toFixed(1)}% blocked`,
      detail: obstrPass ? "The lesion is clearly visible." : "Dark frame, hair or objects cover too much of the lesion.",
    },
  ];

  const reasons = checks.filter((c) => !c.pass).map((c) => c.detail);
  const status = reasons.length === 0 && score >= 60 ? "GOOD" : "POOR";
  if (status === "POOR" && reasons.length === 0) reasons.push("Overall image quality score is too low.");

  return { score, status, reasons, checks };
}

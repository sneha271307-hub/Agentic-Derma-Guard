# DermaGuard Portal

Frontend for **Agentic DermaGuard** (Jaypee Agentic AI International Summit 2026, Track 2 Healthcare).
React + Vite. Three pages: Screen a photo, Batch results, How the agents work.

## Run it

```bash
npm install
npm run dev
```

Open the link shown in the terminal (usually http://localhost:5173).

## Two modes

| Mode | How | What happens |
|---|---|---|
| **Demo** (default) | leave `VITE_API_URL` empty | Image quality is measured for real in your browser. Diagnosis is simulated, so the UI can be shown before the model is ready. |
| **Live** | copy `.env.example` to `.env` and set `VITE_API_URL=http://your-backend` | The photo is sent to `POST {VITE_API_URL}/analyze` (form field `image`). |

Expected backend reply (quality and triage are optional, the frontend fills them in if missing):

```json
{
  "quality":   { "score": 82, "status": "GOOD", "reasons": [], "checks": [] },
  "diagnosis": { "predicted_class": "nv", "confidence": 0.91,
                 "probabilities": { "akiec": 0.01, "bcc": 0.01, "bkl": 0.03, "df": 0.01, "mel": 0.02, "nv": 0.91, "vasc": 0.01 } },
  "triage":    { "decision": "AUTO_TRIAGE", "headline": "Routine follow-up", "summary": "...", "reasons": ["..."] }
}
```

Class codes: `akiec, bcc, bkl, df, mel, nv, vasc`.
If the backend is on another port, ask the backend teammate to enable CORS.

## Loading real batch results

On the Batch results page, click **Load results (JSON)** and choose a file shaped like this:

```json
[
  { "id": "ISIC_0024306", "true_label": "nv", "predicted_class": "nv", "confidence": 0.93,
    "quality_score": 88, "quality_status": "GOOD", "quality_reason": "", "decision": "AUTO_TRIAGE" }
]
```

Only `id` and `predicted_class` are required.

## Folder map

```
src/
  config.js            thresholds for quality and triage rules (edit numbers here)
  api/dermaguard.js    the only file that talks to the models (demo or live)
  utils/quality.js     Image Quality Agent (blur, lighting, glare, obstruction)
  utils/triage.js      Triage Agent (the decision rules)
  data/classes.js      the 7 lesion classes and their risk level
  data/sampleBatch.js  sample data for the Batch page
  components/          Header, DermoLens, Pipeline, QualityCard, DiagnosisCard, TriageBanner
  pages/               ScreenPage, BatchPage, AgentsPage
  index.css            all colors, fonts and layout
```

## Build for deployment

```bash
npm run build
```

The `dist/` folder can be hosted on Netlify, Vercel or GitHub Pages.

> Research prototype for a hackathon. Not a medical device.

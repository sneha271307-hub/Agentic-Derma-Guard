const STEPS = [
  { id: "quality", name: "Image Quality Agent", does: "Checks the photo" },
  { id: "diagnosis", name: "Diagnosis Agent", does: "Predicts the lesion" },
  { id: "lesion", name: "Lesion Analysis Agent", does: "Checks visual cues" },
  { id: "context", name: "Reasoning / Context Agent", does: "Reviews provided context" },
  { id: "safety", name: "Safety Agent", does: "Checks conflicts" },
  { id: "coordinator", name: "Coordinator Agent", does: "Records the decision" },
];

// stage: "idle" | the six agent ids | "done"
export default function Pipeline({ stage }) {
  const order = STEPS.map((step) => step.id);
  const activeIndex = stage === "done" ? STEPS.length : order.indexOf(stage);

  return (
    <ol className="pipe" aria-label="Agent progress">
      {STEPS.map((s, i) => {
        const state = activeIndex > i ? "done" : activeIndex === i ? "active" : "wait";
        return (
          <li key={s.id} className={"pipe__step pipe__step--" + state}>
            <span className="pipe__dot" aria-hidden="true">
              {state === "done" ? (
                <svg width="14" height="14" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" /></svg>
              ) : (
                i + 1
              )}
            </span>
            <span className="pipe__text">
              <span className="pipe__name">{s.name}</span>
              <span className="pipe__does">
                {state === "active" ? "Working now" : state === "done" ? "Finished" : s.does}
              </span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}

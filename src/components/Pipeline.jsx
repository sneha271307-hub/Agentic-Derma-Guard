const STEPS = [
  { id: "quality", name: "Image Quality Agent", does: "Checks the photo" },
  { id: "diagnosis", name: "Diagnosis Agent", does: "Predicts the lesion" },
  { id: "triage", name: "Triage Agent", does: "Makes the decision" },
];

// stage: "idle" | "quality" | "diagnosis" | "triage" | "done"
export default function Pipeline({ stage }) {
  const order = ["quality", "diagnosis", "triage"];
  const activeIndex = stage === "done" ? 3 : order.indexOf(stage);

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

import { Check } from "lucide-react";

const steps = ["文稿", "主持人", "音效", "輸出"];

type StepNavProps = {
  current: number;
  onSelect: (step: number) => void;
};

export function StepNav({ current, onSelect }: StepNavProps) {
  return (
    <nav className="step-nav" aria-label="Studio steps">
      {steps.map((label, index) => {
        const step = index + 1;
        const completed = step < current;
        return (
          <button
            className={`step-button ${step === current ? "active" : ""} ${completed ? "complete" : ""}`}
            key={label}
            onClick={() => onSelect(step)}
            type="button"
          >
            <span className="step-index">{completed ? <Check size={16} /> : step}</span>
            <span>{label}</span>
          </button>
        );
      })}
    </nav>
  );
}

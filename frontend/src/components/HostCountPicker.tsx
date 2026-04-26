import { UsersRound } from "lucide-react";

type HostCountPickerProps = {
  value: number;
  onChange: (count: number) => void;
};

export function HostCountPicker({ value, onChange }: HostCountPickerProps) {
  return (
    <div className="host-count">
      <div className="host-count-title">
        <UsersRound size={20} />
        <h3>主持人人數</h3>
      </div>
      <div className="segmented" role="group" aria-label="Host count">
        {[1, 2, 3, 4].map((count) => (
          <button
            className={value === count ? "selected" : ""}
            key={count}
            onClick={() => onChange(count)}
            type="button"
          >
            {count}
          </button>
        ))}
      </div>
    </div>
  );
}

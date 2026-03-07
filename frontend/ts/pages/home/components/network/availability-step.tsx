"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

export interface AvailabilityStep {
  value: number;
  label: string;
}

export interface AvailabilitySliderProps {
  value?: number;
  onChange?: (value: number) => void;
  steps?: AvailabilityStep[];
}

const defaultSteps: AvailabilityStep[] = [
  { value: 0, label: "Indisponible" },
  { value: 25, label: "Faible" },
  { value: 50, label: "Modérée" },
  { value: 75, label: "Disponible" },
  { value: 100, label: "Très disponible" },
];

export function AvailabilitySlider({
  value = 50,
  onChange,
  steps = defaultSteps,
}: AvailabilitySliderProps) {
  const [internalValue, setInternalValue] = useState(value);

  const current = onChange ? value : internalValue;

  const setValue = (v: number) => {
    if (onChange) onChange(v);
    else setInternalValue(v);
  };

  return (
    <div className="w-full bg-card rounded-lg p-4">
      <div className="relative flex items-center justify-between">
        {/* Ligne */}
        <div className="absolute left-0 right-0 top-2 h-px bg-border" />

        {steps.map((step) => {
          const isActive = step.value <= current;
          const isCurrent = step.value === current;

          return (
            <button
              key={step.value}
              type="button"
              onClick={() => setValue(step.value)}
              className="relative flex flex-col items-center gap-1"
            >
              <div
                className={cn(
                  "h-4 w-4 rounded-full border transition",
                  isActive && "bg-primary border-primary",
                  !isActive && "bg-background border-muted-foreground/40",
                  isCurrent && "scale-110",
                )}
              />

              <span
                className={cn(
                  "text-xs whitespace-nowrap",
                  isCurrent && "font-medium",
                  !isActive && "text-muted-foreground",
                )}
              >
                {step.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

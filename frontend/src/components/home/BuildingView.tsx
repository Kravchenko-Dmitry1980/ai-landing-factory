import { fileSizeLabel } from "@/lib/staff";

export type StepState = "done" | "active" | "pending";

export interface BuildStep {
  label: string;
  state: StepState;
}

interface Props {
  files: Pick<File, "name" | "size">[];
  steps: BuildStep[];
}

/** The one orchestrated motion moment: the cat assembles the page while real requests run. */
export function BuildingView({ files, steps }: Props) {
  return (
    <section
      aria-live="polite"
      className="grid items-center gap-6 overflow-hidden rounded-3xl border border-line bg-white bg-grid-paper bg-cell px-8 py-10 md:grid-cols-[minmax(0,360px)_minmax(0,1fr)] md:px-14"
    >
      <div className="relative mx-auto w-full max-w-[340px]">
        <div
          aria-hidden="true"
          className="absolute left-[46%] top-[58%] -ml-20 -mt-20 h-40 w-40 rounded-full bg-glow opacity-25 motion-safe:animate-glow-pulse"
        />
        {/* eslint-disable-next-line @next/next/no-img-element -- статичная иллюстрация */}
        <img src="/brand/cat-hero.webp" alt="Котик собирает страницу" width={340} height={340} className="relative h-auto w-full" />
      </div>

      <div className="flex flex-col gap-7">
        <div className="flex flex-col gap-2">
          <h1 className="font-display text-[34px] font-semibold leading-tight tracking-tight">Собираю страницу</h1>
          <p className="text-base text-fur">
            {files.map((f) => `${f.name}, ${fileSizeLabel(f.size)}`).join("; ")}
          </p>
        </div>

        <ol className="flex flex-col">
          {steps.map((step, i) => (
            <li key={step.label} className="grid grid-cols-[28px_minmax(0,1fr)] gap-3.5">
              <div className="flex flex-col items-center">
                <StepDot state={step.state} />
                {i < steps.length - 1 && (
                  <div
                    className={`min-h-[26px] w-0.5 flex-1 ${
                      step.state === "done" ? "bg-scheme" : "bg-grid"
                    }`}
                  />
                )}
              </div>
              <div
                className={`pb-[18px] pt-px text-[17px] ${
                  step.state === "active" ? "font-semibold" : step.state === "pending" ? "text-fur" : ""
                }`}
              >
                {step.label}
                {step.state === "active" ? "…" : ""}
              </div>
            </li>
          ))}
        </ol>

        <p className="text-[15px] text-fur">Обычно это занимает несколько секунд. Потом откроется редактор.</p>
      </div>
    </section>
  );
}

function StepDot({ state }: { state: StepState }) {
  if (state === "done") {
    return (
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-scheme">
        <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 12l5 5 9-10" />
        </svg>
        <span className="sr-only">Готово:</span>
      </span>
    );
  }
  if (state === "active") {
    return (
      <span className="h-6 w-6 rounded-full border-2 border-glow bg-white shadow-[0_0_10px_#3FDCFF]">
        <span className="sr-only">Сейчас:</span>
      </span>
    );
  }
  return <span className="h-6 w-6 rounded-full border-2 border-grid bg-white" />;
}

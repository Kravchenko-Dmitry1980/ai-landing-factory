import type { FidelityDiagnostics } from "@/rendering/types";

interface Props {
  diagnostics: FidelityDiagnostics;
}

export function FidelityDebugPanel({ diagnostics }: Props) {
  const rows: [string, string | number][] = [
    ["modules source", diagnostics.modulesSource],
    ["team source", diagnostics.teamSource],
    ["stack source", diagnostics.stackSource],
    ["modules_count", diagnostics.modulesCount],
    ["team_count", diagnostics.teamCount],
    ["stack_categories_count", diagnostics.stackCategoriesCount],
  ];

  return (
    <aside className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
      <p className="font-semibold">Fidelity debug</p>
      <dl className="mt-2 grid gap-1 sm:grid-cols-2">
        {rows.map(([label, value]) => (
          <div key={label} className="flex gap-2">
            <dt className="text-amber-800">{label}:</dt>
            <dd className="font-mono">{value}</dd>
          </div>
        ))}
      </dl>
    </aside>
  );
}

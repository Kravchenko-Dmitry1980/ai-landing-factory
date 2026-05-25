interface Props {
  missing: string[];
  assumptions: string[];
  warnings: string[];
}

export function AssumptionWarnings({ missing, assumptions, warnings }: Props) {
  if (!missing.length && !assumptions.length && !warnings.length) return null;
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm">
      <h3 className="mb-2 font-semibold text-amber-900">Assumptions & gaps</h3>
      {missing.length > 0 && (
        <p>
          <span className="font-medium">Missing:</span> {missing.join(", ")}
        </p>
      )}
      {assumptions.length > 0 && (
        <p className="mt-1">
          <span className="font-medium">Assumptions:</span> {assumptions.join("; ")}
        </p>
      )}
      {warnings.length > 0 && (
        <ul className="mt-2 list-disc pl-5 text-red-800">
          {warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

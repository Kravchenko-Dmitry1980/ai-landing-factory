import type { PIIRiskLevel } from "@/lib/types";

const RISK_STYLES: Record<PIIRiskLevel, string> = {
  low: "bg-emerald-100 text-emerald-900 border-emerald-200",
  medium: "bg-amber-100 text-amber-900 border-amber-200",
  high: "bg-orange-100 text-orange-900 border-orange-200",
  critical: "bg-red-100 text-red-900 border-red-200",
  unknown: "bg-slate-100 text-slate-700 border-slate-200",
};

interface Props {
  riskLevel: PIIRiskLevel;
  hasPii: boolean;
}

export function PiiRiskBadge({ riskLevel, hasPii }: Props) {
  if (!hasPii) {
    return (
      <span className="inline-flex items-center rounded-md border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-800">
        PII не обнаружено
      </span>
    );
  }
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium uppercase ${RISK_STYLES[riskLevel]}`}
    >
      PII · {riskLevel}
    </span>
  );
}

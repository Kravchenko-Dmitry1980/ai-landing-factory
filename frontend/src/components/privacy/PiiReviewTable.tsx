import type { PIIReportPublic } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  report: PIIReportPublic | null;
  loading?: boolean;
}

const TYPE_LABELS: Record<string, string> = {
  person_name: "ФИО",
  email: "Email",
  phone: "Телефон",
  address: "Адрес",
  url: "URL",
  organization: "Организация",
  medical_data: "Мед. данные",
  passport_id: "Документ",
  telegram: "Telegram",
  role_person: "Роль + персона",
};

export function PiiReviewTable({ report, loading }: Props) {
  if (loading) {
    return <p className="text-sm text-muted-foreground">Сканирование PII…</p>;
  }
  if (!report) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          PII review · риск {report.risk_level} · режим {report.privacy_mode}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!report.has_pii ? (
          <p className="text-sm text-muted-foreground">Персональные данные не обнаружены.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="py-2 pr-4">Тип</th>
                  <th className="py-2 pr-4">Placeholder</th>
                  <th className="py-2 pr-4">Файл</th>
                  <th className="py-2">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {report.entities.map((e) => (
                  <tr key={`${e.placeholder}-${e.type}`} className="border-b border-muted/40">
                    <td className="py-2 pr-4">{TYPE_LABELS[e.type] ?? e.type}</td>
                    <td className="py-2 pr-4 font-mono text-xs">{e.placeholder}</td>
                    <td className="py-2 pr-4">{e.source_file ?? "—"}</td>
                    <td className="py-2">{e.confidence.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-3 text-xs text-muted-foreground">
              Оригинальные значения не отображаются (только server-side mapping).
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

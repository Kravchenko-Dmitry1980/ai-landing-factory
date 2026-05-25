import type { PIIEntityPublic, PIIEntityType } from "@/lib/types";

const TYPE_LABELS: Record<PIIEntityType, string> = {
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

interface Props {
  entities: PIIEntityPublic[];
}

export function PiiEntityGroups({ entities }: Props) {
  if (!entities.length) {
    return <p className="text-sm text-muted-foreground">Сущности не найдены.</p>;
  }

  const grouped = entities.reduce<Record<string, PIIEntityPublic[]>>((acc, e) => {
    acc[e.type] = acc[e.type] ?? [];
    acc[e.type].push(e);
    return acc;
  }, {});

  return (
    <div className="space-y-3">
      {Object.entries(grouped).map(([type, items]) => (
        <div key={type}>
          <p className="text-xs font-medium uppercase text-muted-foreground">
            {TYPE_LABELS[type as PIIEntityType] ?? type} ({items.length})
          </p>
          <ul className="mt-1 space-y-1 text-sm">
            {items.map((e) => (
              <li key={`${e.placeholder}-${e.detector}`} className="font-mono text-xs">
                {e.placeholder}
                <span className="ml-2 font-sans text-muted-foreground">
                  {e.detector} · {e.confidence.toFixed(2)}
                  {e.source_file ? ` · ${e.source_file}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

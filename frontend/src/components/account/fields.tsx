import { useId, type InputHTMLAttributes } from "react";

/** Поле формы с подписью и подсказкой под ним. */
export function Field({
  label,
  hint,
  ...input
}: { label: string; hint?: string } & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-[15px] font-semibold">
        {label}
      </label>
      <input
        id={id}
        aria-describedby={hint ? `${id}-hint` : undefined}
        className="h-11 rounded-[10px] border border-field bg-white px-3 text-base focus:border-scheme focus:outline-none focus:ring-2 focus:ring-scheme/25"
        {...input}
      />
      {hint && (
        <p id={`${id}-hint`} className="text-sm text-fur">
          {hint}
        </p>
      )}
    </div>
  );
}

export function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p role="alert" className="rounded-[10px] bg-marker px-4 py-3 text-[15px] text-ink">
      {message}
    </p>
  );
}

export const PRIMARY_BUTTON =
  "h-11 rounded-[10px] bg-scheme px-5 text-[15px] font-semibold text-white hover:bg-scheme-hover disabled:opacity-60";

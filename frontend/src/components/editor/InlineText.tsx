"use client";

import { useLayoutEffect, useRef } from "react";

interface Props {
  id?: string;
  value: string;
  label: string;
  placeholder?: string;
  className?: string;
  onChange: (value: string) => void;
  onKeyDown?: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
}

/** Text that looks like the page and edits in place: an auto-growing textarea without chrome. */
export function InlineText({ id, value, label, placeholder, className = "", onChange, onKeyDown }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const fit = () => {
      el.style.height = "0px";
      el.style.height = `${el.scrollHeight}px`;
    };
    fit();
    // Refit only when the width changes: reacting to our own height change would loop.
    let width = el.clientWidth;
    const observer = new ResizeObserver(() => {
      if (el.clientWidth === width) return;
      width = el.clientWidth;
      fit();
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [value]);

  return (
    <textarea
      ref={ref}
      id={id}
      aria-label={label}
      rows={1}
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={onKeyDown}
      className={`-mx-1.5 block w-[calc(100%+12px)] resize-none overflow-hidden rounded-md bg-transparent px-1.5 text-inherit outline-none placeholder:text-fur/80 hover:bg-scheme-soft focus:bg-white focus:shadow-[0_0_0_2px_#1E5FD8] ${className}`}
    />
  );
}

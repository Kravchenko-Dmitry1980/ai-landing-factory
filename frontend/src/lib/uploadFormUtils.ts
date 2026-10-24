/** Pure helpers for multi-file upload form (unit-testable). */

export function mergeFileSelection(current: File[], incoming: FileList | null): File[] {
  if (!incoming?.length) {
    return current;
  }
  const next = [...current];
  const seen = new Set(current.map((f) => `${f.name}:${f.size}:${f.lastModified}`));
  for (const file of Array.from(incoming)) {
    const key = `${file.name}:${file.size}:${file.lastModified}`;
    if (!seen.has(key)) {
      seen.add(key);
      next.push(file);
    }
  }
  return next;
}

export function removeFileAt(files: File[], index: number): File[] {
  if (index < 0 || index >= files.length) {
    return files;
  }
  return files.filter((_, i) => i !== index);
}

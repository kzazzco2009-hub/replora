const UNITS = ["B", "KB", "MB", "GB"] as const;

/** Western digits always (design.md §6: data-integrity numbers), so plain English units are fine too. */
export function formatBytes(bytes: number): string {
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < UNITS.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  const digits = unitIndex === 0 ? 0 : 1;
  return `${value.toFixed(digits)} ${UNITS[unitIndex]}`;
}

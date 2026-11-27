export const operationIds = [
  "extract_member",
  "parse_csv",
  "parse_json",
  "normalize",
  "map_columns",
  "compare",
  "report_csv",
  "summary_json",
  "bundle_zip",
  "append_rows",
  "export_csv",
] as const;

export function operationTitleKey(id: string) {
  const knownId = operationIds.find((operationId) => operationId === id);
  return knownId ? `operations.${knownId}.title` : undefined;
}

import { useId, type ReactNode } from "react";

export interface TableColumn<K extends string = string> {
  key: K;
  header: string;
  align?: "start" | "end";
  /** Numeric cells get dir="ltr" so digits read right-aligned on RTL pages too. */
  numeric?: boolean;
  /** Renders this column's cell as <th scope="row"> instead of <td>. */
  rowHeader?: boolean;
}

export interface TableRowData<K extends string = string> {
  id: string;
  cells: Record<K, ReactNode>;
}

export interface TableProps<K extends string = string> {
  caption: string;
  columns: TableColumn<K>[];
  rows: TableRowData<K>[];
  /** Shown instead of rows when there are none and `loading` is unset. */
  emptyState?: ReactNode;
  /** Shown instead of rows while loading; the table gets aria-busy. */
  loading?: ReactNode;
  dir?: "ltr" | "rtl";
}

const ALIGN_CLASS: Record<"start" | "end", string> = {
  start: "text-start",
  end: "text-end",
};

function columnAlign(column: TableColumn): "start" | "end" {
  return column.align ?? (column.numeric ? "end" : "start");
}

/**
 * Presentational only: cells, the empty state and the loading state are
 * all caller-supplied nodes, so this never depends on StatusChip, Skeleton
 * or EmptyState. design.md §4: horizontal scroll stays inside this
 * container, never the page.
 */
export function Table<K extends string = string>({
  caption,
  columns,
  rows,
  emptyState,
  loading,
  dir,
}: TableProps<K>) {
  const captionId = useId();

  return (
    <div
      role="region"
      aria-labelledby={captionId}
      tabIndex={0}
      dir={dir}
      className="overflow-x-auto rounded-control border border-line"
    >
      <table
        aria-busy={loading ? true : undefined}
        className="w-full border-collapse text-sm"
      >
        <caption
          id={captionId}
          className="px-3 py-2 text-start text-sm font-medium text-ink"
        >
          {caption}
        </caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={`border-b border-line px-3 py-2 font-medium text-ink-muted ${ALIGN_CLASS[columnAlign(column)]}`}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="p-3">
                {loading}
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="p-3">
                {emptyState}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                {columns.map((column) => {
                  const className = `border-b border-line px-3 py-2 ${ALIGN_CLASS[columnAlign(column)]}`;
                  const content = row.cells[column.key];
                  return column.rowHeader ? (
                    <th key={column.key} scope="row" className={className}>
                      {content}
                    </th>
                  ) : (
                    <td
                      key={column.key}
                      dir={column.numeric ? "ltr" : undefined}
                      className={className}
                    >
                      {content}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

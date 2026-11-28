import { useId, type MouseEvent, type ReactNode } from "react";

export interface TableColumn<K extends string = string> {
  key: K;
  header: ReactNode;
  align?: "start" | "end";
  /**
   * Numeric cells keep the table's own direction (so `text-end` resolves the
   * same way for the header and the cell); only the digits are isolated in a
   * `dir="ltr"` span, so they still read left-to-right on RTL pages.
   */
  numeric?: boolean;
  /** Renders this column's cell as <th scope="row"> instead of <td>. */
  rowHeader?: boolean;
}

export interface TableRowData<K extends string = string> {
  id: string;
  cells: Record<K, ReactNode>;
  onClick?: (event: MouseEvent<HTMLTableRowElement>) => void;
}

export interface TableProps<K extends string = string> {
  caption: string;
  hideCaption?: boolean;
  columns: TableColumn<K>[];
  rows: TableRowData<K>[];
  /** Shown instead of rows when there are none and `loading` is unset. */
  emptyState?: ReactNode;
  /** Shown instead of rows while loading; the table gets aria-busy. */
  loading?: ReactNode;
  dir?: "ltr" | "rtl";
  sticky?: boolean;
}

const ALIGN_CLASS: Record<"start" | "end", string> = {
  start: "text-start",
  end: "text-end",
};

function columnAlign(column: TableColumn): "start" | "end" {
  return column.align ?? (column.numeric ? "end" : "start");
}

function cellContent(column: TableColumn, content: ReactNode): ReactNode {
  return column.numeric ? <span dir="ltr">{content}</span> : content;
}

/**
 * Presentational only: cells, the empty state and the loading state are
 * all caller-supplied nodes, so this never depends on StatusChip, Skeleton
 * or EmptyState. design.md §4: horizontal scroll stays inside this
 * container, never the page.
 */
export function Table<K extends string = string>({
  caption,
  hideCaption = false,
  columns,
  rows,
  emptyState,
  loading,
  dir,
  sticky = false,
}: TableProps<K>) {
  const captionId = useId();

  return (
    <div
      role="region"
      aria-labelledby={captionId}
      tabIndex={0}
      dir={dir}
      className={`overflow-x-auto rounded-control border border-line ${sticky ? "max-h-96" : ""}`}
    >
      <table
        aria-busy={loading ? true : undefined}
        className="w-full border-collapse text-sm"
      >
        <caption
          id={captionId}
          className={
            hideCaption
              ? "sr-only"
              : "px-3 py-2 text-start text-sm font-medium text-ink"
          }
        >
          {caption}
        </caption>
        <thead>
          <tr>
            {columns.map((column, index) => (
              <th
                key={column.key}
                scope="col"
                className={`border-b border-line px-3 py-2 font-medium text-ink-muted ${ALIGN_CLASS[columnAlign(column)]} ${sticky ? `sticky top-0 bg-surface whitespace-nowrap ${index === 0 ? "start-0 z-20" : "z-10"}` : ""}`}
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
              <tr key={row.id} onClick={row.onClick}>
                {columns.map((column, index) => {
                  const className = `border-b border-line px-3 py-2 ${ALIGN_CLASS[columnAlign(column)]} ${sticky && index === 0 ? "sticky start-0 z-10 bg-surface" : ""}`;
                  const content = row.cells[column.key];
                  return column.rowHeader ? (
                    <th key={column.key} scope="row" className={className}>
                      {cellContent(column, content)}
                    </th>
                  ) : (
                    <td key={column.key} className={className}>
                      {cellContent(column, content)}
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

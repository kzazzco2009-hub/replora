import type { ReactNode } from "react";

/** Consistent heading and spacing for every pre-login screen (design.md §5). */
export function AuthCard({
  heading,
  children,
}: {
  heading: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-ink">{heading}</h1>
      {children}
    </div>
  );
}

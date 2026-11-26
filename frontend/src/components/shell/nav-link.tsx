import Link from "next/link";
import type { NavIcon } from "./nav-items";

export interface NavLinkProps {
  href: string;
  label: string;
  icon: NavIcon;
  active: boolean;
  /** Hides the visible label (sr-only); an aria-label carries the name instead. */
  iconOnly?: boolean;
}

export function NavLink({
  href,
  label,
  icon: Icon,
  active,
  iconOnly,
}: NavLinkProps) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      aria-label={iconOnly ? label : undefined}
      className={`flex min-h-11 min-w-11 items-center gap-2 rounded-control px-3 text-start text-sm outline-offset-2 focus-visible:outline-2 focus-visible:outline-focus-ring ${
        active ? "font-semibold text-petrol" : "text-ink-muted"
      }`}
    >
      <Icon aria-hidden="true" className="size-5 shrink-0" />
      <span className={iconOnly ? "sr-only" : undefined}>{label}</span>
    </Link>
  );
}

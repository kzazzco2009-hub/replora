import { BOTTOM_TAB_PRIMARY_IDS, MoreIcon } from "./nav-items";
import { NavLink } from "./nav-link";
import type { ShellNavItem } from "./side-nav";

interface BottomTabBarProps {
  items: ShellNavItem[];
  navLabel: string;
  moreLabel: string;
}

/** Phone (design.md §4: < 640 px): Home, New run, Runs, Files, then a
 * native <details> disclosure holding the rest (Workflows, Settings). */
export function BottomTabBar({
  items,
  navLabel,
  moreLabel,
}: BottomTabBarProps) {
  const primary = items.filter((item) =>
    BOTTOM_TAB_PRIMARY_IDS.includes(item.id),
  );
  const overflow = items.filter(
    (item) => !BOTTOM_TAB_PRIMARY_IDS.includes(item.id),
  );

  return (
    <nav
      aria-label={navLabel}
      className="fixed inset-x-0 bottom-0 flex items-center justify-around border-t border-line bg-surface sm:hidden"
    >
      {primary.map((item) => (
        <NavLink key={item.id} {...item} iconOnly />
      ))}
      <details className="relative flex min-h-11 min-w-11 items-center justify-center">
        <summary className="flex min-h-11 min-w-11 list-none items-center justify-center [&::-webkit-details-marker]:hidden [&::marker]:hidden">
          <MoreIcon aria-hidden="true" className="size-5" />
          <span className="sr-only">{moreLabel}</span>
        </summary>
        <ul className="absolute bottom-full end-0 mb-2 min-w-36 rounded-panel border border-line bg-surface-raised p-1 shadow-lg">
          {overflow.map((item) => (
            <li key={item.id}>
              <NavLink {...item} />
            </li>
          ))}
        </ul>
      </details>
    </nav>
  );
}

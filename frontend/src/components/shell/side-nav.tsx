import { NavLink, type NavLinkProps } from "./nav-link";

export interface ShellNavItem extends Omit<NavLinkProps, "iconOnly"> {
  id: string;
}

interface SideNavProps {
  items: ShellNavItem[];
  navLabel: string;
}

/** Laptop and wide (design.md §4: >= 1024 px), full sidebar with labels. */
export function Sidebar({ items, navLabel }: SideNavProps) {
  return (
    <nav
      aria-label={navLabel}
      className="hidden w-[248px] flex-col gap-1 border-e border-line p-4 lg:flex"
    >
      {items.map((item) => (
        <NavLink key={item.id} {...item} />
      ))}
    </nav>
  );
}

/** Tablet (design.md §4: 640-1023 px), icon-only rail; all 6 items. */
export function IconRail({ items, navLabel }: SideNavProps) {
  return (
    <nav
      aria-label={navLabel}
      className="hidden w-16 flex-col items-center gap-1 border-e border-line py-4 sm:flex lg:hidden"
    >
      {items.map((item) => (
        <NavLink key={item.id} {...item} iconOnly />
      ))}
    </nav>
  );
}

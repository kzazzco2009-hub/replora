import type { ComponentType, SVGProps } from "react";

export type NavIcon = ComponentType<SVGProps<SVGSVGElement>>;

export interface NavItemConfig {
  id: string;
  path: string;
  icon: NavIcon;
}

function icon(d: string): NavIcon {
  function Icon(props: SVGProps<SVGSVGElement>) {
    return (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        {...props}
      >
        <path d={d} />
      </svg>
    );
  }
  return Icon;
}

const HomeIcon = icon("M4 11.5 12 4l8 7.5M6 10v9h12v-9");
const NewRunIcon = icon("M12 5v14M5 12h14");
const RunsIcon = icon("M5 6h14M5 12h14M5 18h9");
const WorkflowsIcon = icon("M4 6h8l4 4h4M4 18h8l4-4h4");
const FilesIcon = icon(
  "M4 7a1 1 0 0 1 1-1h4l2 2h8a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1Z",
);
const SettingsIcon = icon("M12 4v16M4.5 7l15 10M19.5 7l-15 10");
export const MoreIcon = icon("M5 12h.01M12 12h.01M19 12h.01");

// id doubles as the next-intl "nav.<id>" message key (design.md §4).
export const NAV_ITEMS: NavItemConfig[] = [
  { id: "home", path: "", icon: HomeIcon },
  { id: "newRun", path: "/new-run", icon: NewRunIcon },
  { id: "runs", path: "/runs", icon: RunsIcon },
  { id: "workflows", path: "/workflows", icon: WorkflowsIcon },
  { id: "files", path: "/files", icon: FilesIcon },
  { id: "settings", path: "/settings", icon: SettingsIcon },
];

export const BOTTOM_TAB_PRIMARY_IDS = ["home", "newRun", "runs", "files"];

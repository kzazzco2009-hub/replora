import { useTranslations } from "next-intl";
import { ThemeToggle } from "@/components/theme/theme-toggle";

export default function Home() {
  const t = useTranslations("home");

  return (
    <main>
      <h1>{t("title")}</h1>
      <ThemeToggle />
    </main>
  );
}

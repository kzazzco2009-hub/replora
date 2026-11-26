import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import { LocaleSwitch } from "../../src/components/locale/locale-switch";
import messages from "../../messages/en.json";

const replace = vi.fn();

vi.mock("@/i18n/routing", () => ({
  usePathname: () => "/new-run",
  useRouter: () => ({ replace }),
}));

function renderSwitch() {
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <LocaleSwitch />
    </NextIntlClientProvider>,
  );
}

describe("LocaleSwitch", () => {
  it("marks the current locale with aria-pressed, and gives each button its own lang", () => {
    renderSwitch();
    const ar = screen.getByRole("button", { name: "AR" });
    const en = screen.getByRole("button", { name: "EN" });
    expect(ar.getAttribute("lang")).toBe("ar");
    expect(en.getAttribute("lang")).toBe("en");
    expect(en.getAttribute("aria-pressed")).toBe("true");
    expect(ar.getAttribute("aria-pressed")).toBe("false");
  });

  it("keeps the current path and switches locale on click", () => {
    renderSwitch();
    fireEvent.click(screen.getByRole("button", { name: "AR" }));
    expect(replace).toHaveBeenCalledWith("/new-run", { locale: "ar" });
  });
});

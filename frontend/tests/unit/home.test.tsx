import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";
import Home from "../../src/app/[locale]/page";
import messages from "../../messages/en.json";

function renderHome() {
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <Home />
    </NextIntlClientProvider>,
  );
}

describe("Home", () => {
  it("renders the heading", () => {
    renderHome();
    expect(
      screen.getByRole("heading", { level: 1, name: "Replora" }),
    ).toBeTruthy();
  });

  it("renders again in a fresh test without errors (first render)", () => {
    renderHome();
    expect(
      screen.getByRole("heading", { level: 1, name: "Replora" }),
    ).toBeTruthy();
  });

  it("renders again in a fresh test without errors (second render)", () => {
    renderHome();
    expect(
      screen.getByRole("heading", { level: 1, name: "Replora" }),
    ).toBeTruthy();
  });
});

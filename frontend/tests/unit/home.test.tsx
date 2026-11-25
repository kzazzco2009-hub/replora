import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Home from "../../src/app/[locale]/page";

describe("Home", () => {
  it("renders the heading", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Replora" }),
    ).toBeTruthy();
  });

  it("renders again in a fresh test without errors (first render)", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Replora" }),
    ).toBeTruthy();
  });

  it("renders again in a fresh test without errors (second render)", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Replora" }),
    ).toBeTruthy();
  });
});

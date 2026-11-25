import { describe, expect, it } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";

type Messages = { [key: string]: Messages | string };

/** Dotted leaf paths, so a shape mismatch (missing key, or object vs string) shows up as a path. */
function leafPaths(messages: Messages, prefix = ""): string[] {
  return Object.entries(messages).flatMap(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return typeof value === "string" ? [path] : leafPaths(value, path);
  });
}

function emptyPaths(messages: Messages, prefix = ""): string[] {
  return Object.entries(messages).flatMap(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof value === "string") {
      return value.trim() === "" ? [path] : [];
    }
    return emptyPaths(value, path);
  });
}

describe("messages/ar.json and messages/en.json key parity", () => {
  it("have the same set of keys", () => {
    expect(leafPaths(ar).sort()).toEqual(leafPaths(en).sort());
  });

  it("have no empty values in ar.json", () => {
    expect(emptyPaths(ar)).toEqual([]);
  });

  it("have no empty values in en.json", () => {
    expect(emptyPaths(en)).toEqual([]);
  });
});

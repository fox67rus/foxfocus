import { describe, expect, it } from "vitest";

import { applyTheme, readTheme, THEME_STORAGE_KEY } from "./theme";

describe("theme", () => {
  it("defaults to dark and persists the chosen theme", () => {
    localStorage.removeItem(THEME_STORAGE_KEY);
    expect(readTheme()).toBe("dark");

    applyTheme("light");
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("light");
    expect(readTheme()).toBe("light");

    applyTheme("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(readTheme()).toBe("dark");
  });
});

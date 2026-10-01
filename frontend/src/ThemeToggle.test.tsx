import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ThemeToggle } from "./components/ThemeToggle";
import { THEME_STORAGE_KEY } from "./theme";

describe("theme toggle", () => {
  it("switches the document theme and remembers it", () => {
    localStorage.removeItem(THEME_STORAGE_KEY);
    document.documentElement.dataset.theme = "dark";

    render(<ThemeToggle />);
    fireEvent.click(screen.getByRole("button", { name: /светлую тему/i }));

    expect(document.documentElement.dataset.theme).toBe("light");
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("light");
    expect(screen.getByRole("button", { name: /тёмную тему/i })).toBeInTheDocument();
  });
});

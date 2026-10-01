import { useState } from "react";

import { applyTheme, readTheme, type Theme } from "../theme";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => readTheme());
  const next: Theme = theme === "dark" ? "light" : "dark";

  function toggle() {
    applyTheme(next);
    setTheme(next);
  }

  return (
    <button
      type="button"
      className="rounded border border-line-strong bg-surface px-2 py-0.5 leading-none hover:bg-hover"
      onClick={toggle}
      aria-label={next === "light" ? "Включить светлую тему" : "Включить тёмную тему"}
    >
      {next === "light" ? "☀️" : "🌙"}
    </button>
  );
}

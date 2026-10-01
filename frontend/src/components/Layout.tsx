import { NavLink, Outlet } from "react-router-dom";
import { useState } from "react";

import { getUserId, setUserId } from "../api";
import { ThemeToggle } from "./ThemeToggle";

const LINKS = [
  { to: "/", label: "Входящие" },
  { to: "/tasks", label: "Задачи" },
  { to: "/notes", label: "Заметки" },
  { to: "/journal", label: "Журнал" },
];

export function Layout() {
  const [userId, setUser] = useState(getUserId);

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 py-4">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-line pb-3">
        <div className="flex items-baseline gap-6">
          <span className="text-sm font-semibold tracking-wide text-ink-soft">Foxfocus</span>
          <nav className="flex gap-4 text-sm">
            {LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                className={({ isActive }) =>
                  isActive ? "text-ink" : "text-faint hover:text-ink-soft"
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-faint">
            пользователь
            <select
              className="rounded border border-line-strong bg-surface px-2 py-1 text-ink-soft"
              value={userId}
              onChange={(event) => {
                setUserId(event.target.value);
                setUser(event.target.value);
                window.location.reload();
              }}
            >
              <option value="u_1">u_1</option>
              <option value="u_2">u_2</option>
            </select>
          </label>
          <ThemeToggle />
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}

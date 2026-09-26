import { NavLink, Outlet } from "react-router-dom";

import { getUserId, setUserId } from "../api";
import { useState } from "react";

const LINKS = [
  { to: "/", label: "Входящие" },
  { to: "/tasks", label: "Задачи" },
  { to: "/journal", label: "Журнал" },
];

export function Layout() {
  const [userId, setUser] = useState(getUserId);

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 py-4">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 pb-3">
        <div className="flex items-baseline gap-6">
          <span className="text-sm font-semibold tracking-wide text-zinc-200">Foxfocus</span>
          <nav className="flex gap-4 text-sm">
            {LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                className={({ isActive }) =>
                  isActive ? "text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <label className="flex items-center gap-2 text-xs text-zinc-500">
          пользователь
          <select
            className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-200"
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
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}

import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { Inbox } from "./pages/Inbox";
import { ItemCard } from "./pages/ItemCard";
import { Journal } from "./pages/Journal";
import { Notes } from "./pages/Notes";
import { Tasks } from "./pages/Tasks";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Inbox />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/notes" element={<Notes />} />
          <Route path="/journal" element={<Journal />} />
          <Route path="/items/:kind/:id" element={<ItemCard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

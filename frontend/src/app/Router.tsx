import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ChatApp } from "./ChatApp";
import { A2UIDemoPage } from "../features/chat/dev/A2UIDemoPage";

const enableDevRoutes = import.meta.env.DEV;

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatApp />} />
        {enableDevRoutes ? <Route path="/dev/a2ui" element={<A2UIDemoPage />} /> : null}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ChatApp } from "./ChatApp";
import { ConfigPage } from "@/features/config/ConfigPage";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatApp />} />
        <Route path="/config" element={<ConfigPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

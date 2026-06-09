import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ChatApp } from "./ChatApp";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatApp />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

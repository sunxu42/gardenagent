import React from "react";
import ReactDOM from "react-dom/client";
import { Toaster } from "@/components/ui/sonner";
import { AppRouter } from "./app/Router";
import "./shared/styles/reset.css";
import "./shared/styles/apple-tokens.css";
import "./shared/styles/globals.css";
import "./shared/styles/rail-panel-shell.css";
import "./shared/styles/mobile-shell.css";
import "./shared/styles/chat-desktop.css";
import "./shared/styles/chat-apple.css";
import "./shared/styles/theme-light.css";
import "./shared/styles/theme-rail.css";
import "./shared/styles/theme-dark.css";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("应用挂载失败：未找到 #root 元素。");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <AppRouter />
    <Toaster />
  </React.StrictMode>
);

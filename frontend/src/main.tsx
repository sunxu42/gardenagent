import React from "react";
import ReactDOM from "react-dom/client";
import { AppRouter } from "./app/Router";
import "./shared/styles/reset.css";
import "./shared/styles/globals.css";
import "./shared/styles/rail-panel-shell.css";
import "./shared/styles/mobile-shell.css";
import "./shared/styles/chat-desktop.css";
import "./shared/styles/theme-mint-cute.css";
import "./shared/styles/theme-rail.css";
import "./shared/styles/theme-dark.css";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("应用挂载失败：未找到 #root 元素。");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>
);

import React from "react";
import ReactDOM from "react-dom/client";
import { AppRouter } from "./app/Router";
import "./shared/styles/reset.css";
import "./shared/styles/globals.css";
import "./shared/styles/mobile-shell.css";
import "./shared/styles/chat-desktop.css";
import "./shared/styles/theme-mint-cute.css";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Failed to mount app: #root element not found.");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>
);

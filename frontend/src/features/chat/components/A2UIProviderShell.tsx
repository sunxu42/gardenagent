import type { ReactNode } from "react";
import { A2UIProvider } from "a2ui-shadcn";
import { a2uiComponentRegistry } from "./a2uiComponentRegistry";

interface A2UIProviderShellProps {
  children: ReactNode;
}

export function A2UIProviderShell({ children }: A2UIProviderShellProps) {
  return (
    <A2UIProvider defaultDir="ltr" componentRegistry={a2uiComponentRegistry}>
      {children}
    </A2UIProvider>
  );
}

import { Link } from "@tanstack/react-router";
import { Hammer, Settings } from "lucide-react";
import * as React from "react";

import { ApiStatusBadge } from "@/components/ApiStatusBadge";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-full flex-col">
      <header className="border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-2 text-sm font-semibold">
            <Hammer className="h-4 w-4 text-primary" />
            lumina-forge
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <NavLink to="/">Inventory</NavLink>
            <NavLink to="/optimize">Optimize</NavLink>
            <Link
              to="/settings"
              className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground"
            >
              <Settings className="h-4 w-4" />
              Settings
            </Link>
            <ApiStatusBadge />
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">{children}</main>
      <footer className="border-t border-border py-3 text-center text-xs text-muted-foreground">
        <span>Expedition 33 randomizer helper — all local, no telemetry.</span>
      </footer>
    </div>
  );
}

function NavLink({
  to,
  children,
}: {
  to: "/" | "/optimize";
  children: React.ReactNode;
}) {
  return (
    <Link
      to={to}
      className="text-muted-foreground hover:text-foreground [&.active]:font-semibold [&.active]:text-foreground"
      activeProps={{ className: "active" }}
    >
      {children}
    </Link>
  );
}

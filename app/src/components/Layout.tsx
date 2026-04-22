import { Link } from "@tanstack/react-router";
import { Settings } from "lucide-react";
import * as React from "react";

import { ApiStatusBadge } from "@/components/ApiStatusBadge";
import { ThemeToggle } from "@/components/ThemeToggle";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-paper flex min-h-full flex-col">
      <header className="sticky top-0 z-10 border-b border-border bg-background/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link
            to="/"
            className="group flex items-center gap-2.5 text-foreground"
          >
            {/* Two image layers, toggled by the .dark class on <html>. */}
            <img
              src="/logo-light.svg"
              alt=""
              className="h-8 w-8 shrink-0 rounded-md transition group-hover:scale-105 dark:hidden"
            />
            <img
              src="/logo.svg"
              alt="lumina-forge"
              className="hidden h-8 w-8 shrink-0 rounded-md transition group-hover:scale-105 dark:block"
            />
            <span className="font-display text-lg font-bold tracking-tight">
              lumina<span className="text-primary">·</span>forge
            </span>
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <NavLink to="/">Inventory</NavLink>
            <NavLink to="/optimize">Optimize</NavLink>
            <NavLink to="/vault">Vault</NavLink>
            <Link
              to="/settings"
              className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground [&.active]:text-foreground"
              activeProps={{ className: "active" }}
            >
              <Settings className="h-4 w-4" />
              Settings
            </Link>
            <ThemeToggle />
            <ApiStatusBadge />
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        {children}
      </main>
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
  to: "/" | "/optimize" | "/vault";
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

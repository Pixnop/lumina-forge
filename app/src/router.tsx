import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
} from "@tanstack/react-router";

import { Layout } from "@/components/Layout";
import { BuildDetailPage } from "@/pages/BuildDetailPage";
import { HomePage } from "@/pages/HomePage";
import { OptimizePage } from "@/pages/OptimizePage";
import { SettingsPage } from "@/pages/SettingsPage";
import { VaultPage } from "@/pages/VaultPage";

const rootRoute = createRootRoute({
  component: () => (
    <Layout>
      <Outlet />
    </Layout>
  ),
});

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: HomePage,
});

const optimizeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/optimize",
  component: OptimizePage,
});

const buildDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/builds/$rank",
  component: BuildDetailPage,
});

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/settings",
  component: SettingsPage,
});

const vaultRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/vault",
  component: VaultPage,
});

const routeTree = rootRoute.addChildren([
  homeRoute,
  optimizeRoute,
  buildDetailRoute,
  settingsRoute,
  vaultRoute,
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

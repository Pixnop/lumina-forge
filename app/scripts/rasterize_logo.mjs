// Rasterizes public/logo.svg to a 1024×1024 PNG so `tauri icon` can fan
// out all the platform variants from a single source file. Run with:
//   pnpm --dir app exec node scripts/rasterize_logo.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { Resvg } from "@resvg/resvg-js";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");
const source = resolve(root, "public/logo.svg");
const output = resolve(root, "src-tauri/icons/_source-1024.png");

const svg = readFileSync(source);
const resvg = new Resvg(svg, {
  fitTo: { mode: "width", value: 1024 },
  background: "#0B1025",
});
const png = resvg.render().asPng();
writeFileSync(output, png);
console.log(`[rasterize_logo] wrote ${output} (${png.byteLength} bytes)`);

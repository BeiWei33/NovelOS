import { defineConfig } from "tsup";
import { execSync } from "child_process";

export default defineConfig({
  entry: ["main.py"],
  format: "esm",
  noExternal: ["*"],
  outDir: "dist",
  async onSuccess() {
    console.log("Uvicorn server starting...");
  },
  skipNodeModulesBundle: true,
  target: "node22",
});
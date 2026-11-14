import { defineConfig, globalIgnores } from "eslint/config";
import next from "@next/eslint-plugin-next";
import tseslint from "typescript-eslint";
import hooks from "eslint-plugin-react-hooks";
export default defineConfig([
  ...tseslint.configs.recommended,
  { files: ["**/*.{ts,tsx}"], plugins: { "@next/next": next, "react-hooks": hooks }, rules: {
    ...next.configs.recommended.rules,
    ...next.configs["core-web-vitals"].rules,
    ...hooks.configs.recommended.rules,
  } },
  globalIgnores([".next/**", "next-env.d.ts"]),
]);

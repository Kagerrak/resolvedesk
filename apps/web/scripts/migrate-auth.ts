import { getMigrations } from "better-auth/db/migration";
import { auth } from "../lib/auth";
async function main() {
  const migration = await getMigrations(auth.options, { throwOnUnsafe: true });
  if (migration.schemaProblems.length)
    throw new Error(migration.schemaProblems.join("; "));
  await migration.runMigrations();
  console.log("Better Auth schema is current.");
  process.exit(0);
}
main().catch((error) => {
  console.error(error);
  process.exit(1);
});

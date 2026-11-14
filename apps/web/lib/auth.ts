import { betterAuth } from "better-auth";
import { anonymous } from "better-auth/plugins";
import { Pool } from "pg";

export const auth = betterAuth({
  database: new Pool({ connectionString: process.env.DATABASE_URL }),
  baseURL: process.env.BETTER_AUTH_URL,
  secret: process.env.BETTER_AUTH_SECRET,
  trustedOrigins: [process.env.BETTER_AUTH_URL ?? "http://localhost:3000"],
  session: {
    expiresIn: 60 * 60,
    updateAge: 0,
    cookieCache: { enabled: false },
  },
  rateLimit: { enabled: true, window: 60, max: 60, storage: "database" },
  plugins: [anonymous({ disableDeleteAnonymousUser: true })],
});

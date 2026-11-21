import { betterAuth } from "better-auth";
import { APIError } from "better-auth/api";
import { anonymous } from "better-auth/plugins";
import { Pool } from "pg";
import { publicDemoEnabled as publicDemo } from "./public-demo";

const database = new Pool({ connectionString: process.env.DATABASE_URL });

async function reservePublicIdentity() {
  const client = await database.connect();
  try {
    await client.query("BEGIN");
    await client.query(
      "SELECT pg_advisory_xact_lock(hashtextextended('public-auth-capacity',0))",
    );
    const hour = new Date();
    hour.setUTCMinutes(0, 0, 0);
    await client.query(
      "INSERT INTO public_auth_window(hour,identities) VALUES($1,0) ON CONFLICT DO NOTHING",
      [hour],
    );
    const reserved = await client.query(
      "UPDATE public_auth_window SET identities=identities+1 WHERE hour=$1 AND identities<20 RETURNING hour",
      [hour],
    );
    if (!reserved.rowCount)
      throw new APIError("TOO_MANY_REQUESTS", {
        message:
          "The demo is busy. Try again later; existing workspaces remain available.",
      });
    await client.query(
      "DELETE FROM public_auth_window WHERE hour < $1::timestamptz - interval '2 days'",
      [hour],
    );
    await client.query("COMMIT");
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}

export const auth = betterAuth({
  database,
  user: {
    additionalFields: {
      publicDemo: {
        type: "boolean",
        required: false,
        defaultValue: false,
        input: false,
      },
    },
  },
  databaseHooks: {
    user: {
      create: {
        before: async (user) => {
          if (publicDemo) await reservePublicIdentity();
          return { data: { ...user, publicDemo } };
        },
      },
    },
  },
  baseURL: process.env.BETTER_AUTH_URL,
  secret: process.env.BETTER_AUTH_SECRET,
  trustedOrigins: [process.env.BETTER_AUTH_URL ?? "http://localhost:3000"],
  session: {
    expiresIn: 60 * 60,
    disableSessionRefresh: true,
    cookieCache: { enabled: false },
  },
  rateLimit: { enabled: true, window: 60, max: 60, storage: "database" },
  plugins: [anonymous({ disableDeleteAnonymousUser: true })],
});

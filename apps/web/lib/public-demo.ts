// Match the server's accepted boolean environment values.
export const publicDemoEnabled = /^(true|1|yes|on|t|y)$/i.test(
  process.env.PUBLIC_DEMO_ONLY ?? "false",
);

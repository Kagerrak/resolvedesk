import { timingSafeEqual } from "node:crypto";

export const maxDuration = 60;

export async function GET(request: Request) {
  const secret = process.env.CRON_SECRET ?? "";
  if (process.env.PUBLIC_DEMO_ONLY !== "true" || secret.length < 32)
    return Response.json(
      { detail: "Public demo maintenance is not configured." },
      { status: 503 },
    );
  const supplied = Buffer.from(request.headers.get("authorization") ?? "");
  const expected = Buffer.from(`Bearer ${secret}`);
  if (
    supplied.length !== expected.length ||
    !timingSafeEqual(supplied, expected)
  )
    return Response.json(
      { detail: "Maintenance authorization required." },
      { status: 401 },
    );
  try {
    const response = await fetch(
      new URL("internal/maintenance", `${(process.env.API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "")}/`),
      {
        method: "POST",
        headers: {
          authorization: `Bearer ${secret}`,
          origin: new URL(process.env.BETTER_AUTH_URL!).origin,
        },
        cache: "no-store",
        signal: AbortSignal.timeout(45000),
        redirect: "error",
      },
    );
    return new Response(await response.arrayBuffer(), {
      status: response.status,
      headers: {
        "content-type": "application/json",
        "cache-control": "no-store",
      },
    });
  } catch {
    return Response.json(
      { detail: "Maintenance is unavailable. Retry the scheduled cleanup." },
      { status: 503 },
    );
  }
}

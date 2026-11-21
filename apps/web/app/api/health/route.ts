export async function GET() {
  try {
    const response = await fetch(
      new URL(
        "health",
        `${(process.env.API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "")}/`,
      ),
      {
        cache: "no-store",
        signal: AbortSignal.timeout(5000),
        redirect: "error",
      },
    );
    if (!response.ok) throw new Error("Workspace health unavailable");
    const body = await response.json();
    return Response.json(
      {
        status: body.status,
        mode: body.mode,
        public_demo: body.public_demo === true,
      },
      { headers: { "cache-control": "no-store" } },
    );
  } catch {
    return Response.json(
      { status: "unavailable" },
      { status: 503, headers: { "cache-control": "no-store" } },
    );
  }
}

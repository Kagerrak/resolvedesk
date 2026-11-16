import { NextRequest } from "next/server";

async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const route = path.join("/");
  if (
    !/^(demo|workspaces|workspaces\/[0-9a-f-]+\/(?:members|tickets(?:\/[0-9a-f-]+(?:\/draft)?)?))$/.test(
      route,
    )
  ) {
    return Response.json({ detail: "Not found" }, { status: 404 });
  }
  if (
    request.method !== "GET" &&
    request.headers.get("origin") !==
      new URL(process.env.BETTER_AUTH_URL!).origin
  ) {
    return Response.json(
      { detail: "Request origin not allowed" },
      { status: 403 },
    );
  }
  try {
    const response = await fetch(
      `${process.env.API_URL ?? "http://127.0.0.1:8000"}/${route}${request.nextUrl.search}`,
      {
        method: request.method,
        headers: {
          cookie: request.headers.get("cookie") ?? "",
          origin: request.headers.get("origin") ?? "",
          "content-type": "application/json",
        },
        body: request.method === "GET" ? undefined : await request.text(),
        cache: "no-store",
        signal: AbortSignal.timeout(10000),
        redirect: "error",
      },
    );
    return new Response(await response.text(), {
      status: response.status,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return Response.json(
      {
        detail:
          "The workspace service is unavailable. Your saved work is safe. Try again.",
      },
      { status: 503 },
    );
  }
}
export const GET = proxy;
export const POST = proxy;

export const PATCH = proxy;

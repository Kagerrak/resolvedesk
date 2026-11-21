import { NextRequest } from "next/server";

async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const route = path.join("/");
  if (
    !/^(public-policy|demo|workspaces|workspaces\/[0-9a-f-]+\/(?:evaluation-dataset|evaluations(?:\/[0-9a-f-]+(?:\/(?:cancel|cases(?:\/[0-9a-f-]+(?:\/reviews)?)?))?)?|activity(?:\/(?:indexing|generation|handling)\/[0-9a-f-]+(?:\/retry)?)?|knowledge(?:\/[0-9a-f-]+(?:\/(?:publish|archive|delete|retry|download))?)?|citations\/[0-9a-f-]+|members|tickets(?:\/[0-9a-f-]+(?:\/(?:draft|approval-reviews(?:\/[0-9a-f-]+\/approve)?|generations(?:\/(?:latest|[0-9a-f-]+\/(?:cancel|resume)))?|retrievals(?:\/latest)?))?)?))$/.test(
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
    let body: Uint8Array | undefined;
    if (request.method !== "GET" && request.body) {
      const reader = request.body.getReader();
      const parts: Uint8Array[] = [];
      let size = 0;
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > 2900000) {
          await reader.cancel();
          return Response.json(
            {
              detail:
                "This upload is too large. Keep PDFs under 2 MB and text files under 256 KB.",
            },
            { status: 413 },
          );
        }
        parts.push(value);
      }
      body = new Uint8Array(size);
      let offset = 0;
      for (const part of parts) {
        body.set(part, offset);
        offset += part.length;
      }
    }
    const response = await fetch(
      new URL(`${route}${request.nextUrl.search}`, `${(process.env.API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "")}/`),
      {
        method: request.method,
        headers: {
          cookie: request.headers.get("cookie") ?? "",
          origin: request.headers.get("origin") ?? "",
          "content-type": "application/json",
        },
        body: body as BodyInit | undefined,
        cache: "no-store",
        signal: AbortSignal.timeout(10000),
        redirect: "error",
      },
    );
    return new Response(await response.arrayBuffer(), {
      status: response.status,
      headers: {
        "Content-Type":
          response.headers.get("content-type") ?? "application/json",
        ...(response.headers.get("content-disposition")
          ? {
              "Content-Disposition": response.headers.get(
                "content-disposition",
              )!,
            }
          : {}),
        "X-Content-Type-Options": "nosniff",
        ...(route.endsWith("/download")
          ? { "Content-Security-Policy": "sandbox" }
          : {}),
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

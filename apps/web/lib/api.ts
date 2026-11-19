export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  method = "GET",
  signal?: AbortSignal,
  data?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/backend/${path}`, {
      method,
      signal,
      headers:
        data === undefined ? undefined : { "content-type": "application/json" },
      body: data === undefined ? undefined : JSON.stringify(data),
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new ApiError(
      503,
      "We couldn't reach your workspace. Check your connection and try again.",
    );
  }
  let body;
  try {
    body = await response.json();
  } catch {
    throw new ApiError(
      response.ok ? 502 : response.status,
      "The workspace service couldn't complete this request. Your saved work is safe. Try again.",
    );
  }
  if (!response.ok)
    throw new ApiError(
      response.status,
      typeof body.detail === "string"
        ? body.detail
        : "This request couldn't be completed. Try again.",
    );
  return body as T;
}
export type Workspace = {
  id: string;
  name: string;
  role: "admin" | "agent" | "viewer";
  mode: "fixture";
  expires_at: string | null;
};
export type Ticket = {
  id: string;
  number: number;
  subject: string;
  customer_name: string;
  customer_email: string;
  status: string;
  priority: string;
  assigned_to: string | null;
  revision: number;
  tags: string[];
  created_at: string;
};
export type Member = {
  user_id: string;
  name: string;
  role: "admin" | "agent" | "viewer";
};
export type TicketDetail = Ticket & {
  draft: {
    id: string;
    body: string;
    ticket_revision: number;
    generation_id: string | null;
    citation_ids: string[];
    created_at: string;
  } | null;
  events: {
    id: string;
    actor: string;
    action: string;
    changes: Record<
      string,
      | { before: string | string[] | null; after: string | string[] | null }
      | string
    >;
    created_at: string;
  }[];
  messages: {
    id: string;
    kind: string;
    sender_name: string;
    sender_email: string;
    body: string;
    created_at: string;
  }[];
};

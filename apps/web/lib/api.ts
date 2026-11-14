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
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/backend/${path}`, {
      method,
      signal,
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new ApiError(
      503,
      "We couldn't reach your workspace. Check your connection and try again.",
    );
  }
  const body = await response.json();
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
  revision: number;
  created_at: string;
};
export type TicketDetail = Ticket & {
  messages: {
    id: string;
    sender_name: string;
    sender_email: string;
    body: string;
    created_at: string;
  }[];
};

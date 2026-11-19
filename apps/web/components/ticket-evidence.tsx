"use client";
import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
type Run = {
  id: string;
  ticket_revision: number;
  created_at: string;
  sources_changed: boolean;
  results: {
    id: string;
    rank: number;
    available: boolean;
    title: string;
    version_number: number | null;
    heading: string | null;
    excerpt: string | null;
    page_number: number | null;
  }[];
};
type Passage = {
  title: string;
  version_number: number;
  heading: string;
  page_number: number | null;
  content: string;
  ordinal: number;
};
export function TicketEvidence({
  workspaceId,
  ticketId,
  revision,
  readOnly,
}: {
  workspaceId: string;
  ticketId: string;
  revision: number;
  readOnly: boolean;
}) {
  const [run, setRun] = useState<Run | null>(null),
    [passage, setPassage] = useState<Passage | null>(null);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true),
    [retry, setRetry] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null),
    trigger = useRef<HTMLButtonElement | null>(null),
    controller = useRef<AbortController | null>(null);
  const root = `workspaces/${workspaceId}`,
    route = `${root}/tickets/${ticketId}/retrievals`;
  useEffect(() => {
    const request = new AbortController();
    api<Run | null>(`${route}/latest`, "GET", request.signal)
      .then(setRun)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      })
      .finally(() => {
        if (!request.signal.aborted) setLoading(false);
      });
    return () => {
      request.abort();
      controller.current?.abort();
    };
  }, [route, retry]);
  useEffect(() => {
    if (passage) heading.current?.focus();
  }, [passage]);
  async function perform(citation?: string) {
    controller.current?.abort();
    const request = new AbortController();
    controller.current = request;
    setBusy(true);
    setError("");
    setPassage(null);
    try {
      if (citation)
        setPassage(
          await api<Passage>(
            `${root}/citations/${citation}`,
            "GET",
            request.signal,
          ),
        );
      else setRun(await api<Run>(route, "POST", request.signal));
    } catch (e) {
      if (e instanceof Error && e.name !== "AbortError") {
        setError(e.message);
        if (e instanceof ApiError && [401, 403, 404, 410].includes(e.status))
          setRun(null);
      }
    } finally {
      if (!request.signal.aborted) setBusy(false);
    }
  }
  return (
    <section className="ticket-evidence" aria-labelledby="evidence-title">
      <h3 id="evidence-title">Supporting evidence</h3>
      <p className="small muted">
        Fixture retrieval · deterministic matching, not measured AI quality.
      </p>
      {error && (
        <div role="alert">
          <p>{error}</p>
          <button
            className="secondary"
            onClick={() => {
              setError("");
              setLoading(true);
              setRetry((v) => v + 1);
            }}
          >
            Reload saved evidence
          </button>
        </div>
      )}
      {loading ? (
        <p role="status">Loading saved evidence…</p>
      ) : (
        <>
          {!readOnly && (
            <button
              className="secondary"
              disabled={busy}
              onClick={() => perform()}
            >
              {busy ? "Opening evidence…" : "Find supporting evidence"}
            </button>
          )}
          {readOnly && (
            <p className="small muted">
              Viewer access · inspect saved evidence.
            </p>
          )}
          <div role="status" aria-live="polite">
            {!run ? (
              <p>
                No saved retrieval.{" "}
                {readOnly
                  ? "Ask an Agent to retrieve published sources."
                  : "Find published sources for this conversation."}
              </p>
            ) : (
              <>
                <p className="small muted">
                  Retrieved {new Date(run.created_at).toLocaleString()}
                </p>
                {run.ticket_revision !== revision && (
                  <p>
                    The ticket changed. Retrieve again before relying on this
                    evidence.
                  </p>
                )}
                {run.sources_changed && (
                  <p>
                    Source material changed or was deleted. Find current
                    supporting evidence before relying on this retrieval.
                  </p>
                )}
                {!run.sources_changed &&
                  !run.results.some((r) => r.available) && (
                    <p>
                      I couldn&apos;t find a published source for this answer.
                      Review the ticket or escalate it.
                    </p>
                  )}
              </>
            )}
          </div>
          {run && (
            <ol className="evidence-results">
              {run.results.map((r) => (
                <li key={r.id}>
                  <strong>{r.title}</strong>
                  {r.available ? (
                    <>
                      <p className="small muted">
                        Version {r.version_number} ·{" "}
                        {r.page_number ? `Page ${r.page_number}` : r.heading}
                      </p>
                      <p className="evidence-excerpt">{r.excerpt}</p>
                      <button
                        className="secondary"
                        disabled={busy}
                        onClick={(e) => {
                          trigger.current = e.currentTarget;
                          perform(r.id);
                        }}
                      >
                        Open citation {r.rank}
                      </button>
                    </>
                  ) : (
                    <p className="small muted">
                      This source was retired or access changed. Retrieve again.
                    </p>
                  )}
                </li>
              ))}
            </ol>
          )}
          {passage && (
            <article
              className="citation-passage"
              aria-label="Authorized source passage"
            >
              <h4 tabIndex={-1} ref={heading}>
                {passage.title}
              </h4>
              <p className="small muted">
                Version {passage.version_number} ·{" "}
                {passage.page_number
                  ? `Page ${passage.page_number}`
                  : `Section ${passage.ordinal}: ${passage.heading}`}
              </p>
              <p className="message-body">{passage.content}</p>
              <button
                className="secondary"
                onClick={() => {
                  setPassage(null);
                  trigger.current?.focus();
                }}
              >
                Close citation
              </button>
            </article>
          )}
        </>
      )}
    </section>
  );
}

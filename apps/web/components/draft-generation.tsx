"use client";
import { useEffect, useRef, useState } from "react";
import { api, type TicketDetail } from "@/lib/api";
type Run = {
  id: string;
  status: string;
  mode: "fixture" | "openai";
  error: string | null;
  draft_id: string | null;
  citations: string[];
};
export function DraftGeneration({
  route,
  revision,
  disabled,
  readOnly,
  onGenerated,
  onActive,
}: {
  route: string;
  revision: number;
  disabled: boolean;
  readOnly: boolean;
  onGenerated: (detail: TicketDetail) => void;
  onActive: (active: boolean) => void;
}) {
  const [run, setRun] = useState<Run | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const applied = useRef("");
  const active = run?.status === "queued" || run?.status === "running";
  useEffect(() => {
    const controller = new AbortController();
    api<Run | null>(`${route}/generations/latest`, "GET", controller.signal)
      .then((next) => {
        applied.current = next?.id ?? "";
        setRun(next);
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [route]);
  useEffect(() => {
    onActive(active);
    return () => onActive(false);
  }, [active, onActive]);
  useEffect(() => {
    if (!active) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const next = await api<Run | null>(
          `${route}/generations/latest`,
          "GET",
          controller.signal,
        );
        setRun(next);
        if (
          next &&
          ["succeeded", "escalated"].includes(next.status) &&
          applied.current !== next.id
        ) {
          applied.current = next.id;
          const detail = await api<TicketDetail>(
            route,
            "GET",
            controller.signal,
          );
          onGenerated(detail);
        }
        if (next && ["queued", "running"].includes(next.status))
          timer = setTimeout(poll, 2500);
      } catch (e) {
        if (e instanceof Error && e.name !== "AbortError") setError(e.message);
      }
    }
    timer = setTimeout(poll, 1000);
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [active, route, onGenerated]);
  async function generate() {
    setBusy(true);
    setError("");
    try {
      const retrieval = await api<{ id: string } | null>(
        `${route}/retrievals/latest`,
      );
      if (!retrieval)
        throw new Error("Find supporting evidence before generating a draft.");
      setRun(
        await api<Run>(`${route}/generations`, "POST", undefined, {
          expected_revision: revision,
          retrieval_id: retrieval.id,
          request_id: crypto.randomUUID(),
        }),
      );
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Could not start drafting. Your saved draft is safe.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function cancel() {
    if (!run) return;
    setBusy(true);
    try {
      setRun(await api<Run>(`${route}/generations/${run.id}/cancel`, "POST"));
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Could not cancel. Check the saved run before retrying.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="draft-generation">
      <p className="small muted">
        {run?.mode === "openai"
          ? "Real provider generation"
          : "Fixture generation · extracts published evidence; no AI provider call"}
      </p>
      {!readOnly && (
        <div className="form-actions">
          <button
            type="button"
            className="secondary"
            disabled={disabled || active || busy}
            onClick={generate}
          >
            Generate draft
          </button>
          {active && (
            <button
              type="button"
              className="secondary"
              disabled={busy}
              onClick={cancel}
            >
              Cancel generation
            </button>
          )}
        </div>
      )}
      {disabled && !active && !readOnly && (
        <p className="small muted">
          Save or discard your local edits before generating.
        </p>
      )}
      <p role="status">
        {active
          ? "Preparing a draft. Your previous saved draft is safe."
          : run
            ? `${run.status === "succeeded" ? "Generated draft saved for human review" : run.status === "escalated" ? "Escalation draft saved for human review" : run.status}. ${run.error ?? ""}`
            : "No generation run yet."}
      </p>
      {error && <p role="alert">{error}</p>}
    </div>
  );
}

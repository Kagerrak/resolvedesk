"use client";
import { useEffect, useEffectEvent, useRef, useState } from "react";
import { api, type TicketDetail } from "@/lib/api";
type Run = {
  id: string;
  request_id: string;
  status: string;
  mode: "fixture" | "openai" | "deepseek";
  error: string | null;
  draft_id: string | null;
  citations: string[];
  can_resume?: boolean;
};
export function DraftGeneration({
  route,
  revision,
  draftId,
  disabled,
  readOnly,
  onGenerated,
  onActive,
}: {
  route: string;
  revision: number;
  draftId: string | undefined;
  disabled: boolean;
  readOnly: boolean;
  onGenerated: (detail: TicketDetail) => void;
  onActive: (active: boolean) => void;
}) {
  const [run, setRun] = useState<Run | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true),
    [retry, setRetry] = useState(0);
  const applied = useRef(""),
    requestId = useRef<string | null>(null);
  const active = run?.status === "queued" || run?.status === "running";
  const applyRun = useEffectEvent(
    async (next: Run | null, signal: AbortSignal) => {
      if (next?.request_id === requestId.current) requestId.current = null;
      if (
        next &&
        ["succeeded", "escalated"].includes(next.status) &&
        applied.current !== next.id
      ) {
        if (next.draft_id !== draftId) {
          if (disabled)
            throw new Error(
              "A generated draft is saved. Preserve or compare your local edits before refreshing it.",
            );
          const detail = await api<TicketDetail>(route, "GET", signal);
          onGenerated(detail);
        }
        applied.current = next.id;
      }
      setRun(next);
    },
  );
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let stopped = false;
    async function load() {
      try {
        const next = await api<Run | null>(
          `${route}/generations/latest`,
          "GET",
          controller.signal,
        );
        await applyRun(next, controller.signal);
        setError("");
        if (next && ["queued", "running"].includes(next.status))
          timer = setTimeout(load, 2500);
      } catch (e) {
        if (e instanceof Error && e.name !== "AbortError") setError(e.message);
      } finally {
        if (!stopped) setLoading(false);
      }
    }
    void load();
    return () => {
      stopped = true;
      controller.abort();
      clearTimeout(timer);
    };
  }, [route, retry]);
  useEffect(() => {
    onActive(active || loading);
    return () => onActive(false);
  }, [active, loading, onActive]);
  async function generate() {
    setBusy(true);
    setError("");
    try {
      const retrieval = await api<{ id: string } | null>(
        `${route}/retrievals/latest`,
      );
      if (!retrieval)
        throw new Error("Find supporting evidence before generating a draft.");
      requestId.current ??= crypto.randomUUID();
      setRun(
        await api<Run>(`${route}/generations`, "POST", undefined, {
          expected_revision: revision,
          retrieval_id: retrieval.id,
          request_id: requestId.current,
        }),
      );
      requestId.current = null;
      setRetry((v) => v + 1);
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
      setRetry((v) => v + 1);
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
  async function resume() {
    if (!run) return;
    setBusy(true);
    setError("");
    try {
      setRun(await api<Run>(`${route}/generations/${run.id}/resume`, "POST"));
      setRetry((v) => v + 1);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Could not resume. Refresh the saved run before retrying.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="draft-generation">
      <p className="small muted">
        {run?.mode === "deepseek"
          ? "Saved generation: DeepSeek"
          : run?.mode === "openai"
            ? "Saved generation: historical OpenAI"
            : "Demo generation · published extract, no AI provider call"}
      </p>
      {!readOnly && (
        <div className="form-actions">
          <button
            type="button"
            className="secondary"
            disabled={disabled || active || busy || loading}
            onClick={generate}
          >
            Generate demo draft
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
      {!readOnly && (
        <p className="small muted">
          This demo button uses a published extract without an AI provider call.
        </p>
      )}
      {run?.can_resume && !readOnly && (
        <button
          type="button"
          className="secondary"
          disabled={busy || disabled}
          onClick={() => void resume()}
        >
          Resume fixture preparation
        </button>
      )}
      {disabled && !active && !readOnly && (
        <p className="small muted">
          Save or discard your local edits before generating.
        </p>
      )}
      <p role="status">
        {loading
          ? "Checking saved generation…"
          : active
            ? "Preparing a draft. Your previous saved draft is safe."
            : run
              ? `${run.status === "succeeded" ? "Generated draft saved for human review" : run.status === "escalated" ? "Escalation draft saved for human review" : run.status}. ${run.error ?? ""}`
              : "No generation run yet."}
      </p>
      {error && (
        <div role="alert">
          <p>{error}</p>
          <button
            type="button"
            className="secondary"
            onClick={() => {
              setLoading(true);
              setError("");
              setRetry((v) => v + 1);
            }}
          >
            Refresh generation status
          </button>
        </div>
      )}
    </div>
  );
}

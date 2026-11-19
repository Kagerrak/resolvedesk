"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { api, ApiError, type Member, type TicketDetail } from "@/lib/api";
import { DraftCitations } from "@/components/draft-citations";

type Review = {
  id: string;
  body: string;
  actions: Record<
    string,
    { before: string | string[] | null; after: string | string[] | null }
  >;
  warnings: string[];
};

export function ReplyApproval({
  detail,
  workspaceId,
  disabled,
  actions,
  members,
  onApproved,
  onStale,
}: {
  detail: TicketDetail;
  workspaceId: string;
  disabled: boolean;
  actions: {
    status: string;
    priority: string;
    assigned_to: string | null;
    tags: string[];
  };
  members: Member[];
  onApproved: (next: TicketDetail) => void;
  onStale: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const [review, setReview] = useState<Review | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [stale, setStale] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const recorded = detail.events.some(
    (e) =>
      e.action === "demo_reply_recorded" &&
      e.changes.draft_revision === detail.draft?.id,
  );
  useEffect(() => {
    if (review && !dialog.current?.open) {
      dialog.current?.showModal();
      dialog.current?.querySelector<HTMLHeadingElement>("h2")?.focus();
    }
  }, [review]);
  function close() {
    dialog.current?.close();
    setReview(null);
    if (!stale) setError("");
    trigger.current?.focus();
  }
  async function openReview() {
    setBusy(true);
    setError("");
    try {
      const next = await api<Review>(
        `workspaces/${workspaceId}/tickets/${detail.id}/approval-reviews`,
        "POST",
        undefined,
        {
          expected_revision: detail.revision,
          draft_id: detail.draft?.id,
          ...actions,
          reopen: detail.status === "resolved" && actions.status === "open",
        },
      );
      setStale(false);
      setAcknowledged(false);
      setReview(next);
    } catch (reason) {
      setStale(reason instanceof ApiError && reason.status === 409);
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not prepare the review.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function approve() {
    if (!review) return;
    setBusy(true);
    setError("");
    try {
      const next = await api<TicketDetail>(
        `workspaces/${workspaceId}/tickets/${detail.id}/approval-reviews/${review.id}/approve`,
        "POST",
        undefined,
        { acknowledge_unverified: acknowledged },
      );
      onApproved(next);
      close();
    } catch (reason) {
      setStale(reason instanceof ApiError && reason.status === 409);
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not confirm the recorded reply.",
      );
    } finally {
      setBusy(false);
    }
  }
  function value(field: string, value: string | string[] | null) {
    if (field === "assigned_to")
      return value
        ? (members.find((m) => m.user_id === value)?.name ?? "Workspace member")
        : "Unassigned";
    return Array.isArray(value) ? value.join(", ") || "No tags" : value;
  }
  return (
    <>
      <button
        ref={trigger}
        type="button"
        className="primary"
        disabled={disabled || busy || !detail.draft?.body.trim() || recorded}
        onClick={() => void openReview()}
      >
        {recorded ? "Demo reply recorded" : "Review demo reply"}
      </button>
      {error && !review && (
        <p className="alert error" role="alert">
          {error}
          {stale && (
            <button
              type="button"
              className="secondary"
              onClick={() => {
                setError("");
                setStale(false);
                onStale();
              }}
            >
              Load latest saved version
            </button>
          )}
        </p>
      )}
      {review &&
        createPortal(
          <dialog
            ref={dialog}
            className="approval-dialog"
            aria-labelledby="approval-title"
            onCancel={(e) => {
              e.preventDefault();
              if (!busy) close();
            }}
          >
            {review && (
              <>
                <header>
                  <h2 id="approval-title" tabIndex={-1}>
                    Review exact demo reply
                  </h2>
                  <span className="badge">No email delivery</span>
                </header>
                <p>
                  Approval records this exact reply and the changes below in
                  this synthetic conversation.
                </p>
                <h3>Reply to {detail.customer_name}</h3>
                <p className="small muted">{detail.customer_email}</p>
                <p className="message-body review-body">{review.body}</p>
                {detail.draft && (
                  <DraftCitations
                    root={`workspaces/${workspaceId}`}
                    ids={detail.draft.citation_ids}
                  />
                )}
                <h3>Ticket changes</h3>
                {Object.keys(review.actions).length ? (
                  <ul>
                    {Object.entries(review.actions).map(([field, change]) => (
                      <li key={field}>
                        {field === "assigned_to" ? "Assignment" : field}:{" "}
                        {value(field, change.before)} →{" "}
                        {value(field, change.after)}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No ticket fields will change.</p>
                )}
                {review.warnings.map((warning) => (
                  <p className="alert" key={warning}>
                    {warning}
                  </p>
                ))}
                {!!review.warnings.length && (
                  <label className="approval-ack">
                    <input
                      type="checkbox"
                      checked={acknowledged}
                      onChange={(e) => setAcknowledged(e.target.checked)}
                      disabled={busy}
                    />
                    I reviewed the uncited claims and accept responsibility for
                    this demo reply.
                  </label>
                )}
                {error && (
                  <div className="alert error" role="alert">
                    {error}
                    <p>
                      If confirmation was interrupted, retry this approval to
                      check the same recorded reply. If the draft or evidence
                      changed, close this review and review again.
                    </p>
                  </div>
                )}
                <div className="form-actions">
                  <button
                    type="button"
                    className="secondary"
                    disabled={busy}
                    onClick={close}
                  >
                    Back to editing
                  </button>
                  <button
                    type="button"
                    className="primary"
                    disabled={
                      busy || (!!review.warnings.length && !acknowledged)
                    }
                    onClick={() => void approve()}
                  >
                    {busy
                      ? "Checking approval…"
                      : "Approve and record demo reply"}
                  </button>
                </div>
              </>
            )}
          </dialog>,
          document.body,
        )}
    </>
  );
}

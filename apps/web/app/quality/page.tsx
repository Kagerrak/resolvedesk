"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Brand } from "@/components/brand";
import { DraftCitations } from "@/components/draft-citations";
import { ThemeToggle } from "@/components/theme-toggle";
import { api, ApiError, type Workspace } from "@/lib/api";

type Ratio = { numerator: number; denominator: number; value: number | null };
type Allocation = {
  conservative_micros: number;
  generation_attempts: number;
  measured_completions: number;
  note: string;
};
type Timing = {
  count: number;
  median_ms: number | null;
  p95_ms: number | null;
};
type Summary = {
  planned_cases: number;
  completed_cases: number;
  failed_cases?: number;
  source_recall_at_5?: Ratio;
  split_source_recall_at_5?: Record<string, Ratio>;
  fixture?: {
    outputs: number;
    citation_validity: Ratio;
    workflow_match: Ratio;
  };
  provider?: {
    planned_outputs: number;
    outputs: number;
    citation_validity: Ratio;
    workflow_match: Ratio;
    application_escalations: number;
  };
  critical?: {
    workspace_disclosures: number;
    unapproved_actions: number;
    fixture_observed_cases: number;
    provider_observed_cases: number;
  };
  allocation?: Allocation;
  timing?: { retrieval: Timing; provider_preparation: Timing; scope: string };
};
type Run = {
  id: string;
  dataset_version: string;
  dataset_hash: string;
  split: string;
  method: string;
  mode: string;
  model: string;
  prompt_version: string | null;
  status: string;
  summary: Summary;
  allocation?: Allocation;
  error: string | null;
  created_at: string;
  finished_at: string | null;
  limitations: string;
  reviews?: {
    coverage: number;
    support_denominator: number;
    verdicts: Record<string, number>;
    origins: Record<string, number>;
  };
};
type Dataset = {
  version: string;
  hash: string;
  article_count: number;
  case_count: number;
  tuning_count: number;
  held_out_count: number;
  live_sample_count: number;
  methods: string[];
  label_origin: string;
  split_policy: string;
  fixture_note: string;
};
type CaseRow = {
  id: string;
  case_key: string;
  split: string;
  category: string;
  subject: string;
  status: string;
  error: string | null;
  has_provider_output: boolean;
  source_hits: number;
  source_expected: number;
  fixture_outcome: string | null;
  provider_outcome: string | null;
};
type Output = {
  body: string;
  citation_ids: string[];
  outcome: string;
  model: string;
  prompt_version: string | null;
  output_hash: string;
  reason: string | null;
  mode: string;
};
type CaseDetail = {
  id: string;
  definition: {
    id: string;
    subject: string;
    body: string;
    split: string;
    category: string;
    expected_sources: string[];
    expected_abstention: boolean;
  };
  status: string;
  fixture_output: Output | null;
  provider_output: Output | null;
  error: string | null;
  reviews: {
    id: string;
    output_hash: string;
    reviewer_kind: string;
    verdict: string;
    note: string;
    created_at: string;
  }[];
};
const percent = (r?: Ratio) =>
  !r || r.value === null
    ? r
      ? `Not measured (${r.numerator}/${r.denominator})`
      : "Not measured"
    : `${(r.value * 100).toFixed(1)}% (${r.numerator}/${r.denominator})`;
const methodName = (m: string) =>
  m === "bm25-v1"
    ? "Lexical candidate (BM25)"
    : "Exact cosine · fixture vectors";
const active = (r: Run | null) =>
  !!r && ["queued", "preparing", "running"].includes(r.status);

const duration = (t?: Timing) =>
  !t?.count || t.median_ms === null || t.p95_ms === null
    ? "Not measured"
    : `${t.median_ms.toFixed(1)} / ${t.p95_ms.toFixed(1)} ms (${t.count} observations)`;

export default function QualityPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]),
    [workspaceId, setWorkspaceId] = useState("");
  const [dataset, setDataset] = useState<Dataset | null>(null),
    [runs, setRuns] = useState<Run[]>([]),
    [run, setRun] = useState<Run | null>(null),
    [runId, setRunId] = useState("");
  const [scope, setScope] = useState("tuning"),
    [method, setMethod] = useState("exact-cosine-v1"),
    [caseSplit, setCaseSplit] = useState("all");
  const [caseOffset, setCaseOffset] = useState(0),
    [caseTotal, setCaseTotal] = useState(0);
  const [cases, setCases] = useState<CaseRow[]>([]),
    [detail, setDetail] = useState<CaseDetail | null>(null),
    [caseId, setCaseId] = useState("");
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true),
    [reload, setReload] = useState(0);
  const [verdict, setVerdict] = useState("supported"),
    [note, setNote] = useState("");
  const request = useRef<{ key: string; id: string } | null>(null),
    reviewRequest = useRef<{ key: string; id: string } | null>(null);
  const heading = useRef<HTMLHeadingElement>(null),
    current = useRef("");
  const admin = workspaces.find((w) => w.id === workspaceId)?.role === "admin";
  useEffect(() => {
    if (!note.trim()) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [note]);
  function canNavigate() {
    return !note.trim() || window.confirm("Discard this unsaved assessment?");
  }
  function fail(reason: unknown) {
    if (
      reason instanceof ApiError &&
      [401, 403, 404, 410].includes(reason.status)
    ) {
      setRun(null);
      setRuns([]);
      setCases([]);
      setDetail(null);
      if (reason.status === 401) {
        setWorkspaces([]);
        setWorkspaceId("");
      }
    }
    if (reason instanceof Error && reason.name !== "AbortError")
      setError(reason.message);
    setLoading(false);
  }
  useEffect(() => {
    const c = new AbortController();
    api<Workspace[]>("workspaces", "GET", c.signal)
      .then((rows) => {
        setWorkspaces(rows);
        const wanted = new URLSearchParams(window.location.search).get(
          "workspace",
        );
        const id = rows.find((w) => w.id === wanted)?.id ?? rows[0]?.id ?? "";
        current.current = id;
        setWorkspaceId(id);
        if (!id) setLoading(false);
      })
      .catch(fail);
    return () => c.abort();
  }, []);
  useEffect(() => {
    if (!workspaceId) return;
    const c = new AbortController();
    Promise.all([
      api<Dataset>(
        `workspaces/${workspaceId}/evaluation-dataset`,
        "GET",
        c.signal,
      ),
      api<Run[]>(`workspaces/${workspaceId}/evaluations`, "GET", c.signal),
    ])
      .then(([data, rows]) => {
        if (c.signal.aborted || current.current !== workspaceId) return;
        setDataset(data);
        setRuns(rows);
        setLoading(false);
        if (!runId) {
          const wanted = new URLSearchParams(window.location.search).get("run");
          setRunId(rows.find((r) => r.id === wanted)?.id ?? rows[0]?.id ?? "");
        }
      })
      .catch((reason) => {
        if (!c.signal.aborted) {
          setRuns([]);
          setRun(null);
          setDetail(null);
          fail(reason);
        }
      });
    return () => c.abort();
  }, [workspaceId, reload, runId]);
  useEffect(() => {
    if (!workspaceId || !runId) return;
    const c = new AbortController();
    Promise.all([
      api<Run>(
        `workspaces/${workspaceId}/evaluations/${runId}`,
        "GET",
        c.signal,
      ),
      api<{ items: CaseRow[]; total: number }>(
        `workspaces/${workspaceId}/evaluations/${runId}/cases?split=${caseSplit}&limit=20&offset=${caseOffset}`,
        "GET",
        c.signal,
      ),
    ])
      .then(([next, rows]) => {
        if (c.signal.aborted || current.current !== workspaceId) return;
        setRun(next);
        setCases(rows.items);
        setCaseTotal(rows.total);
      })
      .catch((reason) => {
        if (!c.signal.aborted) {
          setRun(null);
          setCases([]);
          setDetail(null);
          fail(reason);
        }
      });
    return () => c.abort();
  }, [workspaceId, runId, caseSplit, caseOffset, reload]);
  useEffect(() => {
    if (!workspaceId || !runId || !caseId) return;
    const c = new AbortController();
    api<CaseDetail>(
      `workspaces/${workspaceId}/evaluations/${runId}/cases/${caseId}`,
      "GET",
      c.signal,
    )
      .then((next) => {
        if (c.signal.aborted || current.current !== workspaceId) return;
        setDetail(next);
        requestAnimationFrame(() => heading.current?.focus());
      })
      .catch((reason) => {
        if (!c.signal.aborted) {
          setDetail(null);
          fail(reason);
        }
      });
    return () => c.abort();
  }, [workspaceId, runId, caseId, reload]);
  async function start() {
    if (!dataset || !canNavigate()) return;
    setNote("");
    setBusy(true);
    setError("");
    setNotice("");
    const key = `${workspaceId}/${method}/${scope}`;
    if (request.current?.key !== key)
      request.current = { key, id: crypto.randomUUID() };
    try {
      const next = await api<Run>(
        `workspaces/${workspaceId}/evaluations`,
        "POST",
        undefined,
        {
          request_id: request.current.id,
          dataset_version: dataset.version,
          split: scope,
          method,
        },
      );
      request.current = null;
      setRunId(next.id);
      setCaseOffset(0);
      setRun(next);
      setCaseId("");
      setDetail(null);
      setCases([]);
      setReload((v) => v + 1);
      setNotice(
        "Fixture evaluation queued. No paid provider request was enabled.",
      );
    } catch (reason) {
      fail(reason);
    } finally {
      setBusy(false);
    }
  }
  async function cancel() {
    if (!run) return;
    setBusy(true);
    setError("");
    try {
      await api(
        `workspaces/${workspaceId}/evaluations/${run.id}/cancel`,
        "POST",
        undefined,
        {},
      );
      setReload((v) => v + 1);
      setNotice(
        "Evaluation cancelled. Recorded results remain available; an in-flight paid preparation may still count toward allocation.",
      );
    } catch (reason) {
      fail(reason);
    } finally {
      setBusy(false);
    }
  }
  async function review(e: React.FormEvent) {
    e.preventDefault();
    if (!detail?.provider_output) return;
    setBusy(true);
    setError("");
    const key = `${detail.id}/${detail.provider_output.output_hash}/${verdict}/${note}`;
    if (reviewRequest.current?.key !== key)
      reviewRequest.current = { key, id: crypto.randomUUID() };
    try {
      await api(
        `workspaces/${workspaceId}/evaluations/${runId}/cases/${detail.id}/reviews`,
        "POST",
        undefined,
        {
          request_id: reviewRequest.current.id,
          output_hash: detail.provider_output.output_hash,
          reviewer_kind: "member",
          verdict,
          note,
        },
      );
      reviewRequest.current = null;
      setNote("");
      setReload((v) => v + 1);
      setNotice(
        "Assessment saved against the exact live output. It is labeled as a member review.",
      );
    } catch (reason) {
      fail(reason);
    } finally {
      setBusy(false);
    }
  }
  const summary = run?.summary,
    allocation = run?.allocation ?? summary?.allocation;
  return (
    <div className="knowledge-shell">
      <header className="app-header">
        <Brand />
        <Link
          className="secondary"
          onClick={(e) => {
            if (!canNavigate()) e.preventDefault();
          }}
          href="/inbox"
        >
          Inbox
        </Link>
        <Link
          className="secondary"
          onClick={(e) => {
            if (!canNavigate()) e.preventDefault();
          }}
          href={`/knowledge?workspace=${workspaceId}`}
        >
          Knowledge
        </Link>
        <Link
          className="secondary"
          onClick={(e) => {
            if (!canNavigate()) e.preventDefault();
          }}
          href={`/activity?workspace=${workspaceId}`}
        >
          Activity
        </Link>
        <div className="header-actions">
          <ThemeToggle />
        </div>
      </header>
      <main id="main" className="knowledge-main">
        <header className="workspace-header">
          <div>
            <span className="eyebrow">Measured assistance</span>
            <h1>Quality</h1>
            <p className="muted">
              Inspect the results and the cases behind them.
            </p>
          </div>
          <label>
            Workspace
            <select
              className="workspace-select"
              value={workspaceId}
              disabled={busy || !workspaces.length}
              onChange={(e) => {
                if (!canNavigate()) return;
                setNote("");
                setCaseOffset(0);
                current.current = e.target.value;
                setWorkspaceId(e.target.value);
                setDataset(null);
                setRuns([]);
                setRun(null);
                setRunId("");
                setCases([]);
                setCaseId("");
                setDetail(null);
                setError("");
                setNotice("");
                setLoading(true);
                window.history.replaceState(
                  null,
                  "",
                  `/quality?workspace=${e.target.value}`,
                );
              }}
            >
              {!workspaces.length && <option>No workspace</option>}
              {workspaces.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          </label>
        </header>
        {dataset && (
          <p>
            {dataset.article_count} authored articles · {dataset.case_count}{" "}
            synthetic cases ({dataset.tuning_count} tuning,{" "}
            {dataset.held_out_count} held out). Labels are author supplied.
          </p>
        )}
        <p className="small muted">
          Fixture extracts do not establish live AI quality. Live DeepSeek
          samples retain fixture retrieval. Agent rubric assessments are
          supplementary; no numeric answer-quality release threshold is set.
        </p>
        {admin && dataset && (
          <section className="quality-controls" aria-labelledby="run-controls">
            <h2 id="run-controls">Prepare a fixture evaluation</h2>
            <p className="small muted">
              Adds synthetic cases and a fixed corpus to an owned demo. Existing
              source content is preserved. Up to three evaluations per demo.
            </p>
            <div className="activity-filters">
              <label>
                Cases
                <select
                  value={scope}
                  disabled={busy || active(run)}
                  onChange={(e) => setScope(e.target.value)}
                >
                  <option value="tuning">
                    Tuning cases ({dataset.tuning_count})
                  </option>
                  <option value="all">
                    Full frozen set ({dataset.case_count})
                  </option>
                </select>
              </label>
              <label>
                Retriever
                <select
                  value={method}
                  disabled={busy || active(run)}
                  onChange={(e) => setMethod(e.target.value)}
                >
                  {dataset.methods.map((m) => (
                    <option key={m} value={m}>
                      {methodName(m)}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="primary"
                disabled={busy || active(run)}
                onClick={() => void start()}
              >
                Run fixture evaluation
              </button>
            </div>
          </section>
        )}
        <div className="form-actions">
          <button
            className="secondary"
            disabled={busy || !workspaceId}
            onClick={() => {
              setError("");
              setReload((v) => v + 1);
            }}
          >
            Refresh results
          </button>
          {admin && active(run) && (
            <button
              className="secondary"
              disabled={busy}
              onClick={() => void cancel()}
            >
              Cancel evaluation
            </button>
          )}
        </div>
        {error && (
          <div className="alert error" role="alert">
            {error}
            <p>
              Refresh to inspect saved runs before retrying. A repeated start
              request uses the same request identifier.
            </p>
            <Link href="/">Demo entry</Link>
          </div>
        )}
        {notice && (
          <p className="save-notice" role="status">
            {notice}
          </p>
        )}
        <div className="activity-layout quality-layout">
          <section aria-labelledby="runs-title">
            <h2 id="runs-title">Evaluation runs</h2>
            {loading ? (
              <p role="status">Loading results…</p>
            ) : !runs.length ? (
              <p>No saved evaluation runs in this workspace.</p>
            ) : (
              <ul className="activity-list">
                {runs.map((row) => (
                  <li key={row.id}>
                    <button
                      className="activity-row"
                      aria-pressed={row.id === runId}
                      onClick={() => {
                        if (row.id === runId || !canNavigate()) return;
                        setNote("");
                        setCaseOffset(0);
                        setRunId(row.id);
                        setRun(null);
                        setCases([]);
                        setCaseId("");
                        setDetail(null);
                        setError("");
                      }}
                    >
                      <strong>{methodName(row.method)}</strong>
                      <span>
                        {row.mode === "fixture"
                          ? "Fixture only"
                          : "Live DeepSeek sample + fixture comparison"}{" "}
                        · {row.split} · {row.status}
                      </span>
                      <span className="small">
                        Source recall@5:{" "}
                        {percent(row.summary.source_recall_at_5)}
                      </span>
                      <time className="small muted" dateTime={row.created_at}>
                        {new Date(row.created_at).toLocaleString()}
                      </time>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section aria-labelledby="results-title" className="activity-detail">
            <h2 id="results-title">
              {run ? "Recorded results" : "Run details"}
            </h2>
            {!run ? (
              <p>Choose a run to inspect its measurements.</p>
            ) : (
              <>
                <p>
                  <span className="badge">
                    {run.mode === "fixture"
                      ? "Fixture only"
                      : "Live sample · fixture retrieval"}
                  </span>{" "}
                  · {run.status}
                </p>
                <p>
                  {summary?.completed_cases ?? 0}/{summary?.planned_cases ?? 0}{" "}
                  cases completed · {summary?.failed_cases ?? 0} failed
                </p>
                {run.error && (
                  <p className="alert error" role="alert">
                    {run.error}
                  </p>
                )}
                <dl className="quality-metrics">
                  <dt>Expected source recall@5</dt>
                  <dd>{percent(summary?.source_recall_at_5)}</dd>
                  <dt>Held-out source recall@5</dt>
                  <dd>
                    {percent(summary?.split_source_recall_at_5?.held_out)}
                  </dd>
                  <dt>Fixture citation IDs valid</dt>
                  <dd>{percent(summary?.fixture?.citation_validity)}</dd>
                  <dt>Live outputs</dt>
                  <dd>
                    {summary?.provider?.outputs ?? 0}/
                    {summary?.provider?.planned_outputs ?? 0} planned
                  </dd>
                  <dt>Live citation IDs valid</dt>
                  <dd>{percent(summary?.provider?.citation_validity)}</dd>
                  <dt>Live expected workflow</dt>
                  <dd>{percent(summary?.provider?.workflow_match)}</dd>
                  <dt>Observed workspace disclosures</dt>
                  <dd>
                    {summary?.critical?.workspace_disclosures ?? "Not measured"}
                  </dd>
                  <dt>Observed unapproved effects</dt>
                  <dd>
                    {summary?.critical?.unapproved_actions ?? "Not measured"}
                  </dd>
                  <dt>Critical-check coverage</dt>
                  <dd>
                    {summary?.critical?.fixture_observed_cases ?? 0} fixture ·{" "}
                    {summary?.critical?.provider_observed_cases ?? 0} live
                    outputs
                  </dd>
                  <dt>Conservative app allocation</dt>
                  <dd>
                    {allocation
                      ? `USD ${(allocation.conservative_micros / 1e6).toFixed(6)}`
                      : "Not measured"}
                  </dd>
                  <dt>Live output assessments</dt>
                  <dd>
                    {run.reviews?.coverage ?? 0} reviewed · support denominator{" "}
                    {run.reviews?.support_denominator ?? 0}
                  </dd>
                  <dt>Retrieval median / p95</dt>
                  <dd>{duration(summary?.timing?.retrieval)}</dd>
                  <dt>Live preparation median / p95</dt>
                  <dd>{duration(summary?.timing?.provider_preparation)}</dd>
                </dl>
                <p className="small muted">
                  Recall uses expected source labels in planned answerable
                  cases; unfinished cases contribute zero hits. Citation
                  validity is separate from claim support. Allocation includes
                  unresolved reservations and is not a provider invoice. Zero
                  observed issues describes this finite set only.
                </p>
                <details>
                  <summary>Run provenance and limitations</summary>
                  <dl>
                    <dt>Dataset</dt>
                    <dd>{run.dataset_version}</dd>
                    <dt>Dataset hash</dt>
                    <dd>{run.dataset_hash}</dd>
                    <dt>Method</dt>
                    <dd>{run.method}</dd>
                    <dt>Model</dt>
                    <dd>{run.model}</dd>
                    <dt>Prompt</dt>
                    <dd>{run.prompt_version ?? "No live-model prompt"}</dd>
                  </dl>
                  <p>{run.limitations}</p>
                </details>
              </>
            )}
          </section>
        </div>
        {run && (
          <section className="quality-cases" aria-labelledby="cases-title">
            <header className="workspace-header">
              <h2 id="cases-title">Cases</h2>
              <label>
                Split
                <select
                  className="workspace-select"
                  value={caseSplit}
                  onChange={(e) => {
                    if (!canNavigate()) return;
                    setNote("");
                    setCaseSplit(e.target.value);
                    setCaseId("");
                    setDetail(null);
                  }}
                >
                  <option value="all">All cases</option>
                  <option value="tuning">Tuning</option>
                  <option value="held_out">Held out</option>
                </select>
              </label>
            </header>
            <div className="activity-layout">
              <div>
                <ul className="activity-list">
                  {cases.map((row) => (
                    <li key={row.id}>
                      <button
                        className="activity-row"
                        aria-pressed={row.id === caseId}
                        onClick={() => {
                          if (row.id === caseId || !canNavigate()) return;
                          setCaseId(row.id);
                          setDetail(null);
                          setError("");
                          setNote("");
                        }}
                      >
                        <span className="small muted">
                          {row.case_key} · {row.split} · {row.category}
                        </span>
                        <strong>{row.subject}</strong>
                        <span>
                          {row.status} · sources {row.source_hits}/
                          {row.source_expected} ·{" "}
                          {row.has_provider_output
                            ? "live output"
                            : row.fixture_outcome
                              ? "fixture extract"
                              : "not prepared"}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
                {!cases.length && <p>No cases in this split.</p>}
                {caseTotal > 20 && (
                  <div className="form-actions">
                    <button
                      className="secondary"
                      disabled={!caseOffset || busy}
                      onClick={() => {
                        if (!canNavigate()) return;
                        setNote("");
                        setCaseOffset((v) => Math.max(0, v - 20));
                        setCaseId("");
                        setDetail(null);
                      }}
                    >
                      Previous cases
                    </button>
                    <span>
                      {caseOffset + 1}–{Math.min(caseOffset + 20, caseTotal)} of{" "}
                      {caseTotal}
                    </span>
                    <button
                      className="secondary"
                      disabled={caseOffset + 20 >= caseTotal || busy}
                      onClick={() => {
                        if (!canNavigate()) return;
                        setNote("");
                        setCaseOffset((v) => v + 20);
                        setCaseId("");
                        setDetail(null);
                      }}
                    >
                      Next cases
                    </button>
                  </div>
                )}
              </div>
              <section className="activity-detail" aria-labelledby="case-title">
                <h2 ref={heading} id="case-title" tabIndex={-1}>
                  {detail ? detail.definition.subject : "Case details"}
                </h2>
                {!detail ? (
                  <p>
                    {caseId
                      ? error
                        ? "Case could not be loaded. Refresh results to recover."
                        : "Loading case…"
                      : "Choose a case to inspect its output and expected sources."}
                  </p>
                ) : (
                  <>
                    <p className="message-body">{detail.definition.body}</p>
                    <p className="small muted">
                      Authored expectation:{" "}
                      {detail.definition.expected_abstention
                        ? "escalation"
                        : "supported answer"}
                      . Expected source labels:{" "}
                      {detail.definition.expected_sources.join(", ") || "none"}.
                    </p>
                    {detail.error && (
                      <p className="alert error">{detail.error}</p>
                    )}
                    {detail.fixture_output && (
                      <details>
                        <summary>Fixture extract · no live AI quality</summary>
                        <p className="message-body">
                          {detail.fixture_output.body}
                        </p>
                        <DraftCitations
                          root={`workspaces/${workspaceId}`}
                          ids={detail.fixture_output.citation_ids}
                        />
                      </details>
                    )}
                    {detail.provider_output ? (
                      <>
                        <h3>Saved live application output</h3>
                        <p className="message-body">
                          {detail.provider_output.body}
                        </p>
                        <DraftCitations
                          root={`workspaces/${workspaceId}`}
                          ids={detail.provider_output.citation_ids}
                        />
                        <p className="small muted">
                          {detail.provider_output.model} ·{" "}
                          {detail.provider_output.prompt_version}. Escalations
                          may use application-owned wording. Sources may have
                          changed since this recorded run.
                        </p>
                        {admin && (
                          <form onSubmit={(e) => void review(e)}>
                            <h3>Review this exact output</h3>
                            <p className="small muted">
                              This form records a workspace member assessment,
                              not verified independent human ground truth. Agent
                              annotations use their own explicit label.
                            </p>
                            <label>
                              Assessment
                              <select
                                className="workspace-select"
                                value={verdict}
                                disabled={busy}
                                onChange={(e) => setVerdict(e.target.value)}
                              >
                                <option value="supported">
                                  Supported answer
                                </option>
                                <option value="unsupported">
                                  Unsupported answer
                                </option>
                                <option value="safe_escalation">
                                  Safe escalation
                                </option>
                                <option value="conservative_escalation">
                                  Conservative escalation
                                </option>
                              </select>
                            </label>
                            <label>
                              Evidence reasoning
                              <textarea
                                value={note}
                                onChange={(e) => setNote(e.target.value)}
                                required
                                minLength={10}
                                maxLength={2000}
                                rows={4}
                                disabled={busy}
                              />
                            </label>
                            <button className="secondary" disabled={busy}>
                              Save assessment
                            </button>
                          </form>
                        )}
                      </>
                    ) : (
                      <p className="small muted">
                        No saved live provider output for this case.
                      </p>
                    )}
                    {!!detail.reviews.length && (
                      <section>
                        <h3>Assessment history</h3>
                        {detail.reviews.map((r) => (
                          <article key={r.id}>
                            <strong>{r.verdict.replaceAll("_", " ")}</strong>
                            <p className="small muted">
                              {r.reviewer_kind === "agent_rubric"
                                ? "Agent rubric assessment"
                                : "Workspace member assessment"}{" "}
                              · {new Date(r.created_at).toLocaleString()}
                            </p>
                            <p>{r.note}</p>
                          </article>
                        ))}
                      </section>
                    )}
                  </>
                )}
              </section>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
type Passage = {
  title: string;
  version_number: number;
  page_number: number | null;
  ordinal: number;
  content: string;
};
export function DraftCitations({ root, ids }: { root: string; ids: string[] }) {
  const [source, setSource] = useState<Passage | null>(null),
    [selected, setSelected] = useState(""),
    [error, setError] = useState("");
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  async function open(id: string) {
    controller.current?.abort();
    const request = new AbortController();
    controller.current = request;
    setSource(null);
    setError("");
    setSelected(id);
    try {
      setSource(
        await api<Passage>(`${root}/citations/${id}`, "GET", request.signal),
      );
    } catch (e) {
      if (e instanceof Error && e.name !== "AbortError") setError(e.message);
    }
  }
  if (!ids.length) return null;
  return (
    <section aria-label="Draft citation references">
      <p className="small muted">
        Evidence references are retained after edits. Review whether each source
        supports the current wording.
      </p>
      <div className="form-actions">
        {ids.map((id, index) => (
          <button
            type="button"
            className="secondary"
            key={id}
            aria-expanded={selected === id && !!source}
            onClick={() => open(id)}
          >
            Draft source {index + 1}
          </button>
        ))}
      </div>
      {error && <p role="alert">{error}</p>}
      {source && (
        <article aria-label="Draft source passage">
          <h4>{source.title}</h4>
          <p className="small muted">
            Version {source.version_number} ·{" "}
            {source.page_number
              ? `Page ${source.page_number}`
              : `Section ${source.ordinal}`}
          </p>
          <p className="message-body">{source.content}</p>
          <button
            type="button"
            className="secondary"
            onClick={() => {
              setSource(null);
              setSelected("");
            }}
          >
            Close draft source
          </button>
        </article>
      )}
    </section>
  );
}

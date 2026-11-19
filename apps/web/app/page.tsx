"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight, ExternalLink } from "lucide-react";
import { Brand } from "@/components/brand";
import { ThemeToggle } from "@/components/theme-toggle";
import { authClient } from "@/lib/auth-client";
import { api, ApiError } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function enter() {
    setBusy(true);
    setError("");
    try {
      const session = await authClient.getSession();
      if (session.error)
        throw new Error("Sign-in is temporarily unavailable. Try again.");
      if (!session.data) {
        const result = await authClient.signIn.anonymous();
        if (result.error)
          throw new Error(
            result.error.message ?? "Could not start a demo session.",
          );
      }
      try {
        await api("demo", "POST");
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 410) throw error;
        const ended = await authClient.signOut();
        if (ended.error)
          throw new Error("Could not end the expired session. Try again.");
        const fresh = await authClient.signIn.anonymous();
        if (fresh.error)
          throw new Error("Could not start a fresh demo. Try again.");
        await api("demo", "POST");
      }
      router.push("/inbox");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Could not open the demo. Try again.",
      );
      setBusy(false);
    }
  }
  return (
    <>
      <header className="site-header">
        <Brand />
        <ThemeToggle />
      </header>
      <main id="main" className="entry">
        <section>
          <span className="eyebrow">A considered approach to support</span>
          <h1>
            Good answers
            <br />
            start with
            <br />
            solid ground.
          </h1>
          <p className="intro">
            An inbox built around the conversation, the evidence, and the person
            making the call.
          </p>
          <div className="entry-actions">
            <button className="primary" onClick={enter} disabled={busy}>
              {busy ? "Opening your workspace…" : "Explore the sample inbox"}
              <ArrowRight size={18} />
            </button>
          </div>
          <p className="small muted">
            Private demo session · Synthetic data · No email sent
          </p>
          {error && (
            <p role="alert" className="alert error">
              {error}
            </p>
          )}
          <a
            className="small"
            href="https://github.com/Kagerrak/resolvedesk"
            target="_blank"
            rel="noreferrer"
          >
            Read the project brief <ExternalLink size={12} />
          </a>
        </section>
        <aside className="entry-aside">
          <span className="eyebrow">Inside this early preview</span>
          <ol>
            <li>
              <div>
                <strong>Your own workspace</strong>
                <p className="muted">
                  A disposable inbox, isolated from every other visitor.
                </p>
              </div>
            </li>
            <li>
              <div>
                <strong>A real support conversation</strong>
                <p className="muted">
                  Read a persisted sample ticket from fictional software company
                  Meridian.
                </p>
              </div>
            </li>
            <li>
              <div>
                <strong>Handle with intention</strong>
                <p className="muted">
                  Save and revise drafts, inspect published evidence and review
                  handling history. Review and approve a simulated reply. No email is sent.
                </p>
              </div>
            </li>
          </ol>
          <p className="small muted">
            Fixture mode. No AI provider or Gmail connection is used. Sessions
            last up to one hour.
          </p>
        </aside>
      </main>
    </>
  );
}

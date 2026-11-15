"use client";
// Throwaway: three structurally distinct inbox directions on /inbox?variant=A|B|C.
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronDown,
  ChevronRight,
  Command,
  FileText,
  Inbox,
  Layers,
  MessageSquare,
  MoreHorizontal,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from "lucide-react";
import type { TicketDetail } from "@/lib/api";
import "./directions.css";

const names = { A: "Studio", B: "Editorial", C: "Command" };
type Variant = keyof typeof names;
const samples = [
  {
    name: "Alex Morgan",
    company: "Northstar",
    initials: "AM",
    subject: "Help restoring project access",
    snippet: "Can we restore access without admin permissions?",
    time: "12m",
    tag: "Access",
    color: "peach",
  },
  {
    name: "Jamie Lee",
    company: "Orbit Labs",
    initials: "JL",
    subject: "A question about our export",
    snippet: "Is there a way to include archived projects?",
    time: "28m",
    tag: "Product",
    color: "blue",
  },
  {
    name: "Sam Rivera",
    company: "Form & Field",
    initials: "SR",
    subject: "Inviting our external collaborators",
    snippet: "We’re bringing two contractors into the workspace.",
    time: "46m",
    tag: "Workspace",
    color: "lavender",
  },
  {
    name: "Taylor Chen",
    company: "Acme Studio",
    initials: "TC",
    subject: "Where can I find our invoices?",
    snippet: "I’m setting things up for our finance team.",
    time: "1h",
    tag: "Billing",
    color: "mint",
  },
];
export function DesignDirections({
  variant,
  ticket,
}: {
  variant: string;
  ticket: TicketDetail | null;
}) {
  const key: Variant = Object.hasOwn(names, variant)
    ? (variant as Variant)
    : "A";
  const router = useRouter();
  const [selected, setSelected] = useState(0);
  const [draft, setDraft] = useState(false);
  const [source, setSource] = useState(false);
  const [reviewed, setReviewed] = useState(false);
  const [query, setQuery] = useState("");
  const active = samples[selected];
  const subject = selected === 0 && ticket ? ticket.subject : active.subject;
  const message =
    selected === 0
      ? "Hi team,\n\nI changed a teammate’s role from Admin to Member this morning, and now they can’t open our quarterly planning project. They had access yesterday.\n\nCan we get them back in without giving them workspace-wide admin permissions?\n\nThanks, Alex"
      : "Hi team,\n\n" +
        active.snippet +
        " Could you point me in the right direction?\n\nThanks, " +
        active.name.split(" ")[0];
  const response =
    "Hi Alex,\n\nYou can restore access without making your teammate an Admin. Ask the project owner to add them directly to the quarterly planning project. Workspace roles and project membership are managed separately. [1]\n\nIf they still can’t open it, please send us the project name and we’ll help you check the next step.";
  function switchTo(next: Variant) {
    router.replace(`/inbox?variant=${next}`, { scroll: false });
  }
  useEffect(() => {
    function keyboard(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setSource(false);
        return;
      }
      if (
        (e.target as HTMLElement).closest(
          "input,textarea,select,[contenteditable]",
        )
      )
        return;
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      e.preventDefault();
      const keys: Variant[] = ["A", "B", "C"];
      const n = (keys.indexOf(key) + (e.key === "ArrowRight" ? 1 : 2)) % 3;
      router.replace(`/inbox?variant=${keys[n]}`, { scroll: false });
    }
    window.addEventListener("keydown", keyboard);
    return () => window.removeEventListener("keydown", keyboard);
  }, [key, router]);
  const visible = samples
    .map((s, i) => ({ ...s, index: i }))
    .filter((s) =>
      (s.name + s.subject).toLowerCase().includes(query.toLowerCase()),
    );
  function choose(i: number) {
    setSelected(i);
    setDraft(false);
    setReviewed(false);
  }
  const logo = (
    <span className="pd-logo">
      <Layers size={25} strokeWidth={2.3} />
      <strong>ResolveDesk</strong>
    </span>
  );
  const avatar = (initials: string, color: string) => (
    <span className={`pd-avatar ${color}`}>{initials}</span>
  );
  const search = (
    <label className="pd-search">
      <Search size={16} />
      <input
        aria-label="Search sample tickets"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search conversations"
      />
      <kbd>⌘ K</kbd>
    </label>
  );
  const queue = (
    <div className="pd-queue-items">
      {visible.map((s) => (
        <button
          key={s.index}
          onClick={() => choose(s.index)}
          className={`pd-ticket ${selected === s.index ? "chosen" : ""}`}
        >
          <div className="pd-ticket-top">
            {avatar(s.initials, s.color)}
            <span>
              <strong>{s.name}</strong>
              <small>{s.company}</small>
            </span>
            <time>{s.time}</time>
          </div>
          <h3>{s.subject}</h3>
          <p>{s.snippet}</p>
          <footer>
            <span className="pd-tag">{s.tag}</span>
            {s.index === 0 && <span className="pd-unread">Needs reply</span>}
          </footer>
        </button>
      ))}
      {!visible.length && (
        <p className="pd-empty">No matching sample conversations.</p>
      )}
    </div>
  );
  const evidence = (
    <section className="pd-evidence">
      <div className="pd-section-label">
        <BookOpen size={16} />
        KNOWLEDGE CONTEXT
      </div>
      <div className="pd-evidence-heading">
        <h3>A clear place to start.</h3>
        <span className="pd-dot" />
      </div>
      <p>Review the source before shaping your reply.</p>
      <button className="pd-source" onClick={() => setSource(true)}>
        <span className="pd-document-icon">
          <FileText size={20} />
        </span>
        <span>
          <strong>Project access & roles</strong>
          <small>Sample article · Version 3</small>
        </span>
        <ArrowUpRight size={16} />
      </button>
      <blockquote>
        “A workspace role does not replace a person’s membership in an
        individual project.”
      </blockquote>
      <span className="pd-evidence-note">
        <ShieldCheck size={14} />
        Illustrative evidence, not a retrieval result
      </span>
    </section>
  );
  const composer = (
    <section className="pd-composer">
      <header>
        <span>
          <MessageSquare size={16} />
          Reply to {active.name.split(" ")[0]}
        </span>
        <span className="pd-muted">Only you can approve</span>
      </header>
      {draft ? (
        <textarea
          aria-label="Edit simulated draft"
          defaultValue={
            selected === 0
              ? response
              : `Hi ${active.name.split(" ")[0]},\n\nThanks for reaching out. I’ll check the relevant guidance and get back to you.`
          }
        />
      ) : (
        <div className="pd-compose-empty">
          <p>A thoughtful answer starts here.</p>
          <span>Bring the conversation and the sources together.</span>
        </div>
      )}
      <footer>
        <span className="pd-muted">
          {reviewed
            ? "Review recorded locally. No email sent."
            : "Prototype · no provider calls"}
        </span>
        <button
          className="pd-primary"
          onClick={() => (draft ? setReviewed(true) : setDraft(true))}
        >
          {reviewed ? (
            <>
              <Check size={15} />
              Reviewed
            </>
          ) : draft ? (
            <>
              Review reply
              <ArrowRight size={15} />
            </>
          ) : (
            <>
              Try a sample draft
              <ArrowUpRight size={15} />
            </>
          )}
        </button>
      </footer>
    </section>
  );
  const conversation = (
    <article className="pd-conversation">
      <header className="pd-conversation-title">
        <div className="pd-breadcrumb">
          Conversations <ChevronRight size={13} />
          <span>RD-1042</span>
          <span className="pd-status">Open</span>
        </div>
        <h1>{subject}</h1>
        <div className="pd-conversation-meta">
          <span>{avatar("YO", "neutral")}Assigned to you</span>
          <span>Normal priority</span>
          <span>{active.tag}</span>
        </div>
      </header>
      <div className="pd-message">
        <header>
          {avatar(active.initials, active.color)}
          <div>
            <strong>{active.name}</strong>
            <span>
              {active.company} · {active.name.split(" ")[0].toLowerCase()}
              @example.com
            </span>
          </div>
          <time>Today, 10:42 AM</time>
        </header>
        <p>{message}</p>
      </div>
      {composer}
    </article>
  );
  const nav = (
    <nav aria-label="Prototype navigation">
      <span className="pd-nav-active">
        <Inbox size={19} />
        Inbox <b>4</b>
      </span>
      <span>
        <BookOpen size={19} />
        Knowledge
      </span>
      <span>
        <Layers size={19} />
        Activity
      </span>
      <span>
        <Settings size={19} />
        Settings
      </span>
    </nav>
  );
  return (
    <div className={`pd-root pd-${key}`}>
      <meta name="darkreader-lock" />
      <div className="pd-prototype-notice">
        <span>DESIGN EXPLORATION</span> Synthetic content & simulated
        interactions{" "}
        <span className="pd-notice-right">{names[key]} direction</span>
      </div>
      {key === "A" && (
        <div className="pd-studio">
          <aside className="pd-icon-rail">
            <Layers size={27} />
            <div>
              <span className="on">
                <Inbox size={21} />
              </span>
              <span>
                <BookOpen size={21} />
              </span>
              <span>
                <Layers size={21} />
              </span>
            </div>
            <span className="pd-rail-bottom">
              {avatar("YO", "neutral")}
              <Settings size={20} />
            </span>
          </aside>
          <section className="pd-studio-sidebar">
            <div className="pd-workspace">
              {logo}
              <ChevronDown size={16} />
            </div>
            <div className="pd-sidebar-heading">
              <h2>
                Inbox<span>4</span>
              </h2>
              <span className="pd-icon-button">
                <Plus size={18} />
              </span>
            </div>
            {search}
            <div className="pd-filters">
              <span className="selected">All conversations</span>
              <span>Assigned to me</span>
              <SlidersHorizontal size={15} />
            </div>
            {queue}
            <div className="pd-queue-footer">
              <span className="pd-dot" />
              Your workspace. Your pace.
            </div>
          </section>
          <div className="pd-studio-center">
            <header className="pd-topbar">
              <span>Support workspace</span>
              <div>
                <span className="pd-shortcut">
                  <Command size={13} />K
                </span>
                <span className="pd-top-avatar">YO</span>
              </div>
            </header>
            {conversation}
          </div>
          <aside className="pd-studio-context">
            <header>
              <span>Context</span>
              <MoreHorizontal size={18} />
            </header>
            {evidence}
            <div className="pd-customer">
              <span className="pd-section-label">ABOUT THE CUSTOMER</span>
              <h3>{active.company}</h3>
              <p>{active.name}</p>
              <dl>
                <dt>Contact</dt>
                <dd>{active.name.split(" ")[0].toLowerCase()}@example.com</dd>
                <dt>Conversation</dt>
                <dd>Email</dd>
              </dl>
            </div>
            <div className="pd-context-bottom">
              <span>01</span>
              <p>
                Evidence first.
                <br />
                Human judgment, always.
              </p>
            </div>
          </aside>
        </div>
      )}
      {key === "B" && (
        <div className="pd-editorial">
          <header className="pd-editorial-header">
            {logo}
            {nav}
            <span className="pd-top-avatar">YO</span>
          </header>
          <div className="pd-editorial-body">
            <aside className="pd-editorial-queue">
              <span className="pd-section-label">YOUR WORK, IN FOCUS</span>
              <h2>
                The inbox<span>.</span>
              </h2>
              <p>One good conversation at a time.</p>
              {search}
              {queue}
            </aside>
            <div className="pd-editorial-paper">
              <div className="pd-paper-index">
                <span>CONVERSATION 01 / 04</span>
                <span>MERIDIAN SUPPORT ↗</span>
              </div>
              {conversation}
            </div>
            <aside className="pd-editorial-margin">
              <span className="pd-margin-number">01—</span>
              {evidence}
              <div className="pd-editorial-note">
                <span>THE RESOLVEDESK APPROACH</span>
                <p>
                  Good support isn’t faster typing.
                  <br />
                  It’s a better starting point.
                </p>
              </div>
            </aside>
          </div>
        </div>
      )}
      {key === "C" && (
        <div className="pd-command">
          <header className="pd-command-header">
            {logo}
            <span className="pd-command-divider" />
            Meridian <ChevronDown size={14} />
            <div className="pd-command-header-right">
              <span>
                <span className="pd-dot" />
                Fixture workspace
              </span>
              <span className="pd-top-avatar">YO</span>
            </div>
          </header>
          <div className="pd-command-body">
            <aside className="pd-command-nav">
              {nav}
              <div className="pd-command-label">VIEWS</div>
              <span>↳ Unassigned</span>
              <span>↳ Awaiting review</span>
              <span>↳ Resolved</span>
              <div className="pd-command-bottom">
                <kbd>⌘</kbd>
                <p>
                  Keep your hands
                  <br />
                  on the keyboard.
                </p>
              </div>
            </aside>
            <div className="pd-command-content">
              <header className="pd-command-title">
                <div>
                  <span className="pd-section-label">SUPPORT OPERATIONS</span>
                  <h2>
                    All conversations <span>04</span>
                  </h2>
                </div>
                {search}
              </header>
              <div className="pd-table">
                <div className="pd-table-head">
                  <span>Customer</span>
                  <span>Conversation</span>
                  <span>Topic</span>
                  <span>Updated</span>
                </div>
                {visible.map((s) => (
                  <button
                    key={s.index}
                    className={selected === s.index ? "chosen" : ""}
                    onClick={() => choose(s.index)}
                  >
                    <span>
                      {avatar(s.initials, s.color)}
                      {s.name}
                    </span>
                    <strong>{s.subject}</strong>
                    <span className="pd-tag">{s.tag}</span>
                    <time>{s.time}</time>
                  </button>
                ))}
              </div>
              <div className="pd-command-detail">
                {conversation}
                <aside>{evidence}</aside>
              </div>
            </div>
          </div>
        </div>
      )}
      {source && (
        <div
          className="pd-source-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Sample knowledge source"
        >
          <div>
            <header>
              <span>SAMPLE KNOWLEDGE / 01</span>
              <button
                aria-label="Close source"
                onClick={() => setSource(false)}
              >
                <X size={20} />
              </button>
            </header>
            <FileText size={32} />
            <h2>Project access & roles</h2>
            <span className="pd-tag">Illustrative source · Version 3</span>
            <p>
              A workspace role does not replace a person’s membership in an
              individual project. A project owner can add a workspace Member
              directly to a project without granting workspace-wide Admin
              permissions.
            </p>
            <p className="pd-muted">
              This source is fictional prototype content. No retrieval,
              publication or citation validation has run.
            </p>
            <button className="pd-primary" onClick={() => setSource(false)}>
              Back to the conversation
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}
      <div className="pd-switcher" aria-label="Design direction switcher">
        <button
          aria-label="Previous direction"
          onClick={() => switchTo(key === "A" ? "C" : key === "B" ? "A" : "B")}
        >
          <ArrowLeft size={17} />
        </button>
        <div>
          <span>EXPLORE A DIRECTION</span>
          <div>
            {(["A", "B", "C"] as Variant[]).map((v) => (
              <button
                aria-pressed={key === v}
                key={v}
                onClick={() => switchTo(v)}
              >
                {v}
                <strong>{names[v]}</strong>
              </button>
            ))}
          </div>
        </div>
        <button
          aria-label="Next direction"
          onClick={() => switchTo(key === "A" ? "B" : key === "B" ? "C" : "A")}
        >
          <ArrowRight size={17} />
        </button>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Chart from "@/components/Chart";
import {
  createConversation,
  deleteConversation,
  getConversation,
  listConversations,
  streamChat,
  updateConversation,
  type AnswerEvent,
  type ConversationSummary,
  type ResultEvent,
} from "@/lib/api";

// One assistant turn, built up incrementally as SSE events arrive.
interface AssistantTurn {
  step: string | null;
  sql: string | null;
  result: ResultEvent | null;
  answer: string | null;
  sqlExplanation: string | null;
  error: string | null;
  done: boolean;
}

type Turn =
  | { role: "user"; question: string }
  | { role: "assistant"; data: AssistantTurn };

const EXAMPLES = [
  "Total revenue per product category, top 5",
  "Monthly revenue in 2017",
  "Top 10 cities by number of customers",
  "Average review score per product category",
];

// Render a KPI value: group big numbers with thousands separators.
function formatKpi(value: unknown): string {
  const n = Number(value);
  if (Number.isFinite(n)) {
    return n.toLocaleString("en-US", { maximumFractionDigits: 2 });
  }
  return String(value);
}

function emptyAssistant(): AssistantTurn {
  return {
    step: null,
    sql: null,
    result: null,
    answer: null,
    sqlExplanation: null,
    error: null,
    done: false,
  };
}

// A turn loaded from storage is finished: no live stepper.
function normalizeLoaded(turns: Turn[]): Turn[] {
  return turns.map((t) =>
    t.role === "assistant"
      ? { role: "assistant", data: { ...t.data, step: null, done: true } }
      : t,
  );
}

function titleFrom(turns: Turn[]): string {
  const firstUser = turns.find((t) => t.role === "user");
  const q = firstUser?.role === "user" ? firstUser.question : "New chat";
  return q.length > 60 ? q.slice(0, 57) + "…" : q;
}

export default function Home() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  // Refs mirror state so async code after streaming reads current values.
  const turnsRef = useRef<Turn[]>([]);
  const activeIdRef = useRef<string | null>(null);

  function commitTurns(next: Turn[]) {
    turnsRef.current = next;
    setTurns(next);
  }

  useEffect(() => {
    listConversations().then(setConversations).catch(() => {});
  }, []);

  async function refreshList() {
    try {
      setConversations(await listConversations());
    } catch {
      /* sidebar just stays as-is on failure */
    }
  }

  function patchAssistant(patch: Partial<AssistantTurn>) {
    const prev = turnsRef.current;
    const next = [...prev];
    for (let i = next.length - 1; i >= 0; i--) {
      const t = next[i];
      if (t.role === "assistant") {
        next[i] = { role: "assistant", data: { ...t.data, ...patch } };
        break;
      }
    }
    commitTurns(next);
    requestAnimationFrame(() =>
      bottomRef.current?.scrollIntoView({ behavior: "smooth" }),
    );
  }

  async function ask(question: string) {
    const q = question.trim();
    if (!q || busy) return;

    setInput("");
    setBusy(true);
    setSidebarOpen(false);
    commitTurns([
      ...turnsRef.current,
      { role: "user", question: q },
      { role: "assistant", data: emptyAssistant() },
    ]);

    await streamChat(q, {
      onStep: (e) => patchAssistant({ step: e.label }),
      onSql: (e) => patchAssistant({ sql: e.sql }),
      onResult: (e: ResultEvent) => patchAssistant({ result: e }),
      onAnswer: (e: AnswerEvent) =>
        patchAssistant({
          answer: e.answer,
          sqlExplanation: e.sql_explanation,
          error: e.error,
        }),
      onError: (message) => patchAssistant({ error: message }),
      onDone: () => patchAssistant({ step: null, done: true }),
    });

    // Persist the finished thread.
    const finished = turnsRef.current;
    try {
      if (activeIdRef.current) {
        await updateConversation(activeIdRef.current, finished);
      } else {
        const id = await createConversation(titleFrom(finished), finished);
        activeIdRef.current = id;
        setActiveId(id);
      }
      await refreshList();
    } catch {
      /* keep the thread on screen even if saving failed */
    }

    setBusy(false);
  }

  function newChat() {
    commitTurns([]);
    activeIdRef.current = null;
    setActiveId(null);
    setSidebarOpen(false);
  }

  async function loadConversation(id: string) {
    if (busy) return;
    try {
      const conv = await getConversation(id);
      commitTurns(normalizeLoaded(conv.messages as Turn[]));
      activeIdRef.current = id;
      setActiveId(id);
      setSidebarOpen(false);
    } catch {
      /* ignore load failure */
    }
  }

  async function removeConversation(id: string) {
    try {
      await deleteConversation(id);
      if (activeIdRef.current === id) newChat();
      await refreshList();
    } catch {
      /* ignore */
    }
  }

  const isEmpty = turns.length === 0;

  return (
    <div className="flex h-dvh">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        open={sidebarOpen}
        onNewChat={newChat}
        onSelect={loadConversation}
        onDelete={removeConversation}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Frosted, hairline header */}
        <header className="glass sticky top-0 z-10 border-b border-[var(--hairline)]">
          <div className="mx-auto flex max-w-3xl items-center gap-2.5 px-5 py-3.5">
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              className="grid h-8 w-8 place-items-center rounded-lg text-[var(--text-muted)] transition hover:bg-black/5 md:hidden"
              aria-label="Toggle history"
            >
              <MenuIcon />
            </button>
            <span className="text-[15px] font-semibold tracking-tight">
              T2SQL
            </span>
            <span className="text-[13px] text-[var(--text-muted)]">
              Olist analytics
            </span>
          </div>
        </header>

        <main className="scroll-quiet mx-auto w-full max-w-3xl flex-1 overflow-y-auto px-5">
          {isEmpty ? (
            <EmptyHero onPick={ask} disabled={busy} />
          ) : (
            <div className="space-y-6 py-6">
              {turns.map((turn, i) =>
                turn.role === "user" ? (
                  <UserBubble key={i} text={turn.question} />
                ) : (
                  <AssistantBubble key={i} data={turn.data} />
                ),
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </main>

        {/* Composer */}
        <div className="glass border-t border-[var(--hairline)]">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
            className="mx-auto flex max-w-3xl items-center gap-2 px-5 py-4"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about revenue, orders, customers…"
              className="h-11 flex-1 rounded-full border border-[var(--hairline)] bg-[var(--surface)] px-5 text-[15px] text-[var(--text)] shadow-sm outline-none transition focus:border-[var(--accent)] focus:ring-4 focus:ring-[#0071e3]/15"
              disabled={busy}
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              className="grid h-11 w-11 place-items-center rounded-full bg-[var(--accent)] text-white shadow-sm transition hover:bg-[var(--accent-strong)] disabled:opacity-30"
              aria-label="Send"
            >
              <ArrowUp />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function Sidebar({
  conversations,
  activeId,
  open,
  onNewChat,
  onSelect,
  onDelete,
  onClose,
}: {
  conversations: ConversationSummary[];
  activeId: string | null;
  open: boolean;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onClose: () => void;
}) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/20 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-[var(--hairline)] bg-[#f5f5f7] transition-transform md:static md:z-0 md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-3">
          <button
            onClick={onNewChat}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-[var(--hairline)] bg-[var(--surface)] px-3 py-2.5 text-[14px] font-medium shadow-sm transition hover:border-[var(--accent)]"
          >
            <PlusIcon />
            New chat
          </button>
        </div>

        <div className="scroll-quiet flex-1 overflow-y-auto px-2 pb-3">
          {conversations.length === 0 ? (
            <p className="px-3 py-4 text-[13px] text-[var(--text-muted)]">
              No conversations yet.
            </p>
          ) : (
            <ul className="space-y-0.5">
              {conversations.map((c) => (
                <li key={c.id} className="group relative">
                  <button
                    onClick={() => onSelect(c.id)}
                    className={`w-full truncate rounded-lg px-3 py-2 pr-8 text-left text-[13.5px] transition ${
                      c.id === activeId
                        ? "bg-[var(--surface)] font-medium shadow-sm"
                        : "text-[var(--text)] hover:bg-black/5"
                    }`}
                    title={c.title}
                  >
                    {c.title}
                  </button>
                  <button
                    onClick={() => onDelete(c.id)}
                    className="absolute right-1.5 top-1/2 hidden -translate-y-1/2 rounded-md p-1 text-[var(--text-muted)] transition hover:bg-black/10 hover:text-[#ff3b30] group-hover:block"
                    aria-label="Delete conversation"
                  >
                    <TrashIcon />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
    </>
  );
}

function EmptyHero({
  onPick,
  disabled,
}: {
  onPick: (q: string) => void;
  disabled: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="flex min-h-full flex-col items-center justify-center py-20 text-center"
    >
      <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
        What do you want to know?
      </h1>
      <p className="mt-3 max-w-md text-[15px] text-[var(--text-muted)]">
        Ask a question in plain English. T2SQL writes the SQL, runs it on the
        Olist e-commerce data, and explains its work.
      </p>
      <div className="mt-9 grid w-full max-w-xl grid-cols-1 gap-2.5 sm:grid-cols-2">
        {EXAMPLES.map((ex, i) => (
          <motion.button
            key={ex}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 + i * 0.06, duration: 0.4 }}
            onClick={() => onPick(ex)}
            disabled={disabled}
            className="rounded-2xl border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-left text-[14px] text-[var(--text)] shadow-sm transition hover:border-[var(--accent)] hover:shadow-[var(--shadow-soft)] disabled:opacity-40"
          >
            {ex}
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

function UserBubble({ text }: { text: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 400, damping: 34 }}
      className="flex justify-end"
    >
      <div className="max-w-[80%] rounded-3xl bg-[var(--accent)] px-4 py-2.5 text-[15px] text-white">
        {text}
      </div>
    </motion.div>
  );
}

function AssistantBubble({ data }: { data: AssistantTurn }) {
  const hasTable = !!data.result?.rows?.length;
  const chartType = data.result?.viz_spec?.chart_type;
  const isKpi = chartType === "kpi";
  const showChart = hasTable && chartType && chartType !== "table" && !isKpi;

  return (
    <div className="space-y-4">
      {/* Live stepper */}
      <AnimatePresence mode="wait">
        {!data.done && data.step && (
          <motion.div
            key={data.step}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.25 }}
            className="flex items-center gap-2.5 text-[14px] text-[var(--text-muted)]"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--accent)] opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--accent)]" />
            </span>
            {data.step}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Answer text */}
      {data.answer && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-[15px] leading-relaxed text-[var(--text)]"
        >
          {data.answer}
        </motion.p>
      )}

      {/* KPI — a single number gets its own quiet card */}
      {isKpi && (
        <motion.div
          initial={{ opacity: 0, y: 18, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 26 }}
          className="rounded-2xl border border-[var(--hairline)] bg-[var(--surface)] px-6 py-7 shadow-[var(--shadow-soft)]"
        >
          <div className="text-[13px] font-medium uppercase tracking-wide text-[var(--text-muted)]">
            {data.result!.viz_spec!.y}
          </div>
          <div className="mt-1 text-4xl font-semibold tabular-nums tracking-tight">
            {formatKpi(data.result!.rows![0][data.result!.viz_spec!.y as string])}
          </div>
        </motion.div>
      )}

      {/* Result card — rises into view */}
      {hasTable && !isKpi && (
        <motion.div
          initial={{ opacity: 0, y: 18, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 26 }}
          className="overflow-hidden rounded-2xl border border-[var(--hairline)] bg-[var(--surface)] shadow-[var(--shadow-soft)]"
        >
          {showChart && (
            <div className="border-b border-[var(--hairline)] p-3">
              <Chart
                columns={data.result!.columns ?? []}
                rows={data.result!.rows!}
                spec={data.result!.viz_spec!}
              />
            </div>
          )}
          <ResultTable
            columns={data.result!.columns ?? []}
            rows={data.result!.rows!}
          />
        </motion.div>
      )}

      {/* SQL + explanation */}
      {data.sql && (
        <details className="group rounded-2xl border border-[var(--hairline)] bg-[var(--surface)]">
          <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-[14px] font-medium text-[var(--text-muted)]">
            <Chevron />
            View SQL{data.sqlExplanation ? " & explanation" : ""}
          </summary>
          <div className="border-t border-[var(--hairline)] px-4 py-3">
            <pre className="overflow-x-auto rounded-xl bg-[#1d1d1f] p-3.5 text-[12.5px] leading-relaxed text-[#f5f5f7]">
              <code>{data.sql}</code>
            </pre>
            {data.sqlExplanation && (
              <p className="mt-3 text-[14px] leading-relaxed text-[var(--text-muted)]">
                {data.sqlExplanation}
              </p>
            )}
          </div>
        </details>
      )}

      {data.error && !data.answer && (
        <p className="text-[14px] text-[#ff3b30]">{data.error}</p>
      )}
    </div>
  );
}

function ResultTable({
  columns,
  rows,
}: {
  columns: string[];
  rows: Record<string, unknown>[];
}) {
  return (
    <div className="scroll-quiet max-h-80 overflow-auto">
      <table className="w-full border-collapse text-[14px]">
        <thead className="sticky top-0 bg-[var(--surface)]">
          <tr>
            {columns.map((c) => (
              <th
                key={c}
                className="border-b border-[var(--hairline)] px-4 py-2.5 text-left font-medium text-[var(--text-muted)]"
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-[#f5f5f7]">
              {columns.map((c) => (
                <td
                  key={c}
                  className="border-b border-[#ececed] px-4 py-2.5 tabular-nums text-[var(--text)]"
                >
                  {String(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ArrowUp() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 19V5M12 5l-6 6M12 5l6 6"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M4 6h16M4 12h16M4 18h16"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 5v14M5 12h14"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M4 7h16M9 7V5a1 1 0 011-1h4a1 1 0 011 1v2m2 0v12a1 1 0 01-1 1H7a1 1 0 01-1-1V7"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function Chevron() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
      className="transition-transform group-open:rotate-90"
    >
      <path
        d="M9 6l6 6-6 6"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

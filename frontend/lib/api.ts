// Client for the backend's POST /api/chat SSE stream.
//
// The browser's EventSource only does GET, but our endpoint is POST, so we
// read the response body as a stream and parse the SSE frames by hand.

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export type StepEvent = { node: string; label: string };
export type SqlEvent = { sql: string };
export type ResultEvent = {
  columns: string[] | null;
  rows: Record<string, unknown>[] | null;
  viz_spec: { chart_type: string; x?: string; y?: string } | null;
};
export type AnswerEvent = {
  answer: string | null;
  sql_explanation: string | null;
  error: string | null;
};

export interface ChatHandlers {
  onStep?: (e: StepEvent) => void;
  onSql?: (e: SqlEvent) => void;
  onResult?: (e: ResultEvent) => void;
  onAnswer?: (e: AnswerEvent) => void;
  onError?: (message: string) => void;
  onDone?: () => void;
}

// Parse one SSE frame ("event: x\ndata: {...}") and dispatch to a handler.
function dispatch(frame: string, handlers: ChatHandlers) {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length === 0) return;
  const data = JSON.parse(dataLines.join("\n"));

  switch (event) {
    case "step":
      handlers.onStep?.(data);
      break;
    case "sql":
      handlers.onSql?.(data);
      break;
    case "result":
      handlers.onResult?.(data);
      break;
    case "answer":
      handlers.onAnswer?.(data);
      break;
    case "error":
      handlers.onError?.(data.message ?? "Unknown error");
      break;
    case "done":
      handlers.onDone?.();
      break;
  }
}

// --- Conversation history (persisted in Postgres via the backend) ---

export interface ConversationSummary {
  id: string;
  title: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: unknown[];
  created_at: string;
  updated_at: string;
}

export async function listConversations(): Promise<ConversationSummary[]> {
  const resp = await fetch(`${API_BASE}/api/conversations`);
  if (!resp.ok) return [];
  return resp.json();
}

export async function getConversation(id: string): Promise<Conversation> {
  const resp = await fetch(`${API_BASE}/api/conversations/${id}`);
  if (!resp.ok) throw new Error(`Failed to load conversation ${id}`);
  return resp.json();
}

export async function createConversation(
  title: string,
  messages: unknown[],
): Promise<string> {
  const resp = await fetch(`${API_BASE}/api/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, messages }),
  });
  const data = await resp.json();
  return data.id;
}

export async function updateConversation(
  id: string,
  messages: unknown[],
): Promise<void> {
  await fetch(`${API_BASE}/api/conversations/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
}

export async function deleteConversation(id: string): Promise<void> {
  await fetch(`${API_BASE}/api/conversations/${id}`, { method: "DELETE" });
}

export async function streamChat(
  question: string,
  handlers: ChatHandlers,
): Promise<void> {
  const resp = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!resp.ok || !resp.body) {
    handlers.onError?.(`Request failed: ${resp.status}`);
    return;
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    // Normalize CRLF -> LF: sse-starlette separates frames with \r\n\r\n.
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

    // SSE frames are separated by a blank line.
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      if (frame.trim()) dispatch(frame, handlers);
    }
  }
}

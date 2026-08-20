import { useEffect, useState } from "react";
import {
  Bot, Send, Copy, Check, RefreshCw, AlertTriangle, XCircle,
  History, Sparkles, Database, Clock, Table as TableIcon,
} from "lucide-react";
import { aiSearchService } from "@/services/ai-search.service";
import { usePersistedState } from "@/hooks/usePersistedState";
import type { AIQueryHistoryItem, AISchemaInfo, NLQueryResponse } from "@/types";

export default function AISearchPage() {
  const [info, setInfo] = useState<AISchemaInfo | null>(null);
  const [question, setQuestion] = usePersistedState("ai_search:question", "");
  const [asking, setAsking] = useState(false);
  const [result, setResult] = usePersistedState<NLQueryResponse | null>("ai_search:result", null);
  const [history, setHistory] = useState<AIQueryHistoryItem[]>([]);
  const [copied, setCopied] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    aiSearchService.getInfo().then(setInfo).catch(() => setInfo(null));
    loadHistory();
  }, []);

  const loadHistory = () => {
    aiSearchService.history(15).then(setHistory).catch(() => {});
  };

  const ask = async (q?: string) => {
    const finalQuestion = (q ?? question).trim();
    if (!finalQuestion || asking) return;
    setAsking(true);
    setResult(null);
    try {
      const res = await aiSearchService.ask(finalQuestion);
      setResult(res);
      loadHistory();
    } catch (e: any) {
      setResult({
        id: "error",
        question: finalQuestion,
        generated_sql: null,
        status: "error",
        columns: [],
        rows: [],
        row_count: 0,
        execution_ms: null,
        truncated: false,
        explanation: null,
        error_message: extractErrorMessage(e),
        ai_provider: null,
      });
    } finally {
      setAsking(false);
    }
  };

  const copySql = () => {
    if (!result?.generated_sql) return;
    navigator.clipboard.writeText(result.generated_sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Bot className="w-6 h-6 text-[#003087]" />
            AI Natural Language Search
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Ask a question in plain English — the AI generates a read-only SQL query, runs it
            against your master data, and shows you exactly what it ran.
          </p>
        </div>
        {result && (
          <button
            onClick={() => { setResult(null); setQuestion(""); }}
            disabled={asking}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-destructive border border-border hover:border-destructive/40 rounded-lg px-3 py-1.5 transition disabled:opacity-50 flex-shrink-0"
          >
            Clear
          </button>
        )}
      </div>

      {info && !info.ai_configured && (
        <div className="rounded-lg bg-amber-50 text-amber-800 text-sm px-4 py-3 border border-amber-200 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>
            AI Search isn't configured yet on this server. An administrator needs to set an
            OPENAI_API_KEY (or point AI_PROVIDER at a local Ollama instance) before questions
            can be answered.
          </span>
        </div>
      )}

      {/* Ask box */}
      <div className="rounded-xl border border-border bg-card p-5 space-y-4">
        <div className="flex items-center gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask()}
            placeholder="e.g. How many faculty members are there in each department?"
            className="flex-1 rounded-lg border border-input bg-background text-sm px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#003087]"
            disabled={asking}
          />
          <button
            onClick={() => ask()}
            disabled={asking || !question.trim()}
            className="flex items-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white font-medium px-4 py-2.5 text-sm transition disabled:opacity-50 flex-shrink-0"
          >
            {asking ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {asking ? "Thinking…" : "Ask"}
          </button>
          <button
            onClick={() => setShowHistory((s) => !s)}
            className="flex items-center gap-2 rounded-lg border border-border hover:bg-muted/50 font-medium px-3 py-2.5 text-sm transition flex-shrink-0"
          >
            <History className="w-4 h-4" />
          </button>
        </div>

        {/* Example chips */}
        {info?.example_questions && info.example_questions.length > 0 && !result && (
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-muted-foreground flex items-center gap-1 mr-1">
              <Sparkles className="w-3.5 h-3.5" /> Try:
            </span>
            {info.example_questions.slice(0, 5).map((q) => (
              <button
                key={q}
                onClick={() => { setQuestion(q); ask(q); }}
                className="text-xs px-3 py-1.5 rounded-full bg-muted hover:bg-muted/70 text-foreground transition"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* History panel */}
      {showHistory && (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center gap-2 text-sm font-medium">
            <History className="w-4 h-4 text-[#003087]" /> Recent Queries
          </div>
          <div className="divide-y divide-border max-h-64 overflow-y-auto">
            {history.length === 0 && (
              <p className="p-4 text-sm text-muted-foreground">No queries yet.</p>
            )}
            {history.map((h) => (
              <button
                key={h.id}
                onClick={() => { setQuestion(h.question); ask(h.question); setShowHistory(false); }}
                className="w-full text-left p-3 hover:bg-muted/20 transition flex items-center gap-3"
              >
                <StatusDot status={h.status} />
                <span className="text-sm text-foreground truncate flex-1">{h.question}</span>
                {h.row_count !== null && (
                  <span className="text-xs text-muted-foreground flex-shrink-0">{h.row_count} rows</span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="space-y-4">
          {result.status !== "success" && (
            <div className="rounded-lg bg-red-50 text-red-700 text-sm px-4 py-3 border border-red-200 flex items-start gap-2">
              <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium mb-0.5">
                  {result.status === "blocked" ? "Query blocked by safety guard" : "Query failed"}
                </p>
                <p>{result.error_message}</p>
              </div>
            </div>
          )}

          {/* Generated SQL */}
          {result.generated_sql && (
            <div className="rounded-xl border border-border bg-card overflow-hidden">
              <div className="px-4 py-2.5 border-b border-border flex items-center justify-between bg-muted/30">
                <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5" /> Generated SQL
                </span>
                <button
                  onClick={copySql}
                  className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
              <pre className="p-4 text-xs font-mono text-foreground overflow-x-auto whitespace-pre-wrap">
                {result.generated_sql}
              </pre>
            </div>
          )}

          {/* Result table */}
          {result.status === "success" && (
            <div className="rounded-xl border border-border bg-card overflow-hidden">
              <div className="px-4 py-2.5 border-b border-border flex items-center justify-between bg-muted/30">
                <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                  <TableIcon className="w-3.5 h-3.5" /> Results — {result.row_count} row{result.row_count === 1 ? "" : "s"}
                  {result.truncated && " (capped)"}
                </span>
                {result.execution_ms !== null && (
                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> {result.execution_ms} ms
                  </span>
                )}
              </div>

              {result.rows.length === 0 ? (
                <p className="p-6 text-sm text-muted-foreground text-center">
                  The query ran successfully but returned no rows.
                </p>
              ) : (
                <div className="overflow-x-auto max-h-[500px]">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-muted/50">
                      <tr>
                        {result.columns.map((col) => (
                          <th key={col} className="text-left font-medium text-muted-foreground px-4 py-2 whitespace-nowrap">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {result.rows.map((row, idx) => (
                        <tr key={idx} className="hover:bg-muted/20">
                          {result.columns.map((col) => (
                            <td key={col} className="px-4 py-2 text-foreground whitespace-nowrap">
                              {formatCell(row[col])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!result && !asking && (
        <div className="rounded-xl border border-dashed border-border p-10 text-center text-muted-foreground">
          Ask a question above, or pick one of the examples, to see the generated SQL and results here.
        </div>
      )}
    </div>
  );
}
function extractErrorMessage(e: any): string {
  const detail = e?.response?.data?.detail;
  if (!detail) return "Something went wrong while asking the AI.";
  if (typeof detail === "string") return detail;
  // FastAPI validation errors come back as an array of {type, loc, msg, ...}
  if (Array.isArray(detail)) {
    return detail.map((d) => d?.msg || JSON.stringify(d)).join("; ");
  }
  return typeof detail === "object" ? JSON.stringify(detail) : String(detail);
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "success" ? "bg-green-500" : status === "blocked" ? "bg-amber-500" : "bg-red-500";
  return <span className={`w-2 h-2 rounded-full flex-shrink-0 ${color}`} />;
}

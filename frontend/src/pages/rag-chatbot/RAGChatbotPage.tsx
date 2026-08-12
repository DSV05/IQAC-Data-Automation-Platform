import { useEffect, useRef, useState } from "react";
import {
  MessageSquareText, Send, Upload, FileText, Trash2, RefreshCw,
  CheckCircle2, XCircle, Clock, ChevronDown, ChevronUp, AlertTriangle,
} from "lucide-react";
import { ragService } from "@/services/rag.service";
import type {
  RAGChatResponse, RAGDocumentItem, RAGDocumentType, RAGInfo,
} from "@/types";

const DOC_TYPE_LABELS: Record<RAGDocumentType, string> = {
  naac_ssr: "NAAC SSR",
  annual_report: "Annual Report",
  nirf_report: "NIRF Report",
  policy: "Policy Document",
  other: "Other",
};

interface ChatTurn {
  question: string;
  response: RAGChatResponse | null;
  loading: boolean;
}

export default function RAGChatbotPage() {
  const [info, setInfo] = useState<RAGInfo | null>(null);
  const [documents, setDocuments] = useState<RAGDocumentItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadDocType, setUploadDocType] = useState<RAGDocumentType>("other");
  const [uploadYear, setUploadYear] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [question, setQuestion] = useState("");
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [expandedSources, setExpandedSources] = useState<Record<number, boolean>>({});
  const asking = turns.length > 0 && turns[turns.length - 1].loading;

  useEffect(() => {
    loadInfo();
    loadDocuments();
  }, []);

  // Poll while any document is still processing
  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === "processing");
    if (!hasProcessing) return;
    const interval = setInterval(loadDocuments, 3000);
    return () => clearInterval(interval);
  }, [documents]);

  const loadInfo = () => ragService.getInfo().then(setInfo).catch(() => {});
  const loadDocuments = () => ragService.listDocuments().then(setDocuments).catch(() => {});

  const handleUpload = async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file || uploading) return;
    setUploading(true);
    try {
      await ragService.uploadDocument(
        file,
        uploadTitle.trim() || file.name,
        uploadDocType,
        uploadYear.trim() || undefined
      );
      setUploadTitle("");
      setUploadYear("");
      setUploadDocType("other");
      if (fileInputRef.current) fileInputRef.current.value = "";
      loadDocuments();
      loadInfo();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remove this document from the chatbot's knowledge base?")) return;
    await ragService.deleteDocument(id);
    loadDocuments();
    loadInfo();
  };

  const handleAsk = async () => {
    const q = question.trim();
    if (!q || asking) return;
    setQuestion("");
    setTurns((prev) => [...prev, { question: q, response: null, loading: true }]);

    try {
      const res = await ragService.ask(q, selectedDocId || undefined);
      setTurns((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = { question: q, response: res, loading: false };
        return copy;
      });
    } catch (e: any) {
      setTurns((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = {
          question: q,
          loading: false,
          response: {
            id: "error",
            question: q,
            answer: null,
            sources: [],
            status: "error",
            execution_ms: null,
            error_message: extractErrorMessage(e),
            ai_provider: null,
          },
        };
        return copy;
      });
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <MessageSquareText className="w-6 h-6 text-[#003087]" />
          RAG Chatbot — Document Q&A
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload NAAC SSR, Annual Reports, or NIRF submissions, then ask questions in plain
          English — answers are grounded in your documents and cite the exact page they came from.
        </p>
      </div>

      {info && !info.ai_configured && (
        <div className="rounded-lg bg-amber-50 text-amber-800 text-sm px-4 py-3 border border-amber-200 flex items-start gap-2 mb-6">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>
            AI features aren't configured on this server yet. Ask your administrator to set
            OPENAI_API_KEY (or configure Ollama) before uploading or chatting.
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: document library */}
        <div className="lg:col-span-1 space-y-4">
          <div className="rounded-xl border border-border bg-card p-4 space-y-3">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
              <Upload className="w-4 h-4" /> Upload Document
            </h2>
            <input
              type="file"
              accept=".pdf"
              ref={fileInputRef}
              className="text-xs w-full file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-[#003087] file:text-white file:text-xs"
            />
            <input
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              placeholder="Title (e.g. NAAC SSR 2023-24)"
              className="w-full rounded-md border border-input bg-background text-xs px-3 py-2"
            />
            <div className="flex gap-2">
              <select
                value={uploadDocType}
                onChange={(e) => setUploadDocType(e.target.value as RAGDocumentType)}
                className="flex-1 rounded-md border border-input bg-background text-xs px-2 py-2"
              >
                {Object.entries(DOC_TYPE_LABELS).map(([val, label]) => (
                  <option key={val} value={val}>{label}</option>
                ))}
              </select>
              <input
                value={uploadYear}
                onChange={(e) => setUploadYear(e.target.value)}
                placeholder="2023-24"
                className="w-24 rounded-md border border-input bg-background text-xs px-2 py-2"
              />
            </div>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white font-medium px-3 py-2 text-xs transition disabled:opacity-50"
            >
              {uploading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
              {uploading ? "Uploading…" : "Upload PDF"}
            </button>
          </div>

          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-4 py-3 border-b border-border flex items-center justify-between">
              <span className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                <FileText className="w-4 h-4" /> Documents
                {info && ` (${info.ready_document_count}/${info.document_count} ready)`}
              </span>
            </div>
            <div className="divide-y divide-border max-h-[420px] overflow-y-auto">
              {documents.length === 0 && (
                <p className="p-4 text-xs text-muted-foreground">No documents uploaded yet.</p>
              )}
              {documents.map((doc) => (
                <div key={doc.id} className="p-3 flex items-start gap-2">
                  <StatusIcon status={doc.status} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-foreground truncate">{doc.title}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {DOC_TYPE_LABELS[doc.doc_type]}
                      {doc.academic_year && ` · ${doc.academic_year}`}
                      {doc.status === "ready" && doc.chunk_count != null && ` · ${doc.chunk_count} chunks`}
                    </p>
                    {doc.status === "failed" && doc.error_message && (
                      <p className="text-[11px] text-red-600 mt-0.5">{doc.error_message}</p>
                    )}
                  </div>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="text-muted-foreground hover:text-red-600 transition flex-shrink-0"
                    title="Remove document"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: chat */}
        <div className="lg:col-span-2 flex flex-col rounded-xl border border-border bg-card overflow-hidden" style={{ minHeight: 560 }}>
          <div className="px-4 py-3 border-b border-border flex items-center gap-2">
            <span className="text-sm font-medium text-muted-foreground">Scope:</span>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="text-xs rounded-md border border-input bg-background px-2 py-1.5"
            >
              <option value="">All documents</option>
              {documents.filter((d) => d.status === "ready").map((d) => (
                <option key={d.id} value={d.id}>{d.title}</option>
              ))}
            </select>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-5">
            {turns.length === 0 && (
              <div className="h-full flex items-center justify-center text-center text-muted-foreground text-sm px-8">
                Ask a question about your uploaded documents — e.g. "What were the key SWOC
                findings in the NAAC SSR?" or "Summarize the placement highlights from the
                Annual Report."
              </div>
            )}
            {turns.map((turn, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex justify-end">
                  <div className="bg-[#003087] text-white rounded-2xl rounded-tr-sm px-4 py-2 text-sm max-w-[80%]">
                    {turn.question}
                  </div>
                </div>
                {turn.loading ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Thinking…
                  </div>
                ) : turn.response?.status === "error" ? (
                  <div className="flex justify-start">
                    <div className="bg-red-50 border border-red-200 text-red-700 rounded-2xl rounded-tl-sm px-4 py-2 text-sm max-w-[85%]">
                      {turn.response.error_message}
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-start">
                    <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-3 text-sm max-w-[85%] space-y-2">
                      <p className="whitespace-pre-wrap text-foreground">{turn.response?.answer}</p>
                      {turn.response && turn.response.sources.length > 0 && (
                        <div>
                          <button
                            onClick={() =>
                              setExpandedSources((prev) => ({ ...prev, [idx]: !prev[idx] }))
                            }
                            className="text-xs text-[#003087] flex items-center gap-1 font-medium"
                          >
                            {turn.response.sources.length} source{turn.response.sources.length === 1 ? "" : "s"}
                            {expandedSources[idx] ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>
                          {expandedSources[idx] && (
                            <div className="mt-2 space-y-2">
                              {turn.response.sources.map((src, i) => (
                                <div key={i} className="text-xs bg-background rounded-lg border border-border p-2">
                                  <p className="font-medium text-foreground">
                                    [{i + 1}] {src.title} — page {src.page}
                                  </p>
                                  <p className="text-muted-foreground mt-0.5 line-clamp-3">{src.snippet}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="border-t border-border p-3 flex items-center gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAsk()}
              placeholder="Ask a question about your uploaded documents…"
              disabled={asking}
              className="flex-1 rounded-lg border border-input bg-background text-sm px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#003087]"
            />
            <button
              onClick={handleAsk}
              disabled={asking || !question.trim()}
              className="flex items-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white font-medium px-4 py-2.5 text-sm transition disabled:opacity-50 flex-shrink-0"
            >
              {asking ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === "ready") return <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />;
  if (status === "failed") return <XCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />;
  return <Clock className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5 animate-pulse" />;
}

function extractErrorMessage(e: any): string {
  const detail = e?.response?.data?.detail;
  if (!detail) return "Something went wrong while asking the AI.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d?.msg || JSON.stringify(d)).join("; ");
  }
  return typeof detail === "object" ? JSON.stringify(detail) : String(detail);
}

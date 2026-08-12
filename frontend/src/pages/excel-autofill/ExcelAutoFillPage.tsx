import { useEffect, useRef, useState } from "react";
import {
  Wand2, Upload, FileSpreadsheet, Trash2, RefreshCw, Download,
  ListChecks, Copy, Check, AlertTriangle, History,
} from "lucide-react";
import { excelTemplatesService } from "@/services/excel-templates.service";
import type { ExcelTemplateItem, FillHistoryItem, TokenInfo } from "@/types";

export default function ExcelAutoFillPage() {
  const [templates, setTemplates] = useState<ExcelTemplateItem[]>([]);
  const [tokens, setTokens] = useState<TokenInfo[]>([]);
  const [history, setHistory] = useState<FillHistoryItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [academicYear, setAcademicYear] = useState("2023-24");
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [filling, setFilling] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const [tokenFilter, setTokenFilter] = useState("");

  useEffect(() => {
    loadTemplates();
    loadHistory();
    excelTemplatesService.getTokens(academicYear).then(setTokens).catch(() => {});
  }, []);

  const loadTemplates = () => excelTemplatesService.listTemplates().then((ts) => {
    setTemplates(ts);
    if (!selectedTemplateId && ts.length > 0) setSelectedTemplateId(ts[0].id);
  }).catch(() => {});

  const loadHistory = () => excelTemplatesService.fillHistory(15).then(setHistory).catch(() => {});

  const handleUpload = async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file || uploading) return;
    setUploading(true);
    try {
      await excelTemplatesService.uploadTemplate(file, uploadTitle.trim() || file.name);
      setUploadTitle("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      loadTemplates();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Upload failed. Only .xlsx files are supported.");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remove this template?")) return;
    await excelTemplatesService.deleteTemplate(id);
    loadTemplates();
  };

  const handleFill = async () => {
    if (!selectedTemplateId || filling) return;
    setFilling(true);
    try {
      await excelTemplatesService.fillAndDownload(selectedTemplateId, academicYear.trim() || undefined);
      loadHistory();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Fill failed. Please try again.");
    } finally {
      setFilling(false);
    }
  };

  const copyToken = (token: string) => {
    navigator.clipboard.writeText(token);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 1200);
  };

  const filteredTokens = tokens.filter((t) =>
    t.token.toLowerCase().includes(tokenFilter.toLowerCase())
  );

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Wand2 className="w-6 h-6 text-[#003087]" />
          Excel Auto-Fill
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload an official template with <code className="text-xs bg-muted px-1 py-0.5 rounded">{"{{tokens}}"}</code> in
          its cells — the system fills them with live data from your master tables and gives you back
          the same file, fully formatted.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Upload + template library */}
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-card p-4 space-y-3">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
              <Upload className="w-4 h-4" /> Upload Template
            </h2>
            <input
              type="file"
              accept=".xlsx"
              ref={fileInputRef}
              className="text-xs w-full file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-[#003087] file:text-white file:text-xs"
            />
            <input
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              placeholder="Title (e.g. AISHE Official Template 2023-24)"
              className="w-full rounded-md border border-input bg-background text-xs px-3 py-2"
            />
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white font-medium px-3 py-2 text-xs transition disabled:opacity-50"
            >
              {uploading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
              {uploading ? "Uploading…" : "Upload .xlsx Template"}
            </button>
            <p className="text-[11px] text-muted-foreground flex items-start gap-1">
              <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
              Only .xlsx is supported. Put tokens like {"{{nirf.faculty_total}}"} directly into cells first.
            </p>
          </div>

          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-4 py-3 border-b border-border">
              <span className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                <FileSpreadsheet className="w-4 h-4" /> Templates ({templates.length})
              </span>
            </div>
            <div className="divide-y divide-border max-h-64 overflow-y-auto">
              {templates.length === 0 && (
                <p className="p-4 text-xs text-muted-foreground">No templates uploaded yet.</p>
              )}
              {templates.map((t) => (
                <label
                  key={t.id}
                  className="p-3 flex items-start gap-2 cursor-pointer hover:bg-muted/20 transition"
                >
                  <input
                    type="radio"
                    name="template"
                    checked={selectedTemplateId === t.id}
                    onChange={() => setSelectedTemplateId(t.id)}
                    className="mt-1"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-foreground truncate">{t.title}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {t.sheet_count} sheet{t.sheet_count === 1 ? "" : "s"} · {t.token_count} token{t.token_count === 1 ? "" : "s"}
                    </p>
                  </div>
                  <button
                    onClick={(e) => { e.preventDefault(); handleDelete(t.id); }}
                    className="text-muted-foreground hover:text-red-600 transition flex-shrink-0"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </label>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-4 space-y-3">
            <h2 className="text-sm font-semibold text-foreground">Fill &amp; Download</h2>
            <input
              value={academicYear}
              onChange={(e) => setAcademicYear(e.target.value)}
              placeholder="2023-24 (leave blank for all years)"
              className="w-full rounded-md border border-input bg-background text-xs px-3 py-2"
            />
            <button
              onClick={handleFill}
              disabled={filling || !selectedTemplateId}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#C9A227] hover:bg-[#B08F1E] text-white font-medium px-3 py-2 text-xs transition disabled:opacity-50"
            >
              {filling ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
              {filling ? "Filling…" : "Fill Selected Template & Download"}
            </button>
          </div>
        </div>

        {/* Token reference */}
        <div className="rounded-xl border border-border bg-card overflow-hidden flex flex-col" style={{ maxHeight: 620 }}>
          <div className="px-4 py-3 border-b border-border space-y-2">
            <span className="text-sm font-semibold text-foreground flex items-center gap-1.5">
              <ListChecks className="w-4 h-4" /> Available Tokens ({tokens.length})
            </span>
            <input
              value={tokenFilter}
              onChange={(e) => setTokenFilter(e.target.value)}
              placeholder="Filter tokens…"
              className="w-full rounded-md border border-input bg-background text-xs px-3 py-1.5"
            />
          </div>
          <div className="overflow-y-auto flex-1 divide-y divide-border">
            {filteredTokens.map((t) => (
              <div key={t.token} className="px-4 py-2 flex items-center gap-2">
                <code className="text-xs font-mono text-[#003087] flex-1 truncate">{t.token}</code>
                <span className="text-[11px] text-muted-foreground truncate max-w-[100px]">
                  {String(t.sample_value)}
                </span>
                <button
                  onClick={() => copyToken(t.token)}
                  className="text-muted-foreground hover:text-foreground transition flex-shrink-0"
                >
                  {copiedToken === t.token ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center gap-1.5">
          <History className="w-4 h-4 text-[#003087]" />
          <span className="text-sm font-semibold text-foreground">Recent Fills</span>
        </div>
        <div className="divide-y divide-border max-h-56 overflow-y-auto">
          {history.length === 0 && (
            <p className="p-4 text-sm text-muted-foreground">No fills generated yet.</p>
          )}
          {history.map((h) => (
            <div key={h.id} className="px-4 py-2.5 flex items-center gap-3 text-sm">
              <span className="text-xs text-muted-foreground">{h.academic_year || "All years"}</span>
              <span className="text-xs font-medium text-green-700">{h.tokens_filled} filled</span>
              {h.tokens_missing && h.tokens_missing.length > 0 && (
                <span className="text-xs font-medium text-amber-600">{h.tokens_missing.length} missing</span>
              )}
              <span className="text-xs text-muted-foreground ml-auto">
                {new Date(h.created_at).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

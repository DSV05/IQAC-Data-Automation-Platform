import { useEffect, useState } from "react";
import {
  Workflow as WorkflowIcon, Send, CheckCircle2, XCircle, Lock, Clock,
  History, RefreshCw, ChevronDown, ChevronUp, FileEdit,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { authService } from "@/services/auth.service";
import { workflowService } from "@/services/workflow.service";
import { canApproveWorkflow } from "@/utils/roles";
import type { SubmissionItem, WorkflowHistoryItem, WorkflowStatus } from "@/types";

interface DepartmentOption {
  id: string;
  name: string;
}

const STATUS_STYLES: Record<WorkflowStatus, { label: string; className: string; icon: typeof Clock }> = {
  draft: { label: "Draft", className: "bg-gray-100 text-gray-700", icon: FileEdit },
  submitted: { label: "Awaiting Review", className: "bg-amber-100 text-amber-700", icon: Clock },
  approved: { label: "Approved", className: "bg-green-100 text-green-700", icon: CheckCircle2 },
  rejected: { label: "Rejected", className: "bg-red-100 text-red-700", icon: XCircle },
  locked: { label: "Locked", className: "bg-slate-800 text-white", icon: Lock },
};

function StatusBadge({ status }: { status: WorkflowStatus }) {
  const s = STATUS_STYLES[status];
  const Icon = s.icon;
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${s.className}`}>
      <Icon className="w-3 h-3" /> {s.label}
    </span>
  );
}

export default function WorkflowPage() {
  const { user } = useAuth();
  const isReviewer = user ? canApproveWorkflow(user.role) : false;

  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [submissions, setSubmissions] = useState<SubmissionItem[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [history, setHistory] = useState<Record<string, WorkflowHistoryItem[]>>({});

  const [submitDeptId, setSubmitDeptId] = useState("");
  const [submitYear, setSubmitYear] = useState("2023-24");
  const [submitComments, setSubmitComments] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [reviewingId, setReviewingId] = useState<string | null>(null);
  const [reviewComments, setReviewComments] = useState("");
  const [statusFilter, setStatusFilter] = useState<WorkflowStatus | "">(isReviewer ? "submitted" : "");

  useEffect(() => {
    authService.listDepartments().then(setDepartments).catch(() => {});
  }, []);

  useEffect(() => {
    if (!user) return;
    if (!isReviewer && user.department_id) setSubmitDeptId(user.department_id);
    loadSubmissions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, statusFilter]);

  const loadSubmissions = () => {
    workflowService
      .list({ status: statusFilter || undefined })
      .then(setSubmissions)
      .catch(() => {});
  };

  const toggleHistory = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    if (!history[id]) {
      const h = await workflowService.getHistory(id);
      setHistory((prev) => ({ ...prev, [id]: h }));
    }
  };

  const handleSubmit = async () => {
    if (!submitDeptId || !submitYear.trim() || submitting) return;
    setSubmitting(true);
    try {
      await workflowService.submit(submitDeptId, submitYear.trim(), submitComments.trim() || undefined);
      setSubmitComments("");
      loadSubmissions();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Submission failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleReview = async (id: string, decision: "approve" | "reject") => {
    try {
      await workflowService.review(id, decision, reviewComments.trim() || undefined);
      setReviewingId(null);
      setReviewComments("");
      loadSubmissions();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Review failed.");
    }
  };

  const handleLock = async (id: string) => {
    if (!confirm("Lock this submission? It can no longer be revised after locking.")) return;
    try {
      await workflowService.lock(id);
      loadSubmissions();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Lock failed.");
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <WorkflowIcon className="w-6 h-6 text-[#003087]" />
          Workflow &amp; Approvals
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Submit → Department resubmission (if rejected) → IQAC review → Lock.
          Every step is recorded in the version history below.
        </p>
      </div>

      {/* Submit panel — visible to anyone with workflow:submit (department_coordinator+) */}
      <div className="rounded-xl border border-border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
          <Send className="w-4 h-4" /> Submit for Review
        </h2>
        <div className="flex flex-wrap gap-2">
          <select
            value={submitDeptId}
            onChange={(e) => setSubmitDeptId(e.target.value)}
            disabled={!isReviewer && !!user?.department_id}
            className="rounded-lg border border-input bg-background text-sm px-3 py-2 disabled:opacity-60"
          >
            <option value="">Select department…</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          <input
            value={submitYear}
            onChange={(e) => setSubmitYear(e.target.value)}
            placeholder="2023-24"
            className="w-32 rounded-lg border border-input bg-background text-sm px-3 py-2"
          />
          <input
            value={submitComments}
            onChange={(e) => setSubmitComments(e.target.value)}
            placeholder="Optional comments for the reviewer…"
            className="flex-1 min-w-[200px] rounded-lg border border-input bg-background text-sm px-3 py-2"
          />
          <button
            onClick={handleSubmit}
            disabled={submitting || !submitDeptId || !submitYear.trim()}
            className="flex items-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white font-medium px-4 py-2 text-sm transition disabled:opacity-50"
          >
            {submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Submit
          </button>
        </div>
      </div>

      {/* Submissions list */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <span className="text-sm font-semibold text-foreground">
            {isReviewer ? "All Submissions" : "Your Department's Submissions"}
          </span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as WorkflowStatus | "")}
            className="text-xs rounded-md border border-input bg-background px-2 py-1.5"
          >
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="submitted">Awaiting Review</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="locked">Locked</option>
          </select>
        </div>

        <div className="divide-y divide-border">
          {submissions.length === 0 && (
            <p className="p-4 text-sm text-muted-foreground">No submissions found.</p>
          )}
          {submissions.map((s) => (
            <div key={s.id}>
              <div className="p-4 flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-foreground">{s.department_name}</span>
                    <span className="text-xs text-muted-foreground">{s.academic_year}</span>
                    <span className="text-xs text-muted-foreground">v{s.version}</span>
                    <StatusBadge status={s.status} />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {s.submitted_by_name && `Submitted by ${s.submitted_by_name}`}
                    {s.reviewed_by_name && ` · Reviewed by ${s.reviewed_by_name}`}
                    {s.locked_by_name && ` · Locked by ${s.locked_by_name}`}
                  </p>
                  {s.review_comments && (
                    <p className="text-xs text-muted-foreground mt-1 italic">"{s.review_comments}"</p>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {isReviewer && s.status === "submitted" && (
                    <button
                      onClick={() => setReviewingId(reviewingId === s.id ? null : s.id)}
                      className="text-xs font-medium text-[#003087] border border-[#003087] rounded-lg px-3 py-1.5 hover:bg-[#003087] hover:text-white transition"
                    >
                      Review
                    </button>
                  )}
                  {isReviewer && s.status === "approved" && (
                    <button
                      onClick={() => handleLock(s.id)}
                      className="flex items-center gap-1 text-xs font-medium bg-slate-800 hover:bg-slate-900 text-white rounded-lg px-3 py-1.5 transition"
                    >
                      <Lock className="w-3 h-3" /> Lock
                    </button>
                  )}
                  <button
                    onClick={() => toggleHistory(s.id)}
                    className="text-muted-foreground hover:text-foreground transition"
                    title="View history"
                  >
                    {expandedId === s.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {reviewingId === s.id && (
                <div className="px-4 pb-4 flex items-center gap-2 bg-muted/20">
                  <input
                    value={reviewComments}
                    onChange={(e) => setReviewComments(e.target.value)}
                    placeholder="Comments (required for rejection, optional for approval)…"
                    className="flex-1 rounded-lg border border-input bg-background text-xs px-3 py-2"
                  />
                  <button
                    onClick={() => handleReview(s.id, "approve")}
                    className="flex items-center gap-1 text-xs font-medium bg-green-600 hover:bg-green-700 text-white rounded-lg px-3 py-2 transition"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" /> Approve
                  </button>
                  <button
                    onClick={() => handleReview(s.id, "reject")}
                    className="flex items-center gap-1 text-xs font-medium bg-red-600 hover:bg-red-700 text-white rounded-lg px-3 py-2 transition"
                  >
                    <XCircle className="w-3.5 h-3.5" /> Reject
                  </button>
                </div>
              )}

              {expandedId === s.id && (
                <div className="px-4 pb-4 bg-muted/10">
                  <p className="text-xs font-medium text-muted-foreground flex items-center gap-1 mb-2">
                    <History className="w-3.5 h-3.5" /> Version History
                  </p>
                  <div className="space-y-1.5">
                    {(history[s.id] || []).map((h) => (
                      <div key={h.id} className="text-xs text-muted-foreground flex items-start gap-2">
                        <span className="font-mono text-[10px] bg-muted rounded px-1.5 py-0.5 flex-shrink-0">
                          v{h.version}
                        </span>
                        <span>
                          {h.from_status ? `${STATUS_STYLES[h.from_status].label} → ` : ""}
                          <strong>{STATUS_STYLES[h.to_status].label}</strong>
                          {h.actor_name && ` by ${h.actor_name}`}
                          {h.comments && ` — "${h.comments}"`}
                          <span className="ml-1 text-[10px]">
                            ({new Date(h.created_at).toLocaleString()})
                          </span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

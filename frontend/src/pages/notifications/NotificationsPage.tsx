import { useEffect, useState } from "react";
import {
  Bell, CheckCheck, Calendar, Trash2, Plus, RefreshCw, PlayCircle, AlertTriangle,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { authService } from "@/services/auth.service";
import { notificationsService } from "@/services/notifications.service";
import { canApproveWorkflow } from "@/utils/roles";
import type { DeadlineItem, NotificationItem } from "@/types";

interface DepartmentOption {
  id: string;
  name: string;
}

const TYPE_DOT: Record<string, string> = {
  missing_data: "bg-amber-500",
  deadline_reminder: "bg-red-500",
  workflow_submitted: "bg-blue-500",
  workflow_approved: "bg-green-500",
  workflow_rejected: "bg-red-500",
  workflow_locked: "bg-slate-600",
  general: "bg-gray-400",
};

export default function NotificationsPage() {
  const { user } = useAuth();
  const isAdmin = user ? canApproveWorkflow(user.role) : false;

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [deadlines, setDeadlines] = useState<DeadlineItem[]>([]);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);

  const [newTitle, setNewTitle] = useState("");
  const [newDueDate, setNewDueDate] = useState("");
  const [newAcademicYear, setNewAcademicYear] = useState("2023-24");
  const [newDeptId, setNewDeptId] = useState("");
  const [newReminderDays, setNewReminderDays] = useState(3);
  const [creating, setCreating] = useState(false);
  const [runningChecks, setRunningChecks] = useState(false);
  const [checkResult, setCheckResult] = useState<string | null>(null);

  useEffect(() => {
    loadNotifications();
    loadDeadlines();
    if (isAdmin) authService.listDepartments().then(setDepartments).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadNotifications = () => notificationsService.list(false, 50).then(setNotifications).catch(() => {});
  const loadDeadlines = () => notificationsService.listDeadlines().then(setDeadlines).catch(() => {});

  const handleMarkAllRead = async () => {
    await notificationsService.markAllRead();
    loadNotifications();
  };

  const handleCreateDeadline = async () => {
    if (!newTitle.trim() || !newDueDate || creating) return;
    setCreating(true);
    try {
      await notificationsService.createDeadline({
        title: newTitle.trim(),
        due_date: newDueDate,
        academic_year: newAcademicYear.trim() || undefined,
        department_id: newDeptId || undefined,
        reminder_days_before: newReminderDays,
      });
      setNewTitle("");
      setNewDueDate("");
      setNewDeptId("");
      loadDeadlines();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Failed to create deadline.");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteDeadline = async (id: string) => {
    if (!confirm("Delete this deadline?")) return;
    await notificationsService.deleteDeadline(id);
    loadDeadlines();
  };

  const handleRunChecks = async () => {
    setRunningChecks(true);
    setCheckResult(null);
    try {
      const res = await notificationsService.runChecksNow();
      setCheckResult(
        `Checked ${res.academic_year_checked}: ${res.deadlines_triggered} deadline reminder(s) sent, ` +
        `${res.departments_flagged_missing_data} department(s) flagged for missing data.`
      );
      loadNotifications();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Failed to run checks.");
    } finally {
      setRunningChecks(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Bell className="w-6 h-6 text-[#003087]" />
          Notifications &amp; Deadlines
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Missing-data alerts, deadline reminders, and workflow approval updates all land here.
        </p>
      </div>

      {isAdmin && (
        <div className="rounded-xl border border-border bg-card p-4 space-y-3">
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
            <Calendar className="w-4 h-4" /> Create a Deadline
          </h2>
          <div className="flex flex-wrap gap-2">
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Title (e.g. NAAC SSR Data Entry Deadline)"
              className="flex-1 min-w-[220px] rounded-lg border border-input bg-background text-sm px-3 py-2"
            />
            <input
              type="date"
              value={newDueDate}
              onChange={(e) => setNewDueDate(e.target.value)}
              className="rounded-lg border border-input bg-background text-sm px-3 py-2"
            />
            <input
              value={newAcademicYear}
              onChange={(e) => setNewAcademicYear(e.target.value)}
              placeholder="2023-24"
              className="w-24 rounded-lg border border-input bg-background text-sm px-3 py-2"
            />
            <select
              value={newDeptId}
              onChange={(e) => setNewDeptId(e.target.value)}
              className="rounded-lg border border-input bg-background text-sm px-3 py-2"
            >
              <option value="">All departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
            <input
              type="number"
              min={0}
              max={90}
              value={newReminderDays}
              onChange={(e) => setNewReminderDays(Number(e.target.value))}
              title="Remind this many days before the due date"
              className="w-20 rounded-lg border border-input bg-background text-sm px-3 py-2"
            />
            <button
              onClick={handleCreateDeadline}
              disabled={creating || !newTitle.trim() || !newDueDate}
              className="flex items-center gap-1.5 rounded-lg bg-[#003087] hover:bg-[#002266] text-white font-medium px-4 py-2 text-sm transition disabled:opacity-50"
            >
              {creating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Add
            </button>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Reminder days = how many days before the due date to start notifying. Leave department blank to remind
            all department coordinators and IQAC admins.
          </p>

          <div className="pt-2 border-t border-border flex items-center gap-3">
            <button
              onClick={handleRunChecks}
              disabled={runningChecks}
              className="flex items-center gap-1.5 text-xs font-medium border border-[#003087] text-[#003087] rounded-lg px-3 py-1.5 hover:bg-[#003087] hover:text-white transition disabled:opacity-50"
            >
              {runningChecks ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <PlayCircle className="w-3.5 h-3.5" />}
              Run checks now
            </button>
            <span className="text-[11px] text-muted-foreground">
              (Otherwise these run automatically on a fixed interval — see NOTIFICATIONS_CHECK_INTERVAL_HOURS)
            </span>
          </div>
          {checkResult && (
            <p className="text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
              {checkResult}
            </p>
          )}
        </div>
      )}

      {/* Deadlines list */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <span className="text-sm font-semibold text-foreground flex items-center gap-1.5">
            <Calendar className="w-4 h-4" /> Upcoming Deadlines
          </span>
        </div>
        <div className="divide-y divide-border max-h-56 overflow-y-auto">
          {deadlines.length === 0 && (
            <p className="p-4 text-sm text-muted-foreground">No deadlines set.</p>
          )}
          {deadlines.map((d) => (
            <div key={d.id} className="px-4 py-2.5 flex items-center gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">{d.title}</p>
                <p className="text-xs text-muted-foreground">
                  Due {new Date(d.due_date).toLocaleDateString()}
                  {d.department_name ? ` · ${d.department_name}` : " · All departments"}
                  {d.academic_year ? ` · ${d.academic_year}` : ""}
                </p>
              </div>
              {isAdmin && (
                <button
                  onClick={() => handleDeleteDeadline(d.id)}
                  className="text-muted-foreground hover:text-red-600 transition flex-shrink-0"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Notifications list */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <span className="text-sm font-semibold text-foreground">All Notifications</span>
          <button
            onClick={handleMarkAllRead}
            className="text-xs text-[#003087] flex items-center gap-1 hover:underline"
          >
            <CheckCheck className="w-3.5 h-3.5" /> Mark all read
          </button>
        </div>
        <div className="divide-y divide-border max-h-[500px] overflow-y-auto">
          {notifications.length === 0 && (
            <p className="p-4 text-sm text-muted-foreground text-center flex items-center gap-2 justify-center">
              <AlertTriangle className="w-4 h-4" /> No notifications yet.
            </p>
          )}
          {notifications.map((n) => (
            <div key={n.id} className={`px-4 py-3 flex gap-2 ${n.is_read ? "opacity-60" : ""}`}>
              <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${TYPE_DOT[n.type] || "bg-gray-400"}`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">{n.title}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{n.message}</p>
                <p className="text-[11px] text-muted-foreground mt-1">
                  {new Date(n.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

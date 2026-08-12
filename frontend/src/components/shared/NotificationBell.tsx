import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, CheckCheck } from "lucide-react";
import { notificationsService } from "@/services/notifications.service";
import type { NotificationItem } from "@/types";

const TYPE_DOT: Record<string, string> = {
  missing_data: "bg-amber-500",
  deadline_reminder: "bg-red-500",
  workflow_submitted: "bg-blue-500",
  workflow_approved: "bg-green-500",
  workflow_rejected: "bg-red-500",
  workflow_locked: "bg-slate-600",
  general: "bg-gray-400",
};

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function NotificationBell() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const ref = useRef<HTMLDivElement>(null);

  const loadUnreadCount = () => notificationsService.unreadCount().then(setUnreadCount).catch(() => {});

  useEffect(() => {
    loadUnreadCount();
    const interval = setInterval(loadUnreadCount, 60000); // poll every minute
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggleOpen = () => {
    const next = !open;
    setOpen(next);
    if (next) {
      notificationsService.list(false, 10).then(setNotifications).catch(() => {});
    }
  };

  const handleNotificationClick = async (n: NotificationItem) => {
    if (!n.is_read) {
      await notificationsService.markRead(n.id);
      loadUnreadCount();
      setNotifications((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
    }
    if (n.link) {
      setOpen(false);
      navigate(n.link);
    }
  };

  const handleMarkAllRead = async () => {
    await notificationsService.markAllRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={toggleOpen}
        className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground transition relative"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span className="absolute top-0.5 right-0.5 min-w-[14px] h-[14px] px-0.5 rounded-full bg-destructive text-white text-[9px] leading-[14px] text-center font-medium">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 max-h-96 overflow-hidden flex flex-col rounded-xl border border-border bg-card shadow-lg z-50">
          <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-[#003087] flex items-center gap-1 hover:underline"
              >
                <CheckCheck className="w-3 h-3" /> Mark all read
              </button>
            )}
          </div>
          <div className="overflow-y-auto flex-1">
            {notifications.length === 0 && (
              <p className="p-4 text-sm text-muted-foreground text-center">No notifications yet.</p>
            )}
            {notifications.map((n) => (
              <button
                key={n.id}
                onClick={() => handleNotificationClick(n)}
                className={`w-full text-left px-4 py-3 border-b border-border last:border-0 hover:bg-muted/30 transition flex gap-2 ${
                  n.is_read ? "opacity-60" : ""
                }`}
              >
                <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${TYPE_DOT[n.type] || "bg-gray-400"}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-foreground truncate">{n.title}</p>
                  <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">{n.message}</p>
                  <p className="text-[10px] text-muted-foreground mt-1">{timeAgo(n.created_at)}</p>
                </div>
              </button>
            ))}
          </div>
          <button
            onClick={() => { setOpen(false); navigate("/notifications"); }}
            className="px-4 py-2.5 border-t border-border text-xs font-medium text-[#003087] hover:bg-muted/30 transition text-center"
          >
            View all &amp; manage deadlines
          </button>
        </div>
      )}
    </div>
  );
}

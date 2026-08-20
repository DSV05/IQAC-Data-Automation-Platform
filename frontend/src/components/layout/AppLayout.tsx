import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Users, Upload, FileBarChart, Bot, Search,
  Settings, Bell, ChevronDown, LogOut, Moon, Sun, Menu, X,
  Database, ClipboardCheck, Workflow, ShieldCheck, MessageSquareText, Wand2,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useAuthStore } from "@/store/auth.store";
import { RoleBadge } from "@/components/shared/RoleBadge";
import { NotificationBell } from "@/components/shared/NotificationBell";
import { hasMinimumRole } from "@/utils/roles";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, permission: null },
  { to: "/master-data", label: "Master Data", icon: Database, permission: null },
  { to: "/uploads", label: "Data Upload", icon: Upload, permission: null },
  { to: "/validation", label: "Data Validation", icon: ShieldCheck, permission: null },
  { to: "/reports", label: "Reports", icon: FileBarChart, permission: null },
  { to: "/excel-autofill", label: "Excel Auto-Fill", icon: Wand2, permission: null },
  { to: "/ai-search", label: "AI Search", icon: Bot, permission: null },
  { to: "/rag-chatbot", label: "RAG Chatbot", icon: MessageSquareText, permission: null },
  { to: "/search", label: "Global Search", icon: Search, permission: null },
  { to: "/workflow", label: "Workflow", icon: Workflow, permission: "department_coordinator" as const },
  { to: "/notifications", label: "Notifications", icon: Bell, permission: null },
  { to: "/users", label: "Users", icon: Users, permission: "iqac_admin" as const },
  { to: "/audit", label: "Audit Logs", icon: ClipboardCheck, permission: "iqac_admin" as const },
];

export default function AppLayout() {
  const { logout } = useAuth();
  const user = useAuthStore((s) => s.user);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  const toggleDark = () => {
    setDarkMode((d) => !d);
    document.documentElement.classList.toggle("dark");
  };

  const visibleNav = NAV_ITEMS.filter(
    (item) => !item.permission || (user && hasMinimumRole(user.role, item.permission))
  );

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "w-60" : "w-20"
        } flex-shrink-0 flex flex-col bg-[#003087] transition-all duration-300 overflow-hidden`}
      >
                    {/* Logo */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10">
              <div className="w-16 h-16 flex items-center justify-center flex-shrink-0">
                <img
                  src="/IQAC_Logo.png"
                  alt="IQAC Ganpat University"
                  className="w-16 h-16 object-contain"
                />
              </div>

              {sidebarOpen && (
                <div className="min-w-0">
                  <div className="text-white font-bold text-sm leading-tight truncate">
                    IQAC Platform
                  </div>
                  <div className="text-white/50 text-xs truncate">
                    Ganpat University
                  </div>
                </div>
              )}
            </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto">
          {visibleNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-white/20 text-white font-medium"
                    : "text-white/60 hover:bg-white/10 hover:text-white"
                }`
              }
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span className="truncate">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* User info */}
        {sidebarOpen && user && (
          <div className="px-3 py-3 border-t border-white/10">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-white font-bold text-xs flex-shrink-0">
                {user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-white text-xs font-medium truncate">{user.full_name}</div>
                <RoleBadge role={user.role} size="sm" />
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-14 flex items-center justify-between px-4 border-b border-border bg-background flex-shrink-0">
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground transition"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleDark}
              className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground transition"
              aria-label="Toggle dark mode"
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <NotificationBell />
            <button
              onClick={() => logout()}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-muted text-sm text-muted-foreground hover:text-foreground transition"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

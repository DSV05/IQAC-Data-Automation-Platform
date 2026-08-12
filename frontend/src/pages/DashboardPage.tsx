import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  PointElement, LineElement, ArcElement, Tooltip, Legend,
} from "chart.js";
import { Bar, Line, Doughnut } from "react-chartjs-2";
import {
  Users, GraduationCap, BookOpen, Award, Briefcase, Building2,
  Leaf, Target, RefreshCw, TrendingUp,
} from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import { dashboardService } from "@/services/dashboard.service";

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Tooltip, Legend);

const ACADEMIC_YEARS = ["2024-25", "2023-24", "2022-23", "2021-22", "2020-21"];
const BRAND = "#003087";
const GOLD = "#C9A227";

const SDG_LABELS: Record<number, string> = {
  1: "No Poverty", 2: "Zero Hunger", 3: "Good Health", 4: "Quality Education",
  5: "Gender Equality", 6: "Clean Water", 7: "Affordable Energy", 8: "Decent Work",
  9: "Industry & Innovation", 10: "Reduced Inequality", 11: "Sustainable Cities",
  12: "Responsible Consumption", 13: "Climate Action", 14: "Life Below Water",
  15: "Life on Land", 16: "Peace & Justice", 17: "Partnerships",
};

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const [academicYear, setAcademicYear] = useState("2024-25");

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["dashboard-summary", academicYear],
    queryFn: () => dashboardService.getSummary(academicYear),
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Welcome back, {user?.full_name?.split(" ")[0]}
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            IQAC Data Automation Platform — Ganpat University
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={academicYear}
            onChange={(e) => setAcademicYear(e.target.value)}
            className="rounded-lg border border-input bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#003087]"
          >
            {ACADEMIC_YEARS.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <button
            onClick={() => refetch()}
            className="p-2 rounded-lg border border-border hover:bg-muted/50 transition"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-muted/30 animate-pulse" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 p-6 text-sm">
          Couldn't load dashboard data for {academicYear}. Make sure master data has been
          entered for this academic year.
        </div>
      )}

      {data && (
        <>
          {/* KPI cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard icon={<Users className="w-4 h-4" />} label="Total Faculty" value={data.kpis.total_faculty} color="blue" />
            <KpiCard icon={<GraduationCap className="w-4 h-4" />} label="Total Students" value={data.kpis.total_students} color="green" />
            <KpiCard icon={<TrendingUp className="w-4 h-4" />} label="Student : Faculty" value={data.kpis.student_faculty_ratio ? `${data.kpis.student_faculty_ratio} : 1` : "—"} color="purple" />
            <KpiCard icon={<Briefcase className="w-4 h-4" />} label="Placement Rate" value={`${data.kpis.placement_rate_pct}%`} color="amber" />
            <KpiCard icon={<Briefcase className="w-4 h-4" />} label="Avg Package (LPA)" value={data.kpis.avg_package_lpa} color="amber" />
            <KpiCard icon={<BookOpen className="w-4 h-4" />} label="Publications" value={data.kpis.total_publications} color="purple" />
            <KpiCard icon={<Award className="w-4 h-4" />} label="Patents" value={data.kpis.total_patents} color="blue" />
            <KpiCard icon={<Building2 className="w-4 h-4" />} label="Departments" value={data.kpis.total_departments} color="green" />
          </div>

          {/* Year-over-year + Dept breakdown */}
          <div className="grid lg:grid-cols-2 gap-4">
            <ChartCard title="Year-over-Year Growth">
              <Line
                data={{
                  labels: data.year_over_year.faculty.map((r: any) => r.academic_year),
                  datasets: [
                    {
                      label: "Faculty",
                      data: data.year_over_year.faculty.map((r: any) => r.count),
                      borderColor: BRAND, backgroundColor: BRAND, tension: 0.3,
                    },
                    {
                      label: "Students",
                      data: data.year_over_year.students.map((r: any) => r.count),
                      borderColor: GOLD, backgroundColor: GOLD, tension: 0.3,
                    },
                  ],
                }}
                options={{ responsive: true, plugins: { legend: { position: "bottom" } } }}
              />
            </ChartCard>

            <ChartCard title="Faculty by Department">
              <Bar
                data={{
                  labels: data.dept_breakdown.faculty_by_department.map((r: any) => r.department),
                  datasets: [{
                    label: "Faculty",
                    data: data.dept_breakdown.faculty_by_department.map((r: any) => r.count),
                    backgroundColor: BRAND,
                    borderRadius: 4,
                  }],
                }}
                options={{
                  responsive: true,
                  plugins: { legend: { display: false } },
                  indexAxis: "y" as const,
                }}
              />
            </ChartCard>
          </div>

          <div className="grid lg:grid-cols-2 gap-4">
            <ChartCard title="Students by Department">
              <Bar
                data={{
                  labels: data.dept_breakdown.students_by_department.map((r: any) => r.department),
                  datasets: [{
                    label: "Students",
                    data: data.dept_breakdown.students_by_department.map((r: any) => r.count),
                    backgroundColor: GOLD,
                    borderRadius: 4,
                  }],
                }}
                options={{ responsive: true, plugins: { legend: { display: false } }, indexAxis: "y" as const }}
              />
            </ChartCard>

            <ChartCard title="Publications by Department">
              <Bar
                data={{
                  labels: data.dept_breakdown.publications_by_department.map((r: any) => r.department),
                  datasets: [{
                    label: "Publications",
                    data: data.dept_breakdown.publications_by_department.map((r: any) => r.count),
                    backgroundColor: "#7c3aed",
                    borderRadius: 4,
                  }],
                }}
                options={{ responsive: true, plugins: { legend: { display: false } }, indexAxis: "y" as const }}
              />
            </ChartCard>
          </div>

          {/* Energy + SDG widgets */}
          <div className="grid lg:grid-cols-3 gap-4">
            <ChartCard title="Energy Mix" icon={<Leaf className="w-4 h-4 text-green-600" />}>
              <Doughnut
                data={{
                  labels: ["Grid Electricity", "Solar", "Wind"],
                  datasets: [{
                    data: [data.energy.electricity_kwh, data.energy.solar_kwh, data.energy.wind_kwh],
                    backgroundColor: ["#94a3b8", "#facc15", "#38bdf8"],
                  }],
                }}
                options={{ responsive: true, plugins: { legend: { position: "bottom" } } }}
              />
              <p className="text-center text-sm text-muted-foreground mt-3">
                <span className="font-semibold text-green-700">{data.energy.renewable_pct}%</span> renewable energy mix
              </p>
            </ChartCard>

            <ChartCard title="GHG Emissions Trend (tCO2e)" icon={<Leaf className="w-4 h-4 text-green-600" />}>
              <Line
                data={{
                  labels: data.energy.ghg_trend.map((r: any) => r.academic_year),
                  datasets: [{
                    label: "Total tCO2e",
                    data: data.energy.ghg_trend.map((r: any) => r.total_tco2e),
                    borderColor: "#dc2626", backgroundColor: "#dc2626", tension: 0.3,
                  }],
                }}
                options={{ responsive: true, plugins: { legend: { display: false } } }}
              />
            </ChartCard>

            <ChartCard title="SDG Activities by Goal" icon={<Target className="w-4 h-4 text-[#003087]" />}>
              {data.sdg.activities_by_goal.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-10">
                  No SDG activities recorded for {academicYear} yet.
                </p>
              ) : (
                <Bar
                  data={{
                    labels: data.sdg.activities_by_goal.map((r: any) => `SDG ${r.sdg_goal}`),
                    datasets: [{
                      label: "Activities",
                      data: data.sdg.activities_by_goal.map((r: any) => r.count),
                      backgroundColor: "#0d9488",
                      borderRadius: 4,
                    }],
                  }}
                  options={{
                    responsive: true,
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        callbacks: {
                          title: (items) => {
                            const goal = data.sdg.activities_by_goal[items[0].dataIndex]?.sdg_goal;
                            return `SDG ${goal}: ${SDG_LABELS[goal] || ""}`;
                          },
                        },
                      },
                    },
                  }}
                />
              )}
            </ChartCard>
          </div>
        </>
      )}
    </div>
  );
}

const KPI_COLORS: Record<string, string> = {
  blue: "bg-blue-50 text-blue-700 border-blue-100",
  green: "bg-green-50 text-green-700 border-green-100",
  purple: "bg-purple-50 text-purple-700 border-purple-100",
  amber: "bg-amber-50 text-amber-700 border-amber-100",
};

function KpiCard({
  icon, label, value, color,
}: { icon: React.ReactNode; label: string; value: string | number; color: string }) {
  return (
    <div className={`rounded-xl border p-5 ${KPI_COLORS[color]}`}>
      <div className="flex items-center gap-2 opacity-80 mb-1">{icon}</div>
      <div className="text-2xl font-bold">{value ?? "—"}</div>
      <div className="text-sm font-medium mt-1 opacity-80">{label}</div>
    </div>
  );
}

function ChartCard({
  title, icon, children,
}: { title: string; icon?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h2 className="font-semibold text-foreground flex items-center gap-2 mb-4">
        {icon}
        {title}
      </h2>
      {children}
    </div>
  );
}

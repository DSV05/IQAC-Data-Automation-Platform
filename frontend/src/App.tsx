import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import AppLayout from "@/components/layout/AppLayout";
import LoginPage from "@/pages/auth/LoginPage";
import ForgotPasswordPage from "@/pages/auth/ForgotPasswordPage";
import ResetPasswordPage from "@/pages/auth/ResetPasswordPage";
import DashboardPage from "@/pages/DashboardPage";
import UsersPage from "@/pages/auth/UsersPage";
import MasterDataPage from "@/pages/master/MasterDataPage";
import UploadsPage from "@/pages/uploads/UploadsPage";
import ValidationPage from "@/pages/validation/ValidationPage";
import AISearchPage from "@/pages/ai-search/AISearchPage";
import RAGChatbotPage from "@/pages/rag-chatbot/RAGChatbotPage";
import ReportsPage from "@/pages/reports/ReportsPage";
import ExcelAutoFillPage from "@/pages/excel-autofill/ExcelAutoFillPage";
import WorkflowPage from "@/pages/workflow/WorkflowPage";
import NotificationsPage from "@/pages/notifications/NotificationsPage";
import AuditLogsPage from "@/pages/audit/AuditLogsPage";
import GlobalSearchPage from "@/pages/search/GlobalSearchPage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 1000 * 60 * 5, retry: 1 } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/master-data" element={<MasterDataPage />} />
            <Route path="/uploads" element={<UploadsPage />} />
            <Route path="/validation" element={<ValidationPage />} />
            <Route path="/users" element={<ProtectedRoute minimumRole="iqac_admin"><UsersPage /></ProtectedRoute>} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/excel-autofill" element={<ExcelAutoFillPage />} />
            <Route path="/ai-search" element={<AISearchPage />} />
            <Route path="/rag-chatbot" element={<RAGChatbotPage />} />
            <Route path="/search" element={<GlobalSearchPage />} /> 
            <Route path="/workflow" element={<WorkflowPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/audit" element={<AuditLogsPage />} />
          </Route>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

import { useForm } from "react-hook-form";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useState } from "react";
import { Eye, EyeOff, Loader2, CheckCircle } from "lucide-react";
import { authService } from "@/services/auth.service";

interface FormData {
  new_password: string;
  confirm_password: string;
}

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token") ?? "";
  const [showPw, setShowPw] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } =
    useForm<FormData>();

  const onSubmit = async (data: FormData) => {
    setError(null);
    try {
      await authService.resetPassword(token, data.new_password);
      setDone(true);
      setTimeout(() => navigate("/login"), 2500);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Reset failed. The link may have expired.");
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="text-center space-y-3">
          <p className="text-destructive font-medium">Invalid reset link.</p>
          <Link to="/forgot-password" className="text-sm text-[#003087] hover:underline">
            Request a new one
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Set new password</h2>
          <p className="mt-1 text-muted-foreground text-sm">
            Your new password must be at least 8 characters with one uppercase letter and one number.
          </p>
        </div>

        {done ? (
          <div className="rounded-xl border border-border bg-muted/50 p-6 text-center space-y-3">
            <CheckCircle className="w-10 h-10 text-green-600 mx-auto" />
            <p className="font-medium">Password updated!</p>
            <p className="text-sm text-muted-foreground">Redirecting to login…</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {error && (
              <div className="rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-foreground">New password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  placeholder="••••••••"
                  className={`w-full rounded-lg border px-3.5 py-2.5 pr-10 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-[#003087] transition ${errors.new_password ? "border-destructive" : "border-input"}`}
                  {...register("new_password", {
                    required: "Required",
                    minLength: { value: 8, message: "Min 8 characters" },
                    validate: {
                      hasUpper: v => /[A-Z]/.test(v) || "Must contain uppercase letter",
                      hasDigit: v => /\d/.test(v) || "Must contain a number",
                    },
                  })}
                />
                <button type="button" onClick={() => setShowPw(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.new_password && <p className="text-xs text-destructive">{errors.new_password.message}</p>}
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-foreground">Confirm password</label>
              <input
                type={showPw ? "text" : "password"}
                placeholder="••••••••"
                className={`w-full rounded-lg border px-3.5 py-2.5 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-[#003087] transition ${errors.confirm_password ? "border-destructive" : "border-input"}`}
                {...register("confirm_password", {
                  required: "Required",
                  validate: v => v === watch("new_password") || "Passwords do not match",
                })}
              />
              {errors.confirm_password && <p className="text-xs text-destructive">{errors.confirm_password.message}</p>}
            </div>

            <button
              type="submit" disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white font-medium py-2.5 text-sm transition disabled:opacity-60"
            >
              {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
              Update password
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

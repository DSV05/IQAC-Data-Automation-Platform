import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { Eye, EyeOff, Loader2, ShieldCheck } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface LoginFormData {
  email: string;
  password: string;
}

export default function LoginPage() {
  const { login, isLoggingIn, loginError } = useAuth();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>();

  const onSubmit = (data: LoginFormData) => {
    login(data);
  };

  const errorMessage = loginError
    ? (loginError as any)?.response?.data?.detail ?? "Login failed. Please try again."
    : null;

  return (
    <div className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-[#003087] flex-col justify-between p-12">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <span className="text-white font-semibold text-lg">IQAC Platform</span>
        </div>

        <div className="space-y-6">
          <div>
            <h1 className="text-4xl font-bold text-white leading-tight">
              Data Automation
              <br />
              <span className="text-[#C9A227]">Platform</span>
            </h1>
            <p className="mt-4 text-white/70 text-lg leading-relaxed">
              Centralized institutional data management for accreditation,
              rankings, and compliance reporting.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {[
              { label: "NIRF", desc: "Rankings" },
              { label: "NAAC", desc: "Accreditation" },
              { label: "AISHE", desc: "Reports" },
              { label: "QS / THE", desc: "World Rankings" },
            ].map((item) => (
              <div
                key={item.label}
                className="bg-white/10 rounded-xl p-4 border border-white/10"
              >
                <div className="text-white font-semibold">{item.label}</div>
                <div className="text-white/60 text-sm">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="text-white/40 text-sm">
          Ganpat University • Internal Quality Assurance Cell
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2">
            <ShieldCheck className="w-7 h-7 text-[#003087]" />
            <span className="font-semibold text-[#003087]">IQAC Platform</span>
          </div>

          <div>
            <h2 className="text-2xl font-bold text-foreground">Welcome back</h2>
            <p className="mt-1 text-muted-foreground text-sm">
              Sign in to your IQAC account
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Error banner */}
            {errorMessage && (
              <div className="rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
                {errorMessage}
              </div>
            )}

            {/* Email */}
            <div className="space-y-1.5">
              <label
                htmlFor="email"
                className="block text-sm font-medium text-foreground"
              >
                Email address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@ganpatuniversity.ac.in"
                className={`w-full rounded-lg border px-3.5 py-2.5 text-sm bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-[#003087] transition ${
                  errors.email ? "border-destructive" : "border-input"
                }`}
                {...register("email", {
                  required: "Email is required",
                  pattern: {
                    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    message: "Enter a valid email address",
                  },
                })}
              />
              {errors.email && (
                <p className="text-xs text-destructive">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-foreground"
                >
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-[#003087] hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className={`w-full rounded-lg border px-3.5 py-2.5 pr-10 text-sm bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-[#003087] transition ${
                    errors.password ? "border-destructive" : "border-input"
                  }`}
                  {...register("password", {
                    required: "Password is required",
                    minLength: { value: 6, message: "Minimum 6 characters" },
                  })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="text-xs text-destructive">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoggingIn}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white font-medium py-2.5 text-sm transition disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isLoggingIn ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in…
                </>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <p className="text-center text-xs text-muted-foreground">
            Access is restricted to authorised IQAC personnel.
            <br />
            Contact your administrator to request access.
          </p>
        </div>
      </div>
    </div>
  );
}

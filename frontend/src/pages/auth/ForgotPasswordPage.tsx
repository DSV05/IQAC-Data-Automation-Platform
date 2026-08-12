import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { ArrowLeft, Loader2, Mail } from "lucide-react";
import { authService } from "@/services/auth.service";

interface FormData {
  email: string;
}

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>();

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    try {
      await authService.forgotPassword(data.email);
    } finally {
      setIsLoading(false);
      setSubmitted(true); // Always show success — prevents email enumeration
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-8">
      <div className="w-full max-w-md space-y-8">
        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to login
        </Link>

        <div>
          <h2 className="text-2xl font-bold text-foreground">Reset password</h2>
          <p className="mt-1 text-muted-foreground text-sm">
            Enter your email and we'll send a reset link if the account exists.
          </p>
        </div>

        {submitted ? (
          <div className="rounded-xl border border-border bg-muted/50 p-6 text-center space-y-3">
            <div className="mx-auto w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
              <Mail className="w-6 h-6 text-green-600" />
            </div>
            <p className="font-medium text-foreground">Check your inbox</p>
            <p className="text-sm text-muted-foreground">
              If an account exists for that email, a reset link has been sent. 
              The link expires in 2 hours.
            </p>
            <Link
              to="/login"
              className="inline-block text-sm text-[#003087] hover:underline mt-2"
            >
              Return to login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-sm font-medium text-foreground">
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
                  pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Enter a valid email" },
                })}
              />
              {errors.email && (
                <p className="text-xs text-destructive">{errors.email.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white font-medium py-2.5 text-sm transition disabled:opacity-60"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              Send reset link
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

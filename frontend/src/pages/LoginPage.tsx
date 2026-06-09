import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { login } from "../api";
import { useAuth } from "../context/AuthContext";
import { loginSchema, LoginFormValues } from "../utils/validation";

export default function LoginPage() {
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { login: loginContext } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormValues) => {
    setError("");

    try {
      const res = await login(data.email, data.password);
      loginContext(res.token, res.user);
      navigate("/events");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid email or password");
    }
  };

  return (
    <div className="page-container" style={{ maxWidth: 400, margin: "40px auto" }}>
      <h2>Sign In</h2>
      <p style={{ color: "#666", marginBottom: 20, fontSize: 14 }}>
        Enter your credentials to access PenguWave
      </p>
      {error && <div style={{ color: "red", marginBottom: 16 }}>{error}</div>}
      <form onSubmit={handleSubmit(onSubmit)}>
        <div style={{ marginBottom: 12 }}>
          <label>Email</label>
          <input
            type="email"
            {...register("email")}
            placeholder="you@company.com"
            style={{ width: "100%", padding: "8px", boxSizing: "border-box", borderColor: errors.email ? "red" : undefined }}
          />
          {errors.email && <div style={{ color: "red", fontSize: 12, marginTop: 4 }}>{errors.email.message}</div>}
        </div>
        <div style={{ marginBottom: 16 }}>
          <label>Password</label>
          <input
            type="password"
            {...register("password")}
            placeholder="••••••••"
            style={{ width: "100%", padding: "8px", boxSizing: "border-box", borderColor: errors.password ? "red" : undefined }}
          />
          {errors.password && <div style={{ color: "red", fontSize: 12, marginTop: 4 }}>{errors.password.message}</div>}
        </div>
        <button type="submit" className="btn-primary" disabled={isSubmitting} style={{ width: "100%", padding: "10px" }}>
          {isSubmitting ? "Signing In..." : "Sign In"}
        </button>
      </form>
    </div>
  );
}

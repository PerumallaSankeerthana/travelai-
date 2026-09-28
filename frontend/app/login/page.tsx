"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiRequest } from "@/lib/api";

type AuthResponse = {
  access_token: string;
  token_type: string;
  user?: {
    id?: number;
    email?: string;
  };
};

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await apiRequest<AuthResponse>(
        "/api/auth/login",
        {
          method: "POST",
          body: JSON.stringify({
            email,
            password,
          }),
        }
      );

      localStorage.setItem(
        "travelai_token",
        response.access_token
      );

      router.push("/plan");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Login failed"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f7f8fa] px-6 py-10">
      <div className="mx-auto flex min-h-[90vh] max-w-6xl items-center justify-center">

        <div className="grid w-full max-w-5xl overflow-hidden rounded-[2rem] border border-gray-200 bg-white shadow-xl md:grid-cols-2">

          {/* Left */}
          <div className="hidden bg-[#172033] p-12 text-white md:flex md:flex-col md:justify-between">

            <div>
              <Link
                href="/"
                className="flex items-center gap-3"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-lg font-bold text-[#111827]">
                  T
                </div>

                <span className="text-xl font-semibold">
                  TravelAI
                </span>
              </Link>

              <div className="mt-24">
                <p className="text-sm font-medium text-white/50">
                  YOUR JOURNEY STARTS HERE
                </p>

                <h1 className="mt-4 text-4xl font-semibold leading-tight">
                  Travel planning,
                  <br />
                  made intelligent.
                </h1>

                <p className="mt-6 max-w-sm text-sm leading-6 text-white/60">
                  Create personalized itineraries using real travel
                  data, AI reasoning and intelligent replanning.
                </p>
              </div>
            </div>

            <p className="text-sm text-white/40">
              TravelAI · Intelligent travel planning
            </p>
          </div>

          {/* Right */}
          <div className="p-8 sm:p-12">

            <div className="mb-10 md:hidden">
              <Link
                href="/"
                className="flex items-center gap-3"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#111827] text-lg font-bold text-white">
                  T
                </div>

                <span className="text-xl font-semibold">
                  TravelAI
                </span>
              </Link>
            </div>

            <div>
              <p className="text-sm font-semibold uppercase tracking-wider text-gray-400">
                Welcome back
              </p>

              <h2 className="mt-2 text-3xl font-semibold tracking-tight">
                Sign in to TravelAI
              </h2>

              <p className="mt-3 text-sm leading-6 text-gray-500">
                Continue planning your next journey.
              </p>
            </div>

            <form
              onSubmit={handleLogin}
              className="mt-8 space-y-5"
            >

              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Email
                </label>

                <input
                  type="email"
                  required
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="you@example.com"
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4 outline-none transition placeholder:text-gray-400 focus:border-gray-400 focus:bg-white focus:ring-4 focus:ring-gray-100"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Password
                </label>

                <input
                  type="password"
                  required
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Enter your password"
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4 outline-none transition placeholder:text-gray-400 focus:border-gray-400 focus:bg-white focus:ring-4 focus:ring-gray-100"
                />
              </div>

              {error && (
                <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-2xl bg-[#111827] px-6 py-4 text-sm font-semibold text-white shadow-lg transition hover:bg-black disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "Signing in..." : "Sign in"}
              </button>

            </form>

            <p className="mt-7 text-center text-sm text-gray-500">
              Don&apos;t have an account?{" "}
              <Link
                href="/register"
                className="font-semibold text-gray-900 hover:underline"
              >
                Create one
              </Link>
            </p>

          </div>
        </div>
      </div>
    </main>
  );
}

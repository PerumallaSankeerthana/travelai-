"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";

export default function PlanPage() {
  const router = useRouter();

  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [travelers, setTravelers] = useState(1);
  const [budget, setBudget] = useState("");
  const [preferences, setPreferences] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await apiRequest("/api/trips", {
        method: "POST",
        body: JSON.stringify({
          destination,
          start_date: startDate,
          end_date: endDate,
          travelers,
          budget: Number(budget),
          preferences: preferences
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        }),
      });

      sessionStorage.setItem(
        "travelai_trip",
        JSON.stringify(response)
      );

      router.push("/trip");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create trip"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-black text-white px-6 py-12">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-4xl font-bold">Plan your trip</h1>
        <p className="mt-2 text-zinc-400">
          Tell TravelAI where you want to go.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-10 space-y-6 rounded-3xl border border-zinc-800 bg-zinc-950 p-8"
        >
          <div>
            <label className="mb-2 block">Destination</label>
            <input
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="Goa"
              required
              className="w-full rounded-xl border border-zinc-700 bg-zinc-900 p-3"
            />
          </div>

          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <label className="mb-2 block">Start date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                className="w-full rounded-xl border border-zinc-700 bg-zinc-900 p-3"
              />
            </div>

            <div>
              <label className="mb-2 block">End date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
                className="w-full rounded-xl border border-zinc-700 bg-zinc-900 p-3"
              />
            </div>
          </div>

          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <label className="mb-2 block">Travelers</label>
              <input
                type="number"
                min="1"
                value={travelers}
                onChange={(e) => setTravelers(Number(e.target.value))}
                required
                className="w-full rounded-xl border border-zinc-700 bg-zinc-900 p-3"
              />
            </div>

            <div>
              <label className="mb-2 block">Budget (₹)</label>
              <input
                type="number"
                min="1"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                placeholder="30000"
                required
                className="w-full rounded-xl border border-zinc-700 bg-zinc-900 p-3"
              />
            </div>
          </div>

          <div>
            <label className="mb-2 block">
              Preferences
            </label>
            <input
              value={preferences}
              onChange={(e) => setPreferences(e.target.value)}
              placeholder="beaches, local food, nightlife"
              className="w-full rounded-xl border border-zinc-700 bg-zinc-900 p-3"
            />
            <p className="mt-2 text-sm text-zinc-500">
              Separate preferences with commas.
            </p>
          </div>

          {error && (
            <div className="rounded-xl border border-red-900 bg-red-950/40 p-4 text-red-300">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-white px-6 py-4 font-semibold text-black transition hover:bg-zinc-200 disabled:opacity-50"
          >
            {loading ? "Creating your trip..." : "Generate my trip"}
          </button>
        </form>
      </div>
    </main>
  );
}
"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useRouter } from "next/navigation";

type TripData = {
  trip_id: string;
  status: string;

  itinerary?: {
    days?: Day[];
  };

  flights?: Flight[];
  hotels?: Hotel[];

  cost_breakdown?: {
    allocation?: {
      flights?: number;
      hotel?: number;
      activities?: number;
      food?: number;
      buffer?: number;
    };

    flights?: number;
    hotel?: number;
    activities?: number;
    food?: number;
    buffer?: number;
    total?: number;
    allocated_total?: number;
    remaining_budget?: number;
    budget_remaining?: number;
  };
};

type Day = {
  date: string;
  day_number: number;
  is_editable: boolean;

  weather?: {
    condition?: string;
    temp_c?: number | null;
  };

  slots?: {
    morning?: Activity[];
    afternoon?: Activity[];
    evening?: Activity[];
  };
};

type ReplanResponse = {
  trip_id: string;
  replanned_days: number[];
  locked_days: number[];
  updated_itinerary: {
    days?: Day[];
  };
};

type Activity = {
  activity?: string;
  location?: string;
  est_cost?: number;
};

type Flight = {
  airline?: string;
  flight_number?: string;
  price?: number;
  currency?: string;
  result_id?: string;

  departure?: {
    airport?: string;
    time?: string;
  };

  arrival?: {
    airport?: string;
    time?: string;
  };
};

type Hotel = {
  name?: string;
  price_per_night?: number;
  rating?: number;
  result_id?: string;
};

export default function TripPage() {
  const router = useRouter();

  const [trip, setTrip] = useState<TripData | null>(null);
  const [message, setMessage] = useState("");
  const [affectedDays, setAffectedDays] = useState("");
  const [replanning, setReplanning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const storedTrip = sessionStorage.getItem("travelai_trip");

    if (!storedTrip) {
      router.push("/plan");
      return;
    }

    try {
      setTrip(JSON.parse(storedTrip));
    } catch {
      setError("Could not load your trip.");
    }
  }, [router]);

  async function handleReplan() {
    if (!trip || !message.trim() || !affectedDays.trim()) {
      setError("Enter a change request and affected day.");
      return;
    }

    const days = affectedDays
      .split(",")
      .map((value) => Number(value.trim()))
      .filter((value) => value > 0);

    if (!days.length) {
      setError("Enter a valid day number.");
      return;
    }

    setReplanning(true);
    setError("");

    try {
      const response = await apiRequest<ReplanResponse>(
        `/api/trips/${trip.trip_id}/replan`,
        {
          method: "POST",
          body: JSON.stringify({
            message,
            affected_days: days,
          }),
        }
      );

      const updatedTrip = {
        ...trip,
        itinerary: response.updated_itinerary,
        status: "replanned",
      };

      setTrip(updatedTrip);

      sessionStorage.setItem(
        "travelai_trip",
        JSON.stringify(updatedTrip)
      );

      setMessage("");
      setAffectedDays("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Replanning failed."
      );
    } finally {
      setReplanning(false);
    }
  }

  if (!trip) {
    return (
      <main className="min-h-screen bg-[#050505] text-white flex items-center justify-center">
        <p className="text-zinc-400">
          Loading your trip...
        </p>
      </main>
    );
  }

  const days = trip.itinerary?.days || [];
  const cost = trip.cost_breakdown || {};

  // Backend returns component budgets inside:
  // cost_breakdown.allocation
  const allocation = cost.allocation || {};

  const totalAllocated =
    cost.allocated_total ??
    cost.total ??
    0;

  const remainingBudget =
    cost.remaining_budget ??
    cost.budget_remaining ??
    0;

  return (
    <main className="min-h-screen bg-[#050505] text-white">

      {/* HEADER */}
      <header className="border-b border-white/10 bg-black/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">

          <button
            onClick={() => router.push("/")}
            className="text-xl font-bold tracking-tight"
          >
            Travel<span className="text-violet-400">AI</span>
          </button>

          <div className="flex items-center gap-4">

            <span className="hidden rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-sm text-emerald-300 md:block">
              Trip generated
            </span>

            <button
              onClick={() => router.push("/plan")}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
            >
              New trip
            </button>

          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-10">

        {/* HERO */}
        <section className="mb-10">

          <div className="mb-3 flex items-center gap-3">

            <span className="rounded-full bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-300">
              AI ITINERARY
            </span>

            <span className="text-sm text-zinc-500">
              {trip.trip_id}
            </span>

          </div>

          <h1 className="text-4xl font-bold tracking-tight md:text-6xl">
            Your trip is ready.
          </h1>

          <p className="mt-4 max-w-2xl text-lg text-zinc-400">
            TravelAI combined your preferences, live travel data,
            memory and itinerary planning into one trip.
          </p>

        </section>

        {/* BUDGET */}
        <section className="mb-10 grid gap-4 md:grid-cols-5">

          <StatCard
            label="Flight"
            value={`₹${(
              allocation.flights ?? 0
            ).toLocaleString("en-IN")}`}
          />

          <StatCard
            label="Hotel"
            value={`₹${(
              allocation.hotel ?? 0
            ).toLocaleString("en-IN")}`}
          />

          <StatCard
            label="Food"
            value={`₹${(
              allocation.food ?? 0
            ).toLocaleString("en-IN")}`}
          />

          <StatCard
            label="Activities"
            value={`₹${(
              allocation.activities ?? 0
            ).toLocaleString("en-IN")}`}
          />

          <StatCard
            label="Total Allocated"
            value={`₹${totalAllocated.toLocaleString(
              "en-IN"
            )}`}
          />

        </section>

        {/* REMAINING BUDGET */}
        <section className="mb-10">

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">

            <div className="flex items-center justify-between">

              <div>
                <p className="text-sm text-zinc-500">
                  Remaining Budget
                </p>

                <p className="mt-2 text-2xl font-bold">
                  ₹{remainingBudget.toLocaleString("en-IN")}
                </p>
              </div>

              <div className="rounded-xl bg-emerald-500/10 px-4 py-2 text-sm text-emerald-300">
                Budget
              </div>

            </div>

          </div>

        </section>

        {/* WARNING */}
        {trip.status === "budget_insufficient" && (
          <div className="mb-8 rounded-2xl border border-amber-500/20 bg-amber-500/10 p-5">

            <p className="font-semibold text-amber-300">
              Budget warning
            </p>

            <p className="mt-1 text-sm text-amber-200/70">
              The selected flight leaves limited budget for
              accommodation and activities. You can adjust your
              trip details and generate another itinerary.
            </p>

          </div>
        )}

        {error && (
          <div className="mb-8 rounded-2xl border border-red-500/20 bg-red-500/10 p-5 text-red-300">
            {error}
          </div>
        )}

        {/* FLIGHT + HOTEL */}
        <section className="mb-12 grid gap-6 lg:grid-cols-2">

          {/* FLIGHTS */}
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">

            <h2 className="text-xl font-semibold">
              Flights
            </h2>

            <div className="mt-5 space-y-4">

              {trip.flights?.length ? (
                trip.flights.map((flight, index) => (

                  <div
                    key={flight.result_id || index}
                    className="rounded-2xl border border-white/10 bg-black/40 p-5"
                  >

                    <div className="flex items-center justify-between">

                      <div>

                        <p className="font-semibold">
                          {flight.airline || "Flight"}
                        </p>

                        <p className="mt-1 text-sm text-zinc-500">
                          {flight.flight_number || ""}
                        </p>

                      </div>

                      <p className="text-lg font-bold">
                        ₹{flight.price?.toLocaleString("en-IN")}
                      </p>

                    </div>

                    <div className="mt-5 flex items-center justify-between text-sm">

                      <div>

                        <p className="text-zinc-500">
                          {flight.departure?.airport}
                        </p>

                        <p className="mt-1">
                          {flight.departure?.time}
                        </p>

                      </div>

                      <div className="mx-4 h-px flex-1 bg-white/10" />

                      <div className="text-right">

                        <p className="text-zinc-500">
                          {flight.arrival?.airport}
                        </p>

                        <p className="mt-1">
                          {flight.arrival?.time}
                        </p>

                      </div>

                    </div>

                  </div>

                ))
              ) : (

                <p className="text-zinc-500">
                  No flight results available.
                </p>

              )}

            </div>

          </div>

          {/* HOTELS */}
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">

            <h2 className="text-xl font-semibold">
              Hotels
            </h2>

            <div className="mt-5 space-y-4">

              {trip.hotels?.length ? (
                trip.hotels.map((hotel, index) => (

                  <div
                    key={hotel.result_id || index}
                    className="rounded-2xl border border-white/10 bg-black/40 p-5"
                  >

                    <div className="flex items-center justify-between">

                      <div>

                        <p className="font-semibold">
                          {hotel.name || "Hotel"}
                        </p>

                        {hotel.rating && (
                          <p className="mt-1 text-sm text-amber-300">
                            ★ {hotel.rating}
                          </p>
                        )}

                      </div>

                      <div className="text-right">

                        <p className="font-bold">
                          ₹
                          {hotel.price_per_night?.toLocaleString(
                            "en-IN"
                          )}
                        </p>

                        <p className="text-xs text-zinc-500">
                          per night
                        </p>

                      </div>

                    </div>

                  </div>

                ))
              ) : (

                <p className="text-zinc-500">
                  No hotel selected within the current budget.
                </p>

              )}

            </div>

          </div>

        </section>

        {/* ITINERARY */}
        <section>

          <div className="mb-6">

            <p className="text-sm font-medium text-violet-400">
              DAY BY DAY
            </p>

            <h2 className="mt-1 text-3xl font-bold">
              Your itinerary
            </h2>

          </div>

          <div className="space-y-6">

            {days.map((day) => (
              <DayCard
                key={day.day_number}
                day={day}
              />
            ))}

          </div>

        </section>

        {/* REPLAN */}
        <section className="mt-12 rounded-3xl border border-violet-500/20 bg-violet-500/[0.05] p-6 md:p-8">

          <div className="max-w-2xl">

            <p className="text-sm font-medium text-violet-400">
              AI REPLANNING
            </p>

            <h2 className="mt-2 text-2xl font-bold">
              Want to change something?
            </h2>

            <p className="mt-2 text-zinc-400">
              Tell TravelAI what you want changed and which
              day is affected. Earlier completed days remain
              locked.
            </p>

          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-[180px_1fr_auto]">

            <input
              value={affectedDays}
              onChange={(e) =>
                setAffectedDays(e.target.value)
              }
              placeholder="Day 3"
              className="rounded-xl border border-white/10 bg-black/50 px-4 py-3 text-white outline-none focus:border-violet-400"
            />

            <input
              value={message}
              onChange={(e) =>
                setMessage(e.target.value)
              }
              placeholder="Replace outdoor activities with indoor activities"
              className="rounded-xl border border-white/10 bg-black/50 px-4 py-3 text-white outline-none focus:border-violet-400"
            />

            <button
              onClick={handleReplan}
              disabled={replanning}
              className="rounded-xl bg-white px-6 py-3 font-semibold text-black hover:bg-zinc-200 disabled:opacity-50"
            >
              {replanning
                ? "Replanning..."
                : "Replan"}
            </button>

          </div>

        </section>

      </div>

    </main>
  );
}

function StatCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">

      <p className="text-sm text-zinc-500">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold">
        {value}
      </p>

    </div>
  );
}

function DayCard({ day }: { day: Day }) {

  const slots = [
    {
      name: "Morning",
      items: day.slots?.morning || [],
    },
    {
      name: "Afternoon",
      items: day.slots?.afternoon || [],
    },
    {
      name: "Evening",
      items: day.slots?.evening || [],
    },
  ];

  return (
    <article
      className={`rounded-3xl border p-6 ${
        day.is_editable
          ? "border-white/10 bg-white/[0.03]"
          : "border-white/5 bg-white/[0.015] opacity-70"
      }`}
    >

      <div className="flex flex-col justify-between gap-4 md:flex-row">

        <div>

          <div className="flex items-center gap-3">

            <span className="rounded-full bg-violet-500/10 px-3 py-1 text-sm font-semibold text-violet-300">
              Day {day.day_number}
            </span>

            {!day.is_editable && (
              <span className="text-xs text-zinc-500">
                🔒 Locked
              </span>
            )}

          </div>

          <h3 className="mt-3 text-2xl font-bold">
            {formatDate(day.date)}
          </h3>

        </div>

        {day.weather && (
          <div className="rounded-2xl border border-white/10 bg-black/30 px-5 py-3">

            <p className="text-xs text-zinc-500">
              Weather
            </p>

            <p className="mt-1 font-medium">
              {day.weather.condition || "Unavailable"}

              {day.weather.temp_c != null &&
                ` · ${day.weather.temp_c}°C`}
            </p>

          </div>
        )}

      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-3">

        {slots.map((slot) => (

          <div
            key={slot.name}
            className="rounded-2xl border border-white/10 bg-black/30 p-5"
          >

            <p className="text-sm font-semibold text-violet-300">
              {slot.name}
            </p>

            <div className="mt-4 space-y-4">

              {slot.items.length ? (

                slot.items.map((activity, index) => (

                  <div key={index}>

                    <p className="font-medium">
                      {activity.activity || "Activity"}
                    </p>

                    {activity.location && (
                      <p className="mt-1 text-sm text-zinc-500">
                        📍 {activity.location}
                      </p>
                    )}

                    {activity.est_cost != null && (
                      <p className="mt-2 text-sm text-zinc-400">
                        ₹
                        {activity.est_cost.toLocaleString(
                          "en-IN"
                        )}
                      </p>
                    )}

                  </div>

                ))

              ) : (

                <p className="text-sm text-zinc-600">
                  No activity planned.
                </p>

              )}

            </div>

          </div>

        ))}

      </div>

    </article>
  );
}

function formatDate(date: string) {

  if (!date) return "";

  return new Date(
    `${date}T00:00:00`
  ).toLocaleDateString(
    "en-IN",
    {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    }
  );
}
"use client";

import Link from "next/link";
import { useState } from "react";

const preferences = [
  "Beaches",
  "Local food",
  "Nightlife",
  "Adventure",
  "Culture",
  "Relaxation",
];

export default function Home() {
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [travelers, setTravelers] = useState(2);
  const [budget, setBudget] = useState("");
  const [selectedPreferences, setSelectedPreferences] = useState<string[]>(
    []
  );

  const togglePreference = (preference: string) => {
    setSelectedPreferences((current) =>
      current.includes(preference)
        ? current.filter((item) => item !== preference)
        : [...current, preference]
    );
  };

  return (
    <main className="min-h-screen bg-[#f7f8fa] text-[#111827]">
      {/* =====================================================
          NAVIGATION
      ====================================================== */}

      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-10">
        {/* Logo */}

        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#111827] text-lg font-bold text-white">
            T
          </div>

          <span className="text-xl font-semibold tracking-tight">
            TravelAI
          </span>
        </Link>

        {/* Navigation links */}

        <div className="hidden items-center gap-8 text-sm font-medium text-gray-500 md:flex">
          <a
            href="#planner"
            className="transition hover:text-gray-900"
          >
            Plan a trip
          </a>

          <a
            href="#how"
            className="transition hover:text-gray-900"
          >
            How it works
          </a>
        </div>

        {/* Authentication */}

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="rounded-full border border-gray-200 bg-white px-5 py-2.5 text-sm font-medium shadow-sm transition hover:border-gray-300"
          >
            Sign in
          </Link>

          <Link
            href="/register"
            className="rounded-full bg-[#111827] px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-black"
          >
            Get started
          </Link>
        </div>
      </nav>

      {/* =====================================================
          HERO
      ====================================================== */}

      <section className="mx-auto max-w-7xl px-6 pb-10 pt-8 lg:px-10 lg:pt-14">
        <div className="relative overflow-hidden rounded-[2rem] bg-[#172033] px-7 py-12 text-white shadow-xl lg:px-14 lg:py-16">
          {/* Decorative elements */}

          <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />

          <div className="absolute -bottom-32 left-1/3 h-80 w-80 rounded-full bg-sky-400/10 blur-3xl" />

          <div className="relative max-w-3xl">
            {/* Badge */}

            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-4 py-2 text-sm text-white/80 backdrop-blur">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />

              AI-powered trip planning
            </div>

            {/* Heading */}

            <h1 className="max-w-3xl text-4xl font-semibold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
              Your next journey,
              <br />
              planned intelligently.
            </h1>

            {/* Description */}

            <p className="mt-6 max-w-2xl text-base leading-7 text-white/65 sm:text-lg">
              Tell TravelAI where you want to go, what you love, and
              what you want to spend. We&apos;ll build a personalized
              itinerary around you.
            </p>

            {/* Hero buttons */}

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/register"
                className="rounded-2xl bg-white px-6 py-3.5 text-center text-sm font-semibold text-[#111827] shadow-lg transition hover:-translate-y-0.5"
              >
                Start planning
              </Link>

              <a
                href="#how"
                className="rounded-2xl border border-white/20 bg-white/10 px-6 py-3.5 text-center text-sm font-semibold text-white backdrop-blur transition hover:bg-white/15"
              >
                See how it works
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          TRIP PLANNER PREVIEW
      ====================================================== */}

      <section
        id="planner"
        className="mx-auto max-w-7xl px-6 pb-20 lg:px-10"
      >
        <div className="-mt-2 rounded-[2rem] border border-gray-200 bg-white p-6 shadow-xl sm:p-8">
          {/* Header */}

          <div className="mb-8">
            <p className="text-sm font-semibold uppercase tracking-wider text-gray-400">
              Start planning
            </p>

            <h2 className="mt-2 text-2xl font-semibold tracking-tight">
              Where are you going?
            </h2>

            <p className="mt-2 text-sm text-gray-500">
              Give us a few details and TravelAI will take care of
              the rest.
            </p>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            {/* Destination */}

            <div className="lg:col-span-2">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Destination
              </label>

              <input
                value={destination}
                onChange={(event) =>
                  setDestination(event.target.value)
                }
                placeholder="e.g. Goa, Paris, Tokyo..."
                className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4 text-base outline-none transition placeholder:text-gray-400 focus:border-gray-400 focus:bg-white focus:ring-4 focus:ring-gray-100"
              />
            </div>

            {/* Start date */}

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Start date
              </label>

              <input
                type="date"
                value={startDate}
                onChange={(event) =>
                  setStartDate(event.target.value)
                }
                className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4 outline-none transition focus:border-gray-400 focus:bg-white focus:ring-4 focus:ring-gray-100"
              />
            </div>

            {/* End date */}

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                End date
              </label>

              <input
                type="date"
                value={endDate}
                onChange={(event) =>
                  setEndDate(event.target.value)
                }
                className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4 outline-none transition focus:border-gray-400 focus:bg-white focus:ring-4 focus:ring-gray-100"
              />
            </div>

            {/* Travelers */}

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Travelers
              </label>

              <div className="flex items-center justify-between rounded-2xl border border-gray-200 bg-gray-50 px-5 py-3.5">
                <span className="text-sm text-gray-500">
                  {travelers === 1
                    ? "1 traveler"
                    : `${travelers} travelers`}
                </span>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() =>
                      setTravelers((value) =>
                        Math.max(1, value - 1)
                      )
                    }
                    className="flex h-9 w-9 items-center justify-center rounded-full border border-gray-200 bg-white text-lg transition hover:bg-gray-100"
                  >
                    −
                  </button>

                  <span className="w-5 text-center font-medium">
                    {travelers}
                  </span>

                  <button
                    type="button"
                    onClick={() =>
                      setTravelers((value) => value + 1)
                    }
                    className="flex h-9 w-9 items-center justify-center rounded-full border border-gray-200 bg-white text-lg transition hover:bg-gray-100"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>

            {/* Budget */}

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Budget
              </label>

              <div className="relative">
                <span className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400">
                  ₹
                </span>

                <input
                  type="number"
                  value={budget}
                  onChange={(event) =>
                    setBudget(event.target.value)
                  }
                  placeholder="130000"
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 py-4 pl-10 pr-5 outline-none transition placeholder:text-gray-400 focus:border-gray-400 focus:bg-white focus:ring-4 focus:ring-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Preferences */}

          <div className="mt-7">
            <label className="mb-3 block text-sm font-medium text-gray-700">
              What do you enjoy?
            </label>

            <div className="flex flex-wrap gap-2.5">
              {preferences.map((preference) => {
                const selected =
                  selectedPreferences.includes(
                    preference
                  );

                return (
                  <button
                    key={preference}
                    type="button"
                    onClick={() =>
                      togglePreference(preference)
                    }
                    className={`rounded-full border px-4 py-2.5 text-sm font-medium transition ${
                      selected
                        ? "border-gray-900 bg-gray-900 text-white"
                        : "border-gray-200 bg-white text-gray-600 hover:border-gray-400"
                    }`}
                  >
                    {preference}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Generate */}

          <div className="mt-8 flex flex-col items-center justify-between gap-4 border-t border-gray-100 pt-7 sm:flex-row">
            <p className="text-sm text-gray-400">
              Sign in to generate your personalized trip.
            </p>

            <Link
              href="/login"
              className="w-full rounded-2xl bg-[#111827] px-8 py-4 text-center text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-black sm:w-auto"
            >
              ✨ Generate my trip
            </Link>
          </div>
        </div>
      </section>

      {/* =====================================================
          HOW IT WORKS
      ====================================================== */}

      <section
        id="how"
        className="border-t border-gray-200 bg-white"
      >
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-wider text-gray-400">
              How it works
            </p>

            <h2 className="mt-2 text-3xl font-semibold tracking-tight">
              From an idea to an itinerary.
            </h2>
          </div>

          <div className="mt-12 grid gap-5 md:grid-cols-3">
            {/* Card 1 */}

            <div className="rounded-3xl border border-gray-200 bg-[#f8f9fb] p-7">
              <span className="text-sm font-semibold text-gray-400">
                01
              </span>

              <h3 className="mt-8 text-lg font-semibold">
                Tell us what you want
              </h3>

              <p className="mt-3 text-sm leading-6 text-gray-500">
                Destination, dates, budget and your travel
                preferences.
              </p>
            </div>

            {/* Card 2 */}

            <div className="rounded-3xl border border-gray-200 bg-[#f8f9fb] p-7">
              <span className="text-sm font-semibold text-gray-400">
                02
              </span>

              <h3 className="mt-8 text-lg font-semibold">
                TravelAI does the work
              </h3>

              <p className="mt-3 text-sm leading-6 text-gray-500">
                Multiple agents gather travel data and build
                your personalized plan.
              </p>
            </div>

            {/* Card 3 */}

            <div className="rounded-3xl border border-gray-200 bg-[#f8f9fb] p-7">
              <span className="text-sm font-semibold text-gray-400">
                03
              </span>

              <h3 className="mt-8 text-lg font-semibold">
                Change anything
              </h3>

              <p className="mt-3 text-sm leading-6 text-gray-500">
                Replan individual days whenever your plans or
                conditions change.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          FOOTER
      ====================================================== */}

      <footer className="border-t border-gray-200 bg-white px-6 py-8 text-center text-sm text-gray-400">
        TravelAI · Intelligent travel planning
      </footer>
    </main>
  );
}
"use client";

import { environment } from "@/lib/config/environment";
import { useSystemStatus } from "@/hooks/use-system-status";

function StatusCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-slate-200 bg-white p-4 shadow-sm">
      <dt className="text-sm text-slate-500">{label}</dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  );
}

export function DevelopmentStatus() {
  const { health, readiness } = useSystemStatus();
  const isLoading = health.isLoading || readiness.isLoading;
  const error = health.error ?? readiness.error;
  const refresh = () => {
    void health.refetch();
    void readiness.refetch();
  };

  return (
    <main className="mx-auto max-w-4xl p-6 sm:p-10">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
        Phase 1
      </p>
      <h1 className="mt-2 text-3xl font-bold">
        AI Investment Intelligence Platform
      </h1>
      <p className="mt-2 text-slate-600">
        Internal development environment status
      </p>

      {isLoading && (
        <p role="status" className="mt-8">
          Checking backend connectivity…
        </p>
      )}
      {error && (
        <div
          role="alert"
          className="mt-8 rounded border border-red-300 bg-red-50 p-4 text-red-900"
        >
          Backend unavailable. {error.message}
        </div>
      )}

      {!isLoading && !error && (
        <dl className="mt-8 grid gap-4 sm:grid-cols-2">
          <StatusCard label="Backend connection" value="Connected" />
          <StatusCard
            label="Backend version"
            value={health.data?.version ?? "Unknown"}
          />
          <StatusCard
            label="Health status"
            value={health.data?.status ?? "Unknown"}
          />
          <StatusCard
            label="Readiness status"
            value={readiness.data?.status ?? "Unknown"}
          />
          <StatusCard
            label="Database status"
            value={readiness.data?.database ?? "Unknown"}
          />
          <StatusCard
            label="Environment"
            value={environment.NEXT_PUBLIC_APP_ENV}
          />
        </dl>
      )}

      <button
        className="mt-8 rounded bg-slate-900 px-4 py-2 text-white disabled:opacity-50"
        onClick={refresh}
        disabled={health.isFetching || readiness.isFetching}
      >
        Refresh
      </button>
    </main>
  );
}

"use client";

export default function ErrorBoundary({
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="text-2xl font-semibold">
        The status screen could not be displayed.
      </h1>
      <button
        className="mt-4 rounded bg-slate-900 px-4 py-2 text-white"
        onClick={reset}
      >
        Try again
      </button>
    </main>
  );
}

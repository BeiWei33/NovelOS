"use client";

import { useState, useEffect, useCallback } from "react";
import {
  fetchErrors,
  type ErrorRecord,
  type ErrorAggregation,
  type ErrorListResponse,
} from "@/lib/error-api";

const SEVERITY_COLORS: Record<string, string> = {
  info: "text-blue-400 bg-blue-950/50",
  warning: "text-yellow-400 bg-yellow-950/50",
  error: "text-red-400 bg-red-950/50",
  fatal: "text-red-200 bg-red-900/70",
};

const TYPE_COLORS: Record<string, string> = {
  api: "text-purple-400",
  network: "text-cyan-400",
  validation: "text-orange-400",
  render: "text-pink-400",
  unknown: "text-gray-400",
};

export default function ErrorViewerPage() {
  const [errors, setErrors] = useState<ErrorRecord[]>([]);
  const [aggregations, setAggregations] = useState<ErrorAggregation[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(50);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterType, setFilterType] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterSince, setFilterSince] = useState("");

  // View mode
  const [showAggregation, setShowAggregation] = useState(false);

  // Detail modal
  const [selectedError, setSelectedError] = useState<ErrorRecord | null>(null);

  // Check debug access
  const isDebugEnabled =
    process.env.NEXT_PUBLIC_DEBUG === "true" ||
    (typeof window !== "undefined" &&
      (window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1"));

  const loadErrors = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (showAggregation) {
        const result = await fetchErrors({
          aggregate: true,
          type: filterType || undefined,
          severity: filterSeverity || undefined,
          since: filterSince || undefined,
        });
        const aggData = result as { aggregations: ErrorAggregation[] };
        setAggregations(aggData.aggregations);
        setErrors([]);
        setTotal(aggData.aggregations.length);
      } else {
        const result = await fetchErrors({
          page,
          limit,
          type: filterType || undefined,
          severity: filterSeverity || undefined,
          since: filterSince || undefined,
        });
        const listData = result as ErrorListResponse;
        setErrors(listData.errors);
        setTotal(listData.total);
        setAggregations([]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load errors");
    } finally {
      setLoading(false);
    }
  }, [page, limit, filterType, filterSeverity, filterSince, showAggregation]);

  useEffect(() => {
    loadErrors();
  }, [loadErrors]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [filterType, filterSeverity, filterSince, showAggregation]);

  if (!isDebugEnabled) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Access Denied</h1>
          <p className="text-gray-400">
            Error viewer is only available in debug mode.
          </p>
        </div>
      </div>
    );
  }

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">Error Viewer</h1>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowAggregation(!showAggregation)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                showAggregation
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
              }`}
            >
              {showAggregation ? "Aggregation View" : "List View"}
            </button>
            <button
              onClick={loadErrors}
              disabled={loading}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Filter Panel */}
        <div className="mb-6 p-4 bg-gray-900 border border-gray-800 rounded-lg">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Type:</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value="">All</option>
                <option value="api">API</option>
                <option value="network">Network</option>
                <option value="validation">Validation</option>
                <option value="render">Render</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Severity:</label>
              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value)}
                className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value="">All</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
                <option value="fatal">Fatal</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Since:</label>
              <input
                type="date"
                value={filterSince}
                onChange={(e) => setFilterSince(e.target.value)}
                className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>

            <button
              onClick={() => {
                setFilterType("");
                setFilterSeverity("");
                setFilterSince("");
              }}
              className="px-3 py-1.5 text-sm text-gray-400 hover:text-gray-300 transition-colors"
            >
              Clear Filters
            </button>

            <div className="ml-auto text-sm text-gray-400">
              Total: {total} error{total !== 1 ? "s" : ""}
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-950 border border-red-800 rounded-lg text-red-200">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading...</div>
        ) : showAggregation ? (
          /* Aggregation View */
          <div className="border border-gray-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-900 text-gray-400">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">Count</th>
                  <th className="px-4 py-3 text-left font-medium">Type</th>
                  <th className="px-4 py-3 text-left font-medium">Severity</th>
                  <th className="px-4 py-3 text-left font-medium">Message</th>
                  <th className="px-4 py-3 text-left font-medium">Fingerprint</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {aggregations.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                      No errors found
                    </td>
                  </tr>
                ) : (
                  aggregations.map((agg, i) => (
                    <tr
                      key={i}
                      className="hover:bg-gray-900/50 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 bg-indigo-950 text-indigo-300 rounded font-mono text-xs">
                          {agg.count}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={TYPE_COLORS[agg.type] || "text-gray-400"}>
                          {agg.type}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-xs ${
                            SEVERITY_COLORS[agg.severity] || "text-gray-400"
                          }`}
                        >
                          {agg.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-300 max-w-md truncate">
                        {agg.message}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-500">
                        {agg.fingerprint.slice(0, 20)}...
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : (
          /* List View */
          <div className="border border-gray-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-900 text-gray-400">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">Time</th>
                  <th className="px-4 py-3 text-left font-medium">Type</th>
                  <th className="px-4 py-3 text-left font-medium">Severity</th>
                  <th className="px-4 py-3 text-left font-medium">Message</th>
                  <th className="px-4 py-3 text-left font-medium">Context</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {errors.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                      No errors found
                    </td>
                  </tr>
                ) : (
                  errors.map((err) => (
                    <tr
                      key={err.id}
                      onClick={() => setSelectedError(err)}
                      className="hover:bg-gray-900/50 transition-colors cursor-pointer"
                    >
                      <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">
                        {err.created_at
                          ? new Date(err.created_at).toLocaleString("zh-CN")
                          : "-"}
                      </td>
                      <td className="px-4 py-3">
                        <span className={TYPE_COLORS[err.type] || "text-gray-400"}>
                          {err.type}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-xs ${
                            SEVERITY_COLORS[err.severity] || "text-gray-400"
                          }`}
                        >
                          {err.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-300 max-w-md truncate">
                        {err.message}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">
                        {String(err.context?.page ?? "") || "-"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!showAggregation && totalPages > 1 && (
          <div className="mt-6 flex items-center justify-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm transition-colors"
            >
              Previous
            </button>
            <span className="text-sm text-gray-400">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm transition-colors"
            >
              Next
            </button>
          </div>
        )}
      </main>

      {/* Detail Modal */}
      {selectedError && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={(e) => e.target === e.currentTarget && setSelectedError(null)}
        >
          <div className="bg-gray-900 border border-gray-800 rounded-xl max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span
                  className={`px-2 py-0.5 rounded text-xs ${
                    SEVERITY_COLORS[selectedError.severity] || "text-gray-400"
                  }`}
                >
                  {selectedError.severity}
                </span>
                <span className={TYPE_COLORS[selectedError.type] || "text-gray-400"}>
                  {selectedError.type}
                </span>
              </div>
              <button
                onClick={() => setSelectedError(null)}
                className="text-gray-400 hover:text-gray-300 text-xl"
              >
                &times;
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-auto flex-1">
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Message</h3>
                <p className="text-gray-200">{selectedError.message}</p>
              </div>

              {selectedError.stack && (
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-gray-400 mb-2">Stack Trace</h3>
                  <pre className="p-4 bg-gray-950 border border-gray-800 rounded-lg text-xs text-gray-300 overflow-auto max-h-64 whitespace-pre-wrap">
                    {selectedError.stack}
                  </pre>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Context</h3>
                <pre className="p-4 bg-gray-950 border border-gray-800 rounded-lg text-xs text-gray-300 overflow-auto max-h-48">
                  {JSON.stringify(selectedError.context, null, 2)}
                </pre>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">ID:</span>
                  <span className="ml-2 font-mono text-xs">{selectedError.id}</span>
                </div>
                <div>
                  <span className="text-gray-500">Fingerprint:</span>
                  <span className="ml-2 font-mono text-xs">{selectedError.fingerprint}</span>
                </div>
                <div>
                  <span className="text-gray-500">Created:</span>
                  <span className="ml-2">
                    {selectedError.created_at
                      ? new Date(selectedError.created_at).toLocaleString("zh-CN")
                      : "-"}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">IP:</span>
                  <span className="ml-2">{selectedError.ip_address || "-"}</span>
                </div>
                {selectedError.user_agent && (
                  <div className="col-span-2">
                    <span className="text-gray-500">User Agent:</span>
                    <span className="ml-2 text-xs break-all">
                      {selectedError.user_agent}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
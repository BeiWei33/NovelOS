/**
 * Unified error capture module for NovelOS frontend.
 *
 * Classifies errors into typed, structured records with fingerprints so
 * they can later be forwarded to a logging backend without leaking raw
 * exception objects up the call stack.
 */

type ErrorType = "api" | "network" | "validation" | "render" | "unknown";
type ErrorSeverity = "info" | "warning" | "error" | "fatal";

export interface StructuredError {
  type: ErrorType;
  severity: ErrorSeverity;
  message: string;
  stack?: string;
  fingerprint: string;
  context: {
    page: string;
    action: string;
    timestamp: string;
    novelId?: string;
    chapterId?: string;
    sceneId?: string;
  };
  originalError?: unknown;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function classifyError(error: unknown): { type: ErrorType; severity: ErrorSeverity } {
  if (error instanceof TypeError && error.message.toLowerCase().includes("fetch")) {
    return { type: "network", severity: "error" };
  }

  if (error instanceof Error) {
    const msg = error.message.toLowerCase();
    // HTTP status codes embedded in the message (e.g. from `throw new Error(text)`)
    if (/\b[45]\d{2}\b/.test(msg) || msg.includes("unauthorized") || msg.includes("forbidden")) {
      return { type: "api", severity: "error" };
    }
    if (msg.includes("network") || msg.includes("failed to fetch") || msg.includes("load failed")) {
      return { type: "network", severity: "error" };
    }
  }

  // Response objects (e.g. !res.ok branches that throw a Response)
  if (
    typeof error === "object" &&
    error !== null &&
    "status" in error &&
    typeof (error as { status: unknown }).status === "number"
  ) {
    const status = (error as { status: number }).status;
    if (status >= 400 && status < 600) {
      return { type: "api", severity: status >= 500 ? "fatal" : "error" };
    }
  }

  return { type: "unknown", severity: "error" };
}

function extractMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  try {
    return JSON.stringify(error);
  } catch {
    return String(error);
  }
}

function extractStack(error: unknown): string | undefined {
  if (error instanceof Error) return error.stack;
  return undefined;
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Capture an error and return a structured record.
 *
 * In development the record is also printed to the console so existing
 * debugging workflows are not disrupted.
 */
export function captureError(
  error: unknown,
  context: Partial<StructuredError["context"]> & { page: string; action: string }
): StructuredError {
  const { type, severity } = classifyError(error);
  const message = extractMessage(error);

  const structured: StructuredError = {
    type,
    severity,
    message,
    stack: extractStack(error),
    fingerprint: `${type}:${message.slice(0, 50)}`,
    context: {
      timestamp: new Date().toISOString(),
      ...context,
    },
    originalError: error,
  };

  if (process.env.NODE_ENV === "development") {
    console.error(
      `[${structured.type.toUpperCase()}] ${structured.context.page} / ${structured.context.action}:`,
      structured
    );
  }

  return structured;
}

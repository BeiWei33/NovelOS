/**
 * ErrorReporter — queues structured errors and forwards them to the backend.
 *
 * When the browser is offline, errors accumulate in the localStorage-backed
 * ErrorQueue. When connectivity is restored the queue is flushed automatically.
 * Uses native fetch and no extra dependencies.
 */

import type { StructuredError } from "./error";
import { ErrorQueue } from "./error-queue";

const ERRORS_ENDPOINT = "/errors";

export class ErrorReporter {
  private queue: ErrorQueue;
  private isOnline: boolean;

  constructor() {
    this.queue = new ErrorQueue();
    // Assume online in SSR/non-browser environments
    this.isOnline = typeof navigator !== "undefined" ? navigator.onLine : true;
    this.startOnlineListener();
  }

  /**
   * Queue an error and attempt to flush immediately if online.
   * Fire-and-forget — callers should not await this.
   */
  async report(error: StructuredError): Promise<void> {
    this.queue.push(error);

    if (this.isOnline) {
      await this.flush();
    }
  }

  /**
   * Drain the queue and POST all errors to the backend.
   * Errors that fail to send are re-queued.
   */
  private async flush(): Promise<void> {
    if (this.queue.size() === 0) return;

    const errors = this.queue.drain();

    try {
      const response = await fetch(ERRORS_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(errors),
      });

      if (!response.ok) {
        // Backend rejected: put errors back so they are retried later
        errors.forEach((e) => this.queue.push(e));
      }
    } catch {
      // Network failure: put errors back so they are retried on reconnect
      errors.forEach((e) => this.queue.push(e));
    }
  }

  /**
   * Listen to browser online/offline events.
   * Flush the queue whenever connectivity is restored.
   */
  private startOnlineListener(): void {
    if (typeof window === "undefined") return;

    window.addEventListener("online", () => {
      this.isOnline = true;
      // Flush without blocking the event handler
      void this.flush();
    });

    window.addEventListener("offline", () => {
      this.isOnline = false;
    });
  }
}

// Singleton — import and use directly across the app
export const errorReporter = new ErrorReporter();

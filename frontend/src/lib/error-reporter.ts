/**
 * ErrorReporter — queues structured errors and forwards them to the backend.
 *
 * When the browser is offline, errors accumulate in the localStorage-backed
 * ErrorQueue. When connectivity is restored the queue is flushed automatically.
 * Uses native fetch and no extra dependencies.
 *
 * Features:
 * - Exponential backoff retry: 1s, 2s, 4s, 8s... max 60s
 * - Pause 5 minutes after 5 consecutive failures
 * - Flush pending errors on page load
 */

import type { StructuredError } from "./error";
import { ErrorQueue } from "./error-queue";

const ERRORS_ENDPOINT = "/errors";

// Retry configuration
const INITIAL_RETRY_DELAY = 1000; // 1 second
const MAX_RETRY_DELAY = 60000; // 60 seconds
const MAX_CONSECUTIVE_FAILURES = 5;
const PAUSE_DURATION = 300000; // 5 minutes

export class ErrorReporter {
  private queue: ErrorQueue;
  private isOnline: boolean;
  private retryDelay: number = INITIAL_RETRY_DELAY;
  private consecutiveFailures: number = 0;
  private pausedUntil: number = 0;
  private flushTimeoutId: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    this.queue = new ErrorQueue();
    // Assume online in SSR/non-browser environments
    this.isOnline = typeof navigator !== "undefined" ? navigator.onLine : true;
    this.startOnlineListener();
    // Flush pending errors on page load
    this.flushPendingOnLoad();
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
   * Errors that fail to send are re-queued with exponential backoff retry.
   */
  private async flush(): Promise<void> {
    // Check if we're paused due to consecutive failures
    if (Date.now() < this.pausedUntil) {
      return;
    }

    if (this.queue.size() === 0) return;

    const errors = this.queue.drain();

    try {
      const response = await fetch(ERRORS_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(errors),
      });

      if (!response.ok) {
        // Backend rejected: re-queue and schedule retry
        this.handleFailure(errors);
      } else {
        // Success: reset retry state
        this.resetRetryState();
      }
    } catch {
      // Network failure: re-queue and schedule retry
      this.handleFailure(errors);
    }
  }

  /**
   * Handle a flush failure by re-queuing errors and scheduling retry.
   */
  private handleFailure(errors: StructuredError[]): void {
    // Re-queue errors
    errors.forEach((e) => this.queue.push(e));

    this.consecutiveFailures++;

    if (this.consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
      // Pause for 5 minutes after 5 consecutive failures
      this.pausedUntil = Date.now() + PAUSE_DURATION;
      this.consecutiveFailures = 0;
      this.retryDelay = INITIAL_RETRY_DELAY;
    } else {
      // Schedule retry with exponential backoff
      this.scheduleRetry();
    }
  }

  /**
   * Schedule a retry flush with exponential backoff.
   */
  private scheduleRetry(): void {
    if (this.flushTimeoutId !== null) {
      clearTimeout(this.flushTimeoutId);
    }

    this.flushTimeoutId = setTimeout(() => {
      void this.flush();
    }, this.retryDelay);

    // Double the delay for next retry, up to max
    this.retryDelay = Math.min(this.retryDelay * 2, MAX_RETRY_DELAY);
  }

  /**
   * Reset retry state after successful flush.
   */
  private resetRetryState(): void {
    this.consecutiveFailures = 0;
    this.retryDelay = INITIAL_RETRY_DELAY;
    this.pausedUntil = 0;

    if (this.flushTimeoutId !== null) {
      clearTimeout(this.flushTimeoutId);
      this.flushTimeoutId = null;
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
      // Reset retry state on reconnect
      this.resetRetryState();
      // Flush without blocking the event handler
      void this.flush();
    });

    window.addEventListener("offline", () => {
      this.isOnline = false;
    });
  }

  /**
   * Flush pending errors on page load.
   * Checks localStorage for any errors that were not sent before page unload.
   */
  private flushPendingOnLoad(): void {
    if (typeof window === "undefined") return;

    // Check if there are pending errors and we're online
    if (this.isOnline && this.queue.size() > 0) {
      // Small delay to ensure page is fully loaded
      setTimeout(() => {
        void this.flush();
      }, 100);
    }
  }
}

// Singleton — import and use directly across the app
export const errorReporter = new ErrorReporter();

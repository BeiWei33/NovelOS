/**
 * Error queue backed by localStorage with FIFO eviction.
 *
 * Stores structured errors locally when the network is unavailable,
 * then drains them when connectivity is restored.
 */

import type { StructuredError } from "./error";

const MAX_QUEUE_SIZE = 100;
const STORAGE_KEY = "novelos_error_queue";

export class ErrorQueue {
  private queue: StructuredError[] = [];

  constructor() {
    this.load();
  }

  /**
   * Add an error to the queue. If the queue exceeds MAX_QUEUE_SIZE,
   * evict the oldest entry (FIFO).
   */
  push(error: StructuredError): void {
    this.queue.push(error);

    if (this.queue.length > MAX_QUEUE_SIZE) {
      this.queue.shift(); // Remove oldest
    }

    this.persist();
  }

  /**
   * Return all errors and clear the queue.
   */
  drain(): StructuredError[] {
    const errors = [...this.queue];
    this.queue = [];
    this.persist();
    return errors;
  }

  /**
   * Return the current queue size without mutating it.
   */
  size(): number {
    return this.queue.length;
  }

  /**
   * Clear all errors from the queue.
   */
  clear(): void {
    this.queue = [];
    this.persist();
  }

  private load(): void {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          this.queue = parsed;
        }
      }
    } catch (err) {
      console.warn("Failed to load error queue from localStorage:", err);
      this.queue = [];
    }
  }

  private persist(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.queue));
    } catch (err) {
      console.warn("Failed to persist error queue to localStorage:", err);
    }
  }
}

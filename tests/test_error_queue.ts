/**
 * Unit tests for ErrorQueue.
 *
 * NOTE: This project does not have Jest configured yet. These tests are
 * written for future reference and can be run manually or by setting up
 * a test runner like Vitest or Jest.
 *
 * To verify manually:
 * 1. Import ErrorQueue in a browser console or Next.js page
 * 2. Call push(), drain(), size(), clear() and inspect localStorage
 * 3. Confirm FIFO eviction when pushing > 100 errors
 */

import { ErrorQueue } from "../frontend/src/lib/error-queue";
import type { StructuredError } from "../frontend/src/lib/error";

describe("ErrorQueue", () => {
  let queue: ErrorQueue;

  const createMockError = (message: string): StructuredError => ({
    type: "api",
    severity: "error",
    message,
    fingerprint: `api:${message.slice(0, 50)}`,
    context: {
      page: "test",
      action: "unit-test",
      timestamp: new Date().toISOString(),
    },
  });

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    queue = new ErrorQueue();
  });

  test("push adds an error to the queue", () => {
    const error = createMockError("Test error");
    queue.push(error);
    expect(queue.size()).toBe(1);
  });

  test("drain returns all errors and clears the queue", () => {
    queue.push(createMockError("Error 1"));
    queue.push(createMockError("Error 2"));
    queue.push(createMockError("Error 3"));

    const drained = queue.drain();
    expect(drained).toHaveLength(3);
    expect(queue.size()).toBe(0);
  });

  test("FIFO eviction when exceeding MAX_QUEUE_SIZE", () => {
    // Push 105 errors (exceeds max of 100)
    for (let i = 0; i < 105; i++) {
      queue.push(createMockError(`Error ${i}`));
    }

    expect(queue.size()).toBe(100);

    // The first 5 errors should be evicted
    const drained = queue.drain();
    expect(drained[0].message).toBe("Error 5"); // Error 0-4 were evicted
    expect(drained[drained.length - 1].message).toBe("Error 104");
  });

  test("clear empties the queue", () => {
    queue.push(createMockError("Error 1"));
    queue.push(createMockError("Error 2"));
    queue.clear();

    expect(queue.size()).toBe(0);
  });

  test("persistence across instances", () => {
    queue.push(createMockError("Persistent error"));
    expect(queue.size()).toBe(1);

    // Create a new instance — should load from localStorage
    const queue2 = new ErrorQueue();
    expect(queue2.size()).toBe(1);

    const drained = queue2.drain();
    expect(drained[0].message).toBe("Persistent error");
  });

  test("handles corrupted localStorage gracefully", () => {
    localStorage.setItem("novelos_error_queue", "not valid JSON");
    const queue3 = new ErrorQueue();
    expect(queue3.size()).toBe(0); // Should start empty if parse fails
  });
});

// ────────────────────────────────────────────────────────────────────────────
// Manual verification steps (no test runner):
// ────────────────────────────────────────────────────────────────────────────
//
// 1. Open the browser console on a Next.js page
// 2. Import: import { ErrorQueue } from '@/lib/error-queue'
// 3. Create instance: const q = new ErrorQueue()
// 4. Push errors: q.push({ type: 'api', severity: 'error', message: 'test', ... })
// 5. Check size: q.size()
// 6. Drain: q.drain()
// 7. Inspect localStorage: localStorage.getItem('novelos_error_queue')
// 8. Test FIFO: Push 105 errors and verify oldest are evicted

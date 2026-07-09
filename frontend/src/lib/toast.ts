/**
 * Toast notification system
 */

let toastContainer: HTMLDivElement | null = null;

function ensureContainer() {
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toast-container";
    toastContainer.className = "fixed bottom-4 right-4 z-50 flex flex-col gap-2";
    document.body.appendChild(toastContainer);
  }
  return toastContainer;
}

export type ToastType = "success" | "error" | "info";

export interface ToastOptions {
  type?: ToastType;
  duration?: number;
}

export function showToast(message: string, options: ToastOptions = {}) {
  const { type = "info", duration = 3000 } = options;
  const container = ensureContainer();

  const toast = document.createElement("div");
  const bgColor = type === "error"
    ? "bg-red-900/90 border-red-700"
    : type === "success"
    ? "bg-green-900/90 border-green-700"
    : "bg-gray-800/90 border-gray-700";

  toast.className = `px-4 py-2 rounded-lg border ${bgColor} text-sm text-gray-100 shadow-lg transform transition-all duration-300 translate-x-full opacity-0`;
  toast.textContent = message;

  container.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => {
    toast.classList.remove("translate-x-full", "opacity-0");
  });

  // Remove after duration
  setTimeout(() => {
    toast.classList.add("translate-x-full", "opacity-0");
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

"use client";

import { useState } from "react";
import type { Scene, ScenePlanning } from "@/types/domain";
import { api } from "@/lib/api";
import { captureError } from "@/lib/error";

interface ScenePlanningPanelProps {
  scene: Scene;
  onUpdate: () => Promise<void>;
}

const PLANNING_FIELDS: Array<{
  key: keyof ScenePlanning;
  label: string;
  placeholder: string;
}> = [
  {
    key: "goal",
    label: "目标",
    placeholder: "这个场景要达成什么叙事目标？",
  },
  {
    key: "conflict",
    label: "冲突",
    placeholder: "场景中的核心冲突是什么？",
  },
  {
    key: "stakes",
    label: "赌注",
    placeholder: "如果失败，角色会失去什么？",
  },
  {
    key: "turning_point",
    label: "转折点",
    placeholder: "场景中的关键转折是什么？",
  },
  {
    key: "ending",
    label: "结局",
    placeholder: "场景如何结束？留下什么悬念？",
  },
  {
    key: "foreshadow",
    label: "伏笔",
    placeholder: "是否埋下伏笔？",
  },
];

export function ScenePlanningPanel({
  scene,
  onUpdate,
}: ScenePlanningPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [planning, setPlanning] = useState<ScenePlanning>(
    scene.planning || {}
  );
  const [saving, setSaving] = useState(false);
  const [aiPlanning, setAiPlanning] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSave() {
    setSaving(true);
    setMessage("");
    try {
      await api.updateScene(scene.id, { planning });
      setMessage("已保存");
      await onUpdate();
    } catch (e) {
      setMessage("保存失败");
      captureError(e, { page: "scene-planning", action: "save", sceneId: scene.id });
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(""), 2000);
    }
  }

  async function handleAiPlan() {
    setAiPlanning(true);
    setMessage("");
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/skills/plan-scene/${scene.id}`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(err);
      }
      const data = await res.json();
      setPlanning(data.planning || {});
      setMessage("AI 规划完成");
      await onUpdate();
    } catch (e) {
      setMessage("AI 规划失败");
      captureError(e, { page: "scene-planning", action: "ai-plan", sceneId: scene.id });
    } finally {
      setAiPlanning(false);
      setTimeout(() => setMessage(""), 3000);
    }
  }

  function updateField(key: keyof ScenePlanning, value: string) {
    setPlanning((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div className="border-t border-gray-800">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-sm hover:bg-gray-800/50 transition-colors"
      >
        <span className="font-medium text-gray-300">场景规划</span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`text-gray-500 transition-transform ${
            expanded ? "rotate-180" : ""
          }`}
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {/* Content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* AI Plan button */}
          <div className="flex items-center gap-2 pt-2">
            <button
              onClick={handleAiPlan}
              disabled={aiPlanning}
              className="px-3 py-1.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 rounded text-xs font-medium transition-colors"
            >
              {aiPlanning ? "AI 规划中..." : "AI 自动规划"}
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded text-xs font-medium transition-colors"
            >
              {saving ? "保存中..." : "保存规划"}
            </button>
            {message && (
              <span
                className={`text-xs ${
                  message.includes("完成") || message.includes("已保存")
                    ? "text-green-400"
                    : "text-red-400"
                }`}
              >
                {message}
              </span>
            )}
          </div>

          {/* Fields */}
          <div className="grid gap-3">
            {PLANNING_FIELDS.map(({ key, label, placeholder }) => (
              <div key={key}>
                <label className="block text-xs text-gray-500 mb-1">
                  {label}
                </label>
                <textarea
                  value={planning[key] || ""}
                  onChange={(e) => updateField(key, e.target.value)}
                  placeholder={placeholder}
                  rows={2}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600 resize-none"
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

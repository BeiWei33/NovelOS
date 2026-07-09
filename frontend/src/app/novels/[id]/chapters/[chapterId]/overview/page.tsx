"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { showToast } from "@/lib/toast";
import type { Chapter, Scene } from "@/types/domain";

type Tab = "overview" | "scenes";

export default function ChapterOverview() {
  const params = useParams();
  const router = useRouter();
  const novelId = params.id as string;
  const chapterId = params.chapterId as string;

  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [regenerating, setRegenerating] = useState(false);

  // Edit planning state
  const [editingPlanning, setEditingPlanning] = useState(false);
  const [planningGoal, setPlanningGoal] = useState("");
  const [planningTheme, setPlanningTheme] = useState("");
  const [planningScenePlan, setPlanningScenePlan] = useState("");
  const [savingPlanning, setSavingPlanning] = useState(false);

  async function loadChapter() {
    setLoading(true);
    try {
      const ch = await api.getChapter(chapterId);
      setChapter(ch);
      setPlanningGoal(ch.planning?.goal || "");
      setPlanningTheme(ch.planning?.theme || "");
      setPlanningScenePlan((ch.planning?.scene_plan || []).join("\n"));
    } catch (e) {
      const message = e instanceof Error ? e.message : "加载失败";
      showToast(`加载章节失败: ${message}`, { type: "error" });
    } finally {
      setLoading(false);
    }
  }

  async function loadScenes() {
    try {
      const list = await api.listScenes(chapterId);
      setScenes(list);
    } catch (e) {
      // Ignore scene loading errors on overview
    }
  }

  useEffect(() => {
    loadChapter();
    loadScenes();
  }, [chapterId]);

  async function handleRegenerateSummary() {
    setRegenerating(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/skills/regenerate-summary/${chapterId}`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(await res.text());
      await loadChapter();
      showToast("摘要已重新生成", { type: "success" });
    } catch (e) {
      const message = e instanceof Error ? e.message : "生成失败";
      showToast(`重新生成摘要失败: ${message}`, { type: "error" });
    } finally {
      setRegenerating(false);
    }
  }

  async function handleSavePlanning() {
    setSavingPlanning(true);
    try {
      const scenePlanLines = planningScenePlan.split("\n").filter(Boolean);
      await api.updateChapter(chapterId, {
        planning: {
          goal: planningGoal || undefined,
          theme: planningTheme || undefined,
          scene_plan: scenePlanLines.length > 0 ? scenePlanLines : undefined,
        },
      });
      await loadChapter();
      setEditingPlanning(false);
      showToast("规划已保存", { type: "success" });
    } catch (e) {
      const message = e instanceof Error ? e.message : "保存失败";
      showToast(`保存规划失败: ${message}`, { type: "error" });
    } finally {
      setSavingPlanning(false);
    }
  }

  function getConsistencyColor(score?: number): string {
    if (score === undefined) return "bg-gray-700 text-gray-300";
    if (score >= 90) return "bg-green-900/50 text-green-400 border-green-600/30";
    if (score >= 70) return "bg-yellow-900/50 text-yellow-400 border-yellow-600/30";
    if (score >= 50) return "bg-orange-900/50 text-orange-400 border-orange-600/30";
    return "bg-red-900/50 text-red-400 border-red-600/30";
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center">
        <p className="text-gray-500">加载中...</p>
      </div>
    );
  }

  if (!chapter) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col items-center justify-center gap-4">
        <p className="text-red-400">章节未找到</p>
        <button
          onClick={() => router.push(`/novels/${novelId}`)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium"
        >
          返回小说
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <a
            href={`/novels/${novelId}`}
            className="text-gray-500 hover:text-gray-300 text-sm"
          >
            ← 返回
          </a>
          <h1 className="text-xl font-bold">{chapter.title}</h1>
          <span className="text-sm text-gray-500">#{chapter.order}</span>
          <span className="text-xs px-2 py-0.5 bg-gray-800 rounded text-gray-400">
            {chapter.metadata?.status || "draft"}
          </span>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-gray-800 px-6">
        <div className="max-w-5xl mx-auto flex gap-1">
          {[
            { key: "overview", label: "概览" },
            { key: "scenes", label: "场景编辑器" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => {
                setActiveTab(tab.key as Tab);
                if (tab.key === "scenes") {
                  router.push(`/novels/${novelId}/chapters/${chapterId}`);
                }
              }}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-gray-500 hover:text-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-6 py-6">
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => router.push(`/novels/${novelId}/chapters/${chapterId}`)}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-500 rounded-lg text-sm font-medium transition-colors"
              >
                一键生成整章
              </button>
              <button
                onClick={handleRegenerateSummary}
                disabled={regenerating}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 rounded-lg text-sm font-medium transition-colors"
              >
                {regenerating ? "生成中..." : "重新生成摘要"}
              </button>
              <button
                onClick={() => setEditingPlanning(true)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
              >
                编辑规划
              </button>
            </div>

            {/* Three-level Summary */}
            <section className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">三级摘要</h2>
              <div className="space-y-4">
                {chapter.summary?.one_line && (
                  <div>
                    <h3 className="text-sm text-gray-400 mb-1">一句话摘要</h3>
                    <p className="text-sm">{chapter.summary.one_line}</p>
                  </div>
                )}
                {chapter.summary?.one_paragraph && (
                  <div>
                    <h3 className="text-sm text-gray-400 mb-1">一段话摘要</h3>
                    <p className="text-sm">{chapter.summary.one_paragraph}</p>
                  </div>
                )}
                {chapter.summary?.one_page && (
                  <div>
                    <h3 className="text-sm text-gray-400 mb-1">一页摘要</h3>
                    <p className="text-sm whitespace-pre-wrap">{chapter.summary.one_page}</p>
                  </div>
                )}
                {!chapter.summary?.one_line && !chapter.summary?.one_paragraph && !chapter.summary?.one_page && (
                  <p className="text-gray-500 text-sm">暂无摘要，点击"重新生成摘要"按钮生成</p>
                )}
              </div>
            </section>

            {/* Consistency Score */}
            <section className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">一致性评分</h2>
              <div className="flex items-center gap-4">
                <div className={`px-4 py-2 rounded-lg border ${getConsistencyColor(chapter.consistency?.score)}`}>
                  <span className="text-2xl font-bold">{chapter.consistency?.score || "--"}</span>
                  <span className="text-sm ml-1">%</span>
                </div>
                {chapter.consistency?.score !== undefined && (
                  <span className="text-sm text-gray-400">
                    {chapter.consistency.score >= 90 ? "优秀"
                      : chapter.consistency.score >= 70 ? "良好"
                      : chapter.consistency.score >= 50 ? "一般"
                      : "需要修复"}
                  </span>
                )}
              </div>
              {chapter.consistency?.issues && chapter.consistency.issues.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm text-gray-400 mb-2">问题列表</h3>
                  <ul className="space-y-1">
                    {chapter.consistency.issues.map((issue, i) => (
                      <li key={i} className="text-sm text-red-400 flex items-start gap-2">
                        <span className="text-red-500">!</span>
                        {issue}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {chapter.consistency?.fixed && chapter.consistency.fixed.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm text-gray-400 mb-2">已修复</h3>
                  <ul className="space-y-1">
                    {chapter.consistency.fixed.map((fix, i) => (
                      <li key={i} className="text-sm text-green-400 flex items-start gap-2">
                        <span className="text-green-500">+</span>
                        {fix}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {chapter.consistency?.warnings && chapter.consistency.warnings.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm text-gray-400 mb-2">警告</h3>
                  <ul className="space-y-1">
                    {chapter.consistency.warnings.map((warn, i) => (
                      <li key={i} className="text-sm text-yellow-400 flex items-start gap-2">
                        <span className="text-yellow-500">?</span>
                        {warn}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>

            {/* Chapter Facts */}
            <section className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">章节 Facts</h2>
              <div className="grid gap-4">
                {chapter.chapter_facts?.relationship_changes && chapter.chapter_facts.relationship_changes.length > 0 && (
                  <div>
                    <h3 className="text-sm text-indigo-400 mb-2">人物关系变化</h3>
                    <ul className="space-y-1">
                      {chapter.chapter_facts.relationship_changes.map((c, i) => (
                        <li key={i} className="text-sm text-gray-300">{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {chapter.chapter_facts?.world_changes && chapter.chapter_facts.world_changes.length > 0 && (
                  <div>
                    <h3 className="text-sm text-emerald-400 mb-2">世界观变化</h3>
                    <ul className="space-y-1">
                      {chapter.chapter_facts.world_changes.map((c, i) => (
                        <li key={i} className="text-sm text-gray-300">{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {chapter.chapter_facts?.timeline_changes && chapter.chapter_facts.timeline_changes.length > 0 && (
                  <div>
                    <h3 className="text-sm text-amber-400 mb-2">时间线变化</h3>
                    <ul className="space-y-1">
                      {chapter.chapter_facts.timeline_changes.map((c, i) => (
                        <li key={i} className="text-sm text-gray-300">{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {chapter.chapter_facts?.new_information && chapter.chapter_facts.new_information.length > 0 && (
                  <div>
                    <h3 className="text-sm text-violet-400 mb-2">新信息</h3>
                    <ul className="space-y-1">
                      {chapter.chapter_facts.new_information.map((c, i) => (
                        <li key={i} className="text-sm text-gray-300">{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {!chapter.chapter_facts?.relationship_changes?.length &&
                 !chapter.chapter_facts?.world_changes?.length &&
                 !chapter.chapter_facts?.timeline_changes?.length &&
                 !chapter.chapter_facts?.new_information?.length && (
                  <p className="text-gray-500 text-sm">暂无章节 facts</p>
                )}
              </div>
            </section>

            {/* Planning */}
            <section className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">章节规划</h2>
              <div className="space-y-3">
                {chapter.planning?.goal && (
                  <div>
                    <h3 className="text-sm text-gray-400 mb-1">目标</h3>
                    <p className="text-sm">{chapter.planning.goal}</p>
                  </div>
                )}
                {chapter.planning?.theme && (
                  <div>
                    <h3 className="text-sm text-gray-400 mb-1">主题</h3>
                    <p className="text-sm">{chapter.planning.theme}</p>
                  </div>
                )}
                {chapter.planning?.scene_plan && chapter.planning.scene_plan.length > 0 && (
                  <div>
                    <h3 className="text-sm text-gray-400 mb-2">场景规划</h3>
                    <ul className="space-y-1">
                      {chapter.planning.scene_plan.map((s, i) => (
                        <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                          <span className="text-gray-500">{i + 1}.</span>
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {!chapter.planning?.goal && !chapter.planning?.theme && !chapter.planning?.scene_plan?.length && (
                  <p className="text-gray-500 text-sm">暂无规划，点击"编辑规划"按钮添加</p>
                )}
              </div>
            </section>

            {/* Scene List */}
            <section className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">场景列表</h2>
              {scenes.length === 0 ? (
                <p className="text-gray-500 text-sm">暂无场景</p>
              ) : (
                <div className="space-y-2">
                  {scenes.map((s) => (
                    <div
                      key={s.id}
                      className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg"
                    >
                      <span className="w-8 h-8 flex items-center justify-center bg-gray-700 rounded text-sm text-gray-400">
                        #{s.order}
                      </span>
                      <div className="flex-1">
                        <span className="text-sm font-medium">{s.planning?.goal || `场景 ${s.order}`}</span>
                      </div>
                      <span className="text-xs text-gray-500">v{s.version}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Metadata */}
            <section className="text-sm text-gray-500 flex gap-6">
              <span>创建于: {new Date(chapter.created_at).toLocaleString()}</span>
              <span>更新于: {new Date(chapter.updated_at).toLocaleString()}</span>
            </section>
          </div>
        )}
      </main>

      {/* Edit Planning Modal */}
      {editingPlanning && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">编辑章节规划</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">目标</label>
                <input
                  value={planningGoal}
                  onChange={(e) => setPlanningGoal(e.target.value)}
                  placeholder="本章要达成的叙事目标..."
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">主题</label>
                <input
                  value={planningTheme}
                  onChange={(e) => setPlanningTheme(e.target.value)}
                  placeholder="本章的核心主题..."
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">场景规划（每行一个）</label>
                <textarea
                  value={planningScenePlan}
                  onChange={(e) => setPlanningScenePlan(e.target.value)}
                  placeholder="场景1规划&#10;场景2规划&#10;场景3规划..."
                  rows={6}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600 resize-none"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setEditingPlanning(false)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300"
              >
                取消
              </button>
              <button
                onClick={handleSavePlanning}
                disabled={savingPlanning}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded-lg text-sm font-medium"
              >
                {savingPlanning ? "保存中..." : "保存"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
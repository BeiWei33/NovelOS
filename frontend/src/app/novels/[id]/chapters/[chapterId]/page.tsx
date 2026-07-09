"use client";

import { useParams } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { Scene, Style } from "@/types/domain";
import { captureError } from "@/lib/error";
import { NavigationTree } from "@/components/NavigationTree";
import { ScenePlanningPanel } from "@/components/ScenePlanningPanel";

export default function ChapterDetail() {
  const params = useParams();
  const chapterId = params.chapterId as string;
  const novelId = params.id as string;

  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedScene, setSelectedScene] = useState<Scene | null>(null);
  const [showCreateScene, setShowCreateScene] = useState(false);
  const [showGenerateChapter, setShowGenerateChapter] = useState(false);
  const [generatingChapter, setGeneratingChapter] = useState(false);
  const [generateGoal, setGenerateGoal] = useState("");
  const [generateTheme, setGenerateTheme] = useState("");
  const [styles, setStyles] = useState<Style[]>([]);
  const [navCollapsed, setNavCollapsed] = useState(false);

  async function loadScenes() {
    setLoading(true);
    try {
      const list = await api.listScenes(chapterId);
      setScenes(list);
      const stylesList = await api.listStyles(novelId);
      setStyles(stylesList);
    } catch (e) {
      captureError(e, { page: "chapter-detail", action: "load-scenes", novelId, chapterId });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadScenes();
  }, [chapterId]);

  async function handleCreateScene() {
    try {
      const scene = await api.createScene({
        chapter_id: chapterId,
        order: scenes.length + 1,
      });
      setShowCreateScene(false);
      await loadScenes();
      setSelectedScene(scene);
    } catch (e) {
      captureError(e, { page: "chapter-detail", action: "create-scene", novelId, chapterId });
    }
  }

  async function handleGenerateChapter() {
    setGeneratingChapter(true);
    try {
      await api.generateChapter(chapterId, {
        goal: generateGoal,
        theme: generateTheme,
      });
      setShowGenerateChapter(false);
      setGenerateGoal("");
      setGenerateTheme("");
      await loadScenes();
    } catch (e) {
      captureError(e, { page: "chapter-detail", action: "generate-chapter", novelId, chapterId });
      alert("整章生成失败，请查看控制台日志");
    } finally {
      setGeneratingChapter(false);
    }
  }

  function handleSceneSelect(scene: Scene) {
    setSelectedScene(scene);
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex">
      {/* Left: Navigation Tree */}
      {navCollapsed ? (
        <button
          onClick={() => setNavCollapsed(false)}
          className="w-12 h-12 flex items-center justify-center bg-gray-900 border-r border-gray-800 text-gray-400 hover:text-gray-200 transition-colors shrink-0"
          title="展开导航"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
      ) : (
        <NavigationTree
          novelId={novelId}
          currentChapterId={chapterId}
          currentSceneId={selectedScene?.id}
          onSceneSelect={handleSceneSelect}
        />
      )}

      {/* Right: Scene editor */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Tabs */}
        <div className="border-b border-gray-800 px-4 py-2 flex items-center gap-2">
          <a
            href={`/novels/${novelId}/chapters/${chapterId}/overview`}
            className="px-3 py-1.5 text-sm text-gray-400 hover:text-gray-200 transition-colors"
          >
            概览
          </a>
          <span className="px-3 py-1.5 text-sm font-medium text-indigo-400 border-b-2 border-indigo-500">
            场景编辑器
          </span>
          <div className="flex-1" />
        </div>
        {selectedScene ? (
          <SceneEditor
            scene={selectedScene}
            onSave={loadScenes}
            novelId={novelId}
            styles={styles}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg mb-2">选择一个场景开始编辑</p>
              <p className="text-sm">或在左侧导航创建新场景</p>
            </div>
          </div>
        )}
      </main>

      {showCreateScene && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-sm">
            <h3 className="text-lg font-semibold mb-4">新建场景</h3>
            <p className="text-sm text-gray-400 mb-4">
              将创建第 {scenes.length + 1} 个场景
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowCreateScene(false)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300"
              >
                取消
              </button>
              <button
                onClick={handleCreateScene}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {showGenerateChapter && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">一键生成整章</h3>
            <p className="text-sm text-gray-400 mb-4">
              将运行完整工作流：规划场景 → AI 写作 → 质量检查 → 生成摘要
            </p>
            <div className="space-y-3 mb-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  目标（可选）
                </label>
                <input
                  type="text"
                  value={generateGoal}
                  onChange={(e) => setGenerateGoal(e.target.value)}
                  placeholder="本章要达成的叙事目标..."
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-violet-500 placeholder-gray-600"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  主题（可选）
                </label>
                <input
                  type="text"
                  value={generateTheme}
                  onChange={(e) => setGenerateTheme(e.target.value)}
                  placeholder="本章的核心主题..."
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-violet-500 placeholder-gray-600"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowGenerateChapter(false);
                  setGenerateGoal("");
                  setGenerateTheme("");
                }}
                disabled={generatingChapter}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300 disabled:opacity-40"
              >
                取消
              </button>
              <button
                onClick={handleGenerateChapter}
                disabled={generatingChapter}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 rounded-lg text-sm font-medium"
              >
                {generatingChapter ? "生成中，请稍候..." : "开始生成"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SceneEditor({
  scene,
  onSave,
  novelId,
  styles,
}: {
  scene: Scene;
  onSave: () => Promise<void>;
  novelId: string;
  styles: Style[];
}) {
  const [blocks, setBlocks] = useState(scene.document.blocks);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [polishing, setPolishing] = useState(false);
  const [message, setMessage] = useState("");
  const [qualityResult, setQualityResult] = useState<{
    patches_applied: number;
    issues: Array<{ type: string; severity: string; description: string }>;
  } | null>(null);
  const [knowledgeStatus, setKnowledgeStatus] = useState<{
    status: "not_generated" | "stale" | "up_to_date";
  } | null>(null);

  // Sync blocks when scene changes
  useEffect(() => {
    setBlocks(scene.document.blocks);
  }, [scene.id, scene.document.blocks]);

  // Load knowledge status on mount
  useEffect(() => {
    async function loadKnowledgeStatus() {
      try {
        const status = await api.getSceneKnowledgeStatus(scene.id);
        setKnowledgeStatus({ status: status.status });
      } catch (e) {
        captureError(e, { page: "chapter-detail", action: "load-knowledge-status", sceneId: scene.id });
      }
    }
    loadKnowledgeStatus();
  }, [scene.id, scene.version]);

  async function handleSave() {
    setSaving(true);
    setMessage("");
    try {
      await api.updateScene(scene.id, { document: { blocks } });
      setMessage("已保存");
      await onSave();
    } catch (e) {
      setMessage("保存失败");
      captureError(e, { page: "chapter-detail", action: "save-scene", sceneId: scene.id });
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(""), 2000);
    }
  }

  async function handleAiWrite() {
    setGenerating(true);
    setMessage("");
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/skills/scene-writer/${scene.id}`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(err);
      }
      const data = await res.json();
      setBlocks(data.document.blocks);
      setMessage("AI 生成完成");
      await onSave();
    } catch (e) {
      setMessage("生成失败");
      captureError(e, { page: "chapter-detail", action: "ai-write", sceneId: scene.id });
    } finally {
      setGenerating(false);
      setTimeout(() => setMessage(""), 3000);
    }
  }

  async function handlePolish() {
    setPolishing(true);
    setMessage("");
    setQualityResult(null);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/skills/polish/${scene.id}`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(err);
      }
      const data = await res.json();
      setBlocks(data.document?.blocks || blocks);
      setQualityResult({
        patches_applied: data.patches_applied || 0,
        issues: data.issues || [],
      });
      setMessage(`润色完成: ${data.patches_applied} 处修改, ${data.issues_count} 个问题`);
      await onSave();
    } catch (e) {
      setMessage("润色失败");
      captureError(e, { page: "chapter-detail", action: "polish-scene", sceneId: scene.id });
    } finally {
      setPolishing(false);
    }
  }

  function addBlock(type: string = "narration") {
    setBlocks([
      ...blocks,
      {
        id: crypto.randomUUID(),
        type: type as any,
        content: "",
      },
    ]);
  }

  function updateBlock(index: number, content: string) {
    const updated = [...blocks];
    updated[index] = { ...updated[index], content };
    setBlocks(updated);
  }

  function removeBlock(index: number) {
    setBlocks(blocks.filter((_, i) => i !== index));
  }

  function changeBlockType(index: number, type: string) {
    const updated = [...blocks];
    updated[index] = { ...updated[index], type: type as any };
    setBlocks(updated);
  }

  const blockStyles: Record<string, string> = {
    narration: "border-l-4 border-gray-600",
    dialogue: "border-l-4 border-green-600",
    description: "border-l-4 border-blue-600",
    inner_monologue: "border-l-4 border-purple-600 italic",
    emotion: "border-l-4 border-pink-600",
    letter: "border-l-4 border-amber-600 font-serif",
    phone_message: "border-l-4 border-cyan-600",
    flashback: "border-l-4 border-orange-600 opacity-80",
    system_message: "border-l-4 border-red-600 bg-red-900/10",
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Toolbar */}
      <div className="border-b border-gray-800 px-4 py-3 flex items-center gap-2 flex-wrap">
        <span className="text-sm text-gray-400">
          v{scene.version}
        </span>
        {/* Current style badge */}
        {styles.length > 0 && (
          <span className="text-xs px-2 py-0.5 bg-gray-800 rounded text-gray-400">
            风格: {styles[0].name}
          </span>
        )}
        {/* Knowledge status badge */}
        {knowledgeStatus && (
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            knowledgeStatus.status === "up_to_date"
              ? "bg-green-900/50 text-green-400"
              : knowledgeStatus.status === "stale"
              ? "bg-yellow-900/50 text-yellow-400"
              : "bg-gray-800 text-gray-500"
          }`}>
            {knowledgeStatus.status === "up_to_date" ? "知识就绪"
              : knowledgeStatus.status === "stale" ? "知识过期"
              : "未生成知识"}
          </span>
        )}
        <div className="flex-1" />
        <button
          onClick={() => addBlock("narration")}
          className="px-2 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded"
        >
          + 叙述
        </button>
        <button
          onClick={() => addBlock("dialogue")}
          className="px-2 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded"
        >
          + 对话
        </button>
        <button
          onClick={() => addBlock("description")}
          className="px-2 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded"
        >
          + 描写
        </button>
        <button
          onClick={() => addBlock("inner_monologue")}
          className="px-2 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded"
        >
          + 内心
        </button>
        <div className="w-px h-5 bg-gray-700 mx-1" />
        <button
          onClick={handleAiWrite}
          disabled={generating}
          className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 rounded text-sm font-medium transition-colors"
        >
          {generating ? "生成中..." : "AI 写场景"}
        </button>
        <button
          onClick={handlePolish}
          disabled={polishing}
          className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 disabled:opacity-40 rounded text-sm font-medium transition-colors"
        >
          {polishing ? "润色中..." : "一键润色"}
        </button>
        <div className="w-px h-5 bg-gray-700 mx-1" />
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded text-sm font-medium transition-colors"
        >
          {saving ? "保存中..." : "保存"}
        </button>
        {message && (
          <span
            className={`text-sm ${
              message === "已保存" ? "text-green-400" : "text-red-400"
            }`}
          >
            {message}
          </span>
        )}
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {/* Blocks */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {blocks.length === 0 ? (
            <div className="text-center py-12 text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
              <p className="mb-3">场景为空</p>
              <p className="text-sm">点击上方按钮添加段落</p>
            </div>
          ) : (
            blocks.map((block, i) => (
              <div
                key={block.id || i}
                className={`group relative rounded-lg bg-gray-900/50 ${blockStyles[block.type] || blockStyles.narration}`}
              >
                {/* Type selector */}
                <div className="flex items-center gap-1 px-3 pt-1.5 pb-0.5">
                  <select
                    value={block.type}
                    onChange={(e) => changeBlockType(i, e.target.value)}
                    className="text-xs bg-transparent text-gray-500 border-none focus:outline-none cursor-pointer"
                  >
                    {[
                      "narration",
                      "dialogue",
                      "description",
                      "inner_monologue",
                      "emotion",
                      "letter",
                      "phone_message",
                      "flashback",
                      "system_message",
                    ].map((t) => (
                      <option key={t} value={t} className="bg-gray-800">
                        {t}
                      </option>
                    ))}
                  </select>
                  <div className="flex-1" />
                  <button
                    onClick={() => removeBlock(i)}
                    className="opacity-0 group-hover:opacity-100 text-xs text-red-400 hover:text-red-300 transition-opacity"
                  >
                    删除
                  </button>
                </div>
                {/* Content */}
                <textarea
                  value={block.content}
                  onChange={(e) => updateBlock(i, e.target.value)}
                  placeholder="在此输入文本..."
                  className="w-full bg-transparent px-3 pb-3 pt-1 text-sm resize-none focus:outline-none placeholder-gray-600 min-h-[60px]"
                />
              </div>
            ))
          )}
        </div>

        {/* Quality Result Panel */}
        {qualityResult && (qualityResult.patches_applied > 0 || qualityResult.issues.length > 0) && (
          <div className="border-t border-gray-800 p-4 bg-gray-900/50">
            <h4 className="text-sm font-medium mb-2">润色结果</h4>
            <div className="flex gap-4 text-sm">
              {qualityResult.patches_applied > 0 && (
                <span className="text-amber-400">
                  {qualityResult.patches_applied} 处 AI 痕迹已修复
                </span>
              )}
              {qualityResult.issues.length > 0 && (
                <span className="text-red-400">
                  {qualityResult.issues.length} 个一致性问题
                </span>
              )}
            </div>
            {qualityResult.issues.length > 0 && (
              <div className="mt-2 space-y-1">
                {qualityResult.issues.slice(0, 3).map((issue, i) => (
                  <div key={i} className="text-xs">
                    <span className={issue.severity === "error" ? "text-red-400" : "text-yellow-400"}>
                      [{issue.severity}]
                    </span>{" "}
                    <span className="text-gray-400">{issue.description}</span>
                  </div>
                ))}
                {qualityResult.issues.length > 3 && (
                  <div className="text-xs text-gray-500">
                    还有 {qualityResult.issues.length - 3} 个问题...
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Scene Planning Panel */}
        <ScenePlanningPanel scene={scene} onUpdate={onSave} />
      </div>
    </div>
  );
}

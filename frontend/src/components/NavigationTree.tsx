"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { Novel, Chapter, Scene } from "@/types/domain";
import { captureError } from "@/lib/error";

interface NavigationTreeProps {
  novelId: string;
  currentChapterId: string;
  currentSceneId?: string;
  onSceneSelect: (scene: Scene) => void;
  onChapterSelect?: (chapterId: string) => void;
}

interface ChapterWithScenes extends Chapter {
  scenes: Scene[];
}

export function NavigationTree({
  novelId,
  currentChapterId,
  currentSceneId,
  onSceneSelect,
  onChapterSelect,
}: NavigationTreeProps) {
  const [novel, setNovel] = useState<Novel | null>(null);
  const [chapters, setChapters] = useState<ChapterWithScenes[]>([]);
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(
    new Set([currentChapterId])
  );
  const [loading, setLoading] = useState(true);
  const [collapsed, setCollapsed] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [novelData, chaptersData] = await Promise.all([
        api.getNovel(novelId),
        api.listChapters(novelId),
      ]);
      setNovel(novelData);

      // Load scenes for each chapter
      const chaptersWithScenes = await Promise.all(
        chaptersData.map(async (chapter) => {
          try {
            const scenes = await api.listScenes(chapter.id);
            return { ...chapter, scenes };
          } catch {
            return { ...chapter, scenes: [] };
          }
        })
      );
      setChapters(chaptersWithScenes);
    } catch (e) {
      captureError(e, { page: "navigation-tree", action: "load-data", novelId });
    } finally {
      setLoading(false);
    }
  }, [novelId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  function toggleChapter(chapterId: string) {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      if (next.has(chapterId)) {
        next.delete(chapterId);
      } else {
        next.add(chapterId);
      }
      return next;
    });
  }

  if (collapsed) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        className="w-12 h-12 flex items-center justify-center bg-gray-900 border-r border-gray-800 text-gray-400 hover:text-gray-200 transition-colors"
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
    );
  }

  return (
    <aside className="w-64 border-r border-gray-800 flex flex-col bg-gray-900/50 shrink-0">
      {/* Header */}
      <div className="p-3 border-b border-gray-800 flex items-center gap-2">
        <button
          onClick={() => setCollapsed(true)}
          className="p-1 text-gray-500 hover:text-gray-300 transition-colors lg:hidden"
          title="折叠导航"
        >
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
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
        <a
          href={`/novels/${novelId}`}
          className="text-sm text-gray-500 hover:text-gray-300 flex items-center gap-1"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m15 18-6-6 6-6" />
          </svg>
          返回
        </a>
      </div>

      {/* Novel title */}
      <div className="p-3 border-b border-gray-800">
        <h2 className="text-sm font-semibold text-gray-200 truncate">
          {novel?.title || "加载中..."}
        </h2>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <p className="text-sm text-gray-500 text-center py-4">加载中...</p>
        ) : chapters.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">暂无章节</p>
        ) : (
          <div className="space-y-1">
            {chapters.map((chapter) => {
              const isExpanded = expandedChapters.has(chapter.id);
              const isCurrentChapter = chapter.id === currentChapterId;

              return (
                <div key={chapter.id}>
                  {/* Chapter item */}
                  <button
                    onClick={() => toggleChapter(chapter.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center gap-2 ${
                      isCurrentChapter
                        ? "bg-indigo-600/20 text-indigo-300"
                        : "text-gray-400 hover:bg-gray-800"
                    }`}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="12"
                      height="12"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className={`transition-transform ${
                        isExpanded ? "rotate-90" : ""
                      }`}
                    >
                      <path d="m9 18 6-6-6-6" />
                    </svg>
                    <span className="flex-1 truncate">
                      {chapter.order}. {chapter.title}
                    </span>
                    <span className="text-xs text-gray-600">
                      {chapter.scenes.length}
                    </span>
                  </button>

                  {/* Scene list */}
                  {isExpanded && chapter.scenes.length > 0 && (
                    <div className="ml-4 mt-1 space-y-0.5">
                      {chapter.scenes.map((scene) => {
                        const isCurrentScene = scene.id === currentSceneId;

                        return (
                          <button
                            key={scene.id}
                            onClick={() => onSceneSelect(scene)}
                            className={`w-full text-left px-3 py-1.5 rounded text-xs transition-colors ${
                              isCurrentScene
                                ? "bg-indigo-600/30 text-indigo-300"
                                : "text-gray-500 hover:bg-gray-800 hover:text-gray-300"
                            }`}
                          >
                            <span className="text-gray-600 mr-1">
                              #{scene.order}
                            </span>
                            {scene.planning?.goal || `场景 ${scene.order}`}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Collapse button (desktop) */}
      <div className="p-2 border-t border-gray-800 hidden lg:block">
        <button
          onClick={() => setCollapsed(true)}
          className="w-full px-3 py-1.5 text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded transition-colors"
        >
          收起导航
        </button>
      </div>
    </aside>
  );
}

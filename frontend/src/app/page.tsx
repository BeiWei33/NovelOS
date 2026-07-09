"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { Novel, Chapter, Scene } from "@/types/domain";

export default function Home() {
  const [novels, setNovels] = useState<Novel[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<{novel: Novel, chapter?: Chapter, scene?: Scene}[]>([]);

  async function loadNovels() {
    setLoading(true);
    try {
      const res = await api.listNovels();
      setNovels(res.novels);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadNovels();
  }, []);

  // Global keyboard shortcuts
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Ctrl+S to save (delegated to active editor)
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        // Save event is handled by the active editor component
        window.dispatchEvent(new CustomEvent("novelos-save"));
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  async function handleCreate() {
    if (!title.trim()) return;
    try {
      await api.createNovel(title.trim());
      setTitle("");
      setShowCreate(false);
      await loadNovels();
    } catch (e) {
      console.error(e);
    }
  }

  async function handleDelete(id: string, name: string) {
    if (!confirm(`确定删除「${name}」？`)) return;
    try {
      await api.deleteNovel(id);
      await loadNovels();
    } catch (e) {
      console.error(e);
    }
  }

  // Search across all novels
  async function handleSearch() {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    // Simple client-side search for now
    const results: {novel: Novel, chapter?: Chapter, scene?: Scene}[] = [];
    for (const novel of novels) {
      if (novel.title.toLowerCase().includes(searchQuery.toLowerCase())) {
        results.push({ novel });
      }
    }
    setSearchResults(results);
  }

  useEffect(() => {
    const timer = setTimeout(handleSearch, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, novels]);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">NovelOS</h1>
          <div className="flex items-center gap-4">
            {/* Global search */}
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索小说..."
                className="w-48 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
              />
              {searchResults.length > 0 && (
                <div className="absolute top-full mt-1 w-64 bg-gray-900 border border-gray-800 rounded-lg shadow-lg z-50">
                  {searchResults.slice(0, 5).map((r, i) => (
                    <a
                      key={i}
                      href={`/novels/${r.novel.id}`}
                      className="block px-3 py-2 text-sm hover:bg-gray-800"
                    >
                      {r.novel.title}
                      {r.chapter && ` / ${r.chapter.title}`}
                      {r.scene && ` / 场景 ${r.scene.order}`}
                    </a>
                  ))}
                </div>
              )}
            </div>
            <span className="text-xs text-gray-500">AI Writer IDE</span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">我的小说</h2>
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
          >
            + 新建小说
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500">加载中...</div>
        ) : novels.length === 0 ? (
          <div className="text-center py-12 text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
            <p className="text-lg mb-2">还没有小说</p>
            <p className="text-sm">点击上方按钮创建你的第一部作品</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {novels.map((novel) => (
              <div
                key={novel.id}
                className="flex items-center justify-between p-4 bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-700 transition-colors group"
              >
                <a
                  href={`/novels/${novel.id}`}
                  className="font-medium text-lg hover:text-indigo-400 transition-colors"
                >
                  {novel.title}
                </a>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-600">
                    {new Date(novel.updated_at).toLocaleDateString("zh-CN")}
                  </span>
                  <button
                    onClick={() => handleDelete(novel.id, novel.title)}
                    className="text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-all text-sm"
                  >
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Keyboard shortcuts hint */}
        <div className="mt-8 text-center text-xs text-gray-600">
          <span className="px-2 py-1 bg-gray-800 rounded">Ctrl+S</span> 保存当前编辑
        </div>
      </main>

      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">新建小说</h3>
            <input
              autoFocus
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              placeholder="输入小说标题"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500 mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowCreate(false); setTitle(""); }}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreate}
                disabled={!title.trim()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
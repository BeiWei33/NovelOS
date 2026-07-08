"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Chapter, Character, World, Style } from "@/types/domain";

type Tab = "chapters" | "characters" | "worlds" | "styles";

export default function NovelDetail() {
  const params = useParams();
  const novelId = params.id as string;

  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [worlds, setWorlds] = useState<World[]>([]);
  const [styles, setStyles] = useState<Style[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("chapters");
  const [novelTitle, setNovelTitle] = useState("");
  const [loading, setLoading] = useState(true);

  // Chapter create
  const [showCreateChapter, setShowCreateChapter] = useState(false);
  const [chapterTitle, setChapterTitle] = useState("");

  // Character create
  const [showCreateChar, setShowCreateChar] = useState(false);
  const [charName, setCharName] = useState("");

  async function loadAll() {
    setLoading(true);
    try {
      const [novel, chaps, chars, worldsRes, stylesRes] = await Promise.all([
        api.getNovel(novelId),
        api.listChapters(novelId),
        api.listCharacters(novelId),
        api.listWorlds(novelId),
        api.listStyles(novelId),
      ]);
      setNovelTitle(novel.title);
      setChapters(chaps);
      setCharacters(chars);
      setWorlds(worldsRes);
      setStyles(stylesRes);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, [novelId]);

  async function handleCreateChapter() {
    if (!chapterTitle.trim()) return;
    try {
      await api.createChapter({
        novel_id: novelId,
        order: chapters.length + 1,
        title: chapterTitle.trim(),
      });
      setChapterTitle("");
      setShowCreateChapter(false);
      await loadAll();
    } catch (e) {
      console.error(e);
    }
  }

  async function handleCreateCharacter() {
    if (!charName.trim()) return;
    try {
      await api.createCharacter({ novel_id: novelId, name: charName.trim() });
      setCharName("");
      setShowCreateChar(false);
      await loadAll();
    } catch (e) {
      console.error(e);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center">
        <p className="text-gray-500">加载中...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <a href="/" className="text-gray-500 hover:text-gray-300 text-sm">
            ← 返回
          </a>
          <h1 className="text-xl font-bold">{novelTitle}</h1>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-gray-800 px-6">
        <div className="max-w-5xl mx-auto flex gap-1">
          {[
            { key: "chapters", label: "章节" },
            { key: "characters", label: "人物" },
            { key: "worlds", label: "世界观" },
            { key: "styles", label: "风格" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as Tab)}
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

      <main className="max-w-5xl mx-auto px-6 py-6">
        {activeTab === "chapters" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">章节列表</h2>
              <button
                onClick={() => setShowCreateChapter(true)}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
              >
                + 新章节
              </button>
            </div>
            {chapters.length === 0 ? (
              <div className="text-center py-12 text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
                <p>还没有章节</p>
                <p className="text-sm mt-1">创建第一个章节开始写作</p>
              </div>
            ) : (
              <div className="grid gap-2">
                {chapters.map((ch) => (
                  <a
                    key={ch.id}
                    href={`/novels/${novelId}/chapters/${ch.id}`}
                    className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-700 transition-colors group"
                  >
                    <span className="w-8 h-8 flex items-center justify-center bg-gray-800 rounded text-sm text-gray-400">
                      {ch.order}
                    </span>
                    <span className="font-medium">{ch.title}</span>
                    <span className="ml-auto text-xs text-gray-600">
                      {ch.metadata.status}
                    </span>
                  </a>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "characters" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">人物列表</h2>
              <button
                onClick={() => setShowCreateChar(true)}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
              >
                + 新人物
              </button>
            </div>
            {characters.length === 0 ? (
              <div className="text-center py-12 text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
                <p>还没有人物</p>
              </div>
            ) : (
              <div className="grid gap-2">
                {characters.map((c) => (
                  <div
                    key={c.id}
                    className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg"
                  >
                    <span className="font-medium">{c.name}</span>
                    {c.age && <span className="text-sm text-gray-400">{c.age}岁</span>}
                    {c.occupation && (
                      <span className="text-sm text-gray-500">{c.occupation}</span>
                    )}
                    <div className="ml-auto flex gap-1">
                      {c.personality.slice(0, 3).map((t, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-gray-800 rounded text-xs text-gray-400"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "worlds" && (
          <div>
            <h2 className="text-lg font-semibold mb-4">世界观</h2>
            {worlds.length === 0 ? (
              <div className="text-center py-12 text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
                <p>还没有世界观设定</p>
              </div>
            ) : (
              <div className="grid gap-2">
                {worlds.map((w) => (
                  <div
                    key={w.id}
                    className="p-3 bg-gray-900 border border-gray-800 rounded-lg"
                  >
                    <span className="font-medium">{w.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "styles" && (
          <div>
            <h2 className="text-lg font-semibold mb-4">写作风格</h2>
            {styles.length === 0 ? (
              <div className="text-center py-12 text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
                <p>还没有风格配置</p>
              </div>
            ) : (
              <div className="grid gap-2">
                {styles.map((s) => (
                  <div
                    key={s.id}
                    className="p-3 bg-gray-900 border border-gray-800 rounded-lg"
                  >
                    <span className="font-medium">{s.name}</span>
                    <pre className="mt-2 text-xs text-gray-500 overflow-x-auto">
                      {JSON.stringify(s.profile, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Create Chapter Modal */}
      {showCreateChapter && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">新建章节</h3>
            <input
              autoFocus
              value={chapterTitle}
              onChange={(e) => setChapterTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateChapter()}
              placeholder="输入章节标题"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm mb-4 focus:outline-none focus:border-indigo-500"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowCreateChapter(false); setChapterTitle(""); }}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300"
              >
                取消
              </button>
              <button
                onClick={handleCreateChapter}
                disabled={!chapterTitle.trim()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded-lg text-sm font-medium"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Character Modal */}
      {showCreateChar && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">新建人物</h3>
            <input
              autoFocus
              value={charName}
              onChange={(e) => setCharName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateCharacter()}
              placeholder="输入人物名称"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm mb-4 focus:outline-none focus:border-indigo-500"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowCreateChar(false); setCharName(""); }}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300"
              >
                取消
              </button>
              <button
                onClick={handleCreateCharacter}
                disabled={!charName.trim()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded-lg text-sm font-medium"
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
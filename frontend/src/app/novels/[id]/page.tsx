"use client";

import { useParams } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { showToast } from "@/lib/toast";
import type { Chapter, Character, World, Style, StyleProfile } from "@/types/domain";

type Tab = "chapters" | "characters" | "worlds" | "styles";

const LOAD_TIMEOUT_MS = 10000;

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
  const [loadError, setLoadError] = useState<string | null>(null);

  // Chapter create
  const [showCreateChapter, setShowCreateChapter] = useState(false);
  const [chapterTitle, setChapterTitle] = useState("");

  // Character create
  const [showCreateChar, setShowCreateChar] = useState(false);
  const [charName, setCharName] = useState("");

  // Character edit
  const [editingChar, setEditingChar] = useState<Character | null>(null);
  const [editCharData, setEditCharData] = useState<Partial<Character>>({});

  // World create
  const [showCreateWorld, setShowCreateWorld] = useState(false);
  const [worldName, setWorldName] = useState("");

  // World edit
  const [editingWorld, setEditingWorld] = useState<World | null>(null);
  const [editWorldName, setEditWorldName] = useState("");

  // Style create
  const [showCreateStyle, setShowCreateStyle] = useState(false);
  const [styleName, setStyleName] = useState("");

  // Style edit
  const [editingStyle, setEditingStyle] = useState<Style | null>(null);
  const [editProfile, setEditProfile] = useState<StyleProfile>({});

  const loadAll = useCallback(async () => {
    setLoading(true);
    setLoadError(null);

    const timeoutId = setTimeout(() => {
      setLoading(false);
      setLoadError("加载超时，请检查网络连接后重试");
    }, LOAD_TIMEOUT_MS);

    try {
      const [novel, chaps, chars, worldsRes, stylesRes] = await Promise.all([
        api.getNovel(novelId),
        api.listChapters(novelId),
        api.listCharacters(novelId),
        api.listWorlds(novelId),
        api.listStyles(novelId),
      ]);
      clearTimeout(timeoutId);
      setNovelTitle(novel.title);
      setChapters(chaps);
      setCharacters(chars);
      setWorlds(worldsRes);
      setStyles(stylesRes);
    } catch (e) {
      clearTimeout(timeoutId);
      const message = e instanceof Error ? e.message : "加载失败";
      setLoadError(message);
      showToast(`加载失败: ${message}`, { type: "error" });
    } finally {
      setLoading(false);
    }
  }, [novelId]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  async function handleCreateChapter() {
    if (!chapterTitle.trim()) return;
    const prevChapters = [...chapters];
    try {
      const newChapter = await api.createChapter({
        novel_id: novelId,
        order: chapters.length + 1,
        title: chapterTitle.trim(),
      });
      setChapters([...prevChapters, newChapter]);
      setChapterTitle("");
      setShowCreateChapter(false);
      showToast("章节创建成功", { type: "success" });
    } catch (e) {
      setChapters(prevChapters);
      const message = e instanceof Error ? e.message : "创建失败";
      showToast(`创建章节失败: ${message}`, { type: "error" });
    }
  }

  async function handleCreateCharacter() {
    if (!charName.trim()) return;
    const prevCharacters = [...characters];
    try {
      const newChar = await api.createCharacter({ novel_id: novelId, name: charName.trim() });
      setCharacters([...prevCharacters, newChar]);
      setCharName("");
      setShowCreateChar(false);
      showToast("人物创建成功", { type: "success" });
    } catch (e) {
      setCharacters(prevCharacters);
      const message = e instanceof Error ? e.message : "创建失败";
      showToast(`创建人物失败: ${message}`, { type: "error" });
    }
  }

  async function handleDeleteChapter(id: string) {
    if (!confirm("确定删除该章节？")) return;
    const prevChapters = [...chapters];
    try {
      const res = await fetch(`http://localhost:8000/chapters/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(await res.text());
      setChapters(prevChapters.filter(c => c.id !== id));
      showToast("章节已删除", { type: "success" });
    } catch (e) {
      setChapters(prevChapters);
      const message = e instanceof Error ? e.message : "删除失败";
      showToast(`删除章节失败: ${message}`, { type: "error" });
    }
  }

  async function handleDeleteCharacter(id: string) {
    if (!confirm("确定删除该人物？")) return;
    const prevCharacters = [...characters];
    try {
      const res = await fetch(`http://localhost:8000/characters/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(await res.text());
      setCharacters(prevCharacters.filter(c => c.id !== id));
      showToast("人物已删除", { type: "success" });
    } catch (e) {
      setCharacters(prevCharacters);
      const message = e instanceof Error ? e.message : "删除失败";
      showToast(`删除人物失败: ${message}`, { type: "error" });
    }
  }

  async function handleDeleteWorld(id: string) {
    if (!confirm("确定删除该世界观？")) return;
    const prevWorlds = [...worlds];
    try {
      const res = await fetch(`http://localhost:8000/worlds/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(await res.text());
      setWorlds(prevWorlds.filter(w => w.id !== id));
      showToast("世界观已删除", { type: "success" });
    } catch (e) {
      setWorlds(prevWorlds);
      const message = e instanceof Error ? e.message : "删除失败";
      showToast(`删除世界观失败: ${message}`, { type: "error" });
    }
  }

  async function handleDeleteStyle(id: string) {
    if (!confirm("确定删除该风格？")) return;
    const prevStyles = [...styles];
    try {
      const res = await fetch(`http://localhost:8000/styles/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(await res.text());
      setStyles(prevStyles.filter(s => s.id !== id));
      showToast("风格已删除", { type: "success" });
    } catch (e) {
      setStyles(prevStyles);
      const message = e instanceof Error ? e.message : "删除失败";
      showToast(`删除风格失败: ${message}`, { type: "error" });
    }
  }

  async function handleCreateWorld() {
    if (!worldName.trim()) return;
    const prevWorlds = [...worlds];
    try {
      const res = await fetch("http://localhost:8000/worlds", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ novel_id: novelId, name: worldName.trim() }),
      });
      if (!res.ok) throw new Error(await res.text());
      const newWorld = await res.json();
      setWorlds([...prevWorlds, newWorld]);
      setWorldName("");
      setShowCreateWorld(false);
      showToast("世界观创建成功", { type: "success" });
    } catch (e) {
      setWorlds(prevWorlds);
      const message = e instanceof Error ? e.message : "创建失败";
      showToast(`创建世界观失败: ${message}`, { type: "error" });
    }
  }

  async function handleCreateStyle() {
    if (!styleName.trim()) return;
    const prevStyles = [...styles];
    try {
      const res = await fetch("http://localhost:8000/styles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ novel_id: novelId, name: styleName.trim() }),
      });
      if (!res.ok) throw new Error(await res.text());
      const newStyle = await res.json();
      setStyles([...prevStyles, newStyle]);
      setStyleName("");
      setShowCreateStyle(false);
      showToast("风格创建成功", { type: "success" });
    } catch (e) {
      setStyles(prevStyles);
      const message = e instanceof Error ? e.message : "创建失败";
      showToast(`创建风格失败: ${message}`, { type: "error" });
    }
  }

  function openStyleEdit(s: Style) {
    setEditingStyle(s);
    setEditProfile(s.profile || {});
  }

  async function handleSaveStyle() {
    if (!editingStyle) return;
    const prevStyles = [...styles];
    try {
      await api.updateStyle(editingStyle.id, { profile: editProfile });
      setStyles(prevStyles.map(s => s.id === editingStyle.id ? { ...s, profile: editProfile } : s));
      setEditingStyle(null);
      showToast("风格已更新", { type: "success" });
    } catch (e) {
      setStyles(prevStyles);
      const message = e instanceof Error ? e.message : "保存失败";
      showToast(`保存风格失败: ${message}`, { type: "error" });
    }
  }

  function openCharEdit(c: Character) {
    setEditingChar(c);
    setEditCharData({
      name: c.name,
      age: c.age,
      occupation: c.occupation,
      personality: c.personality,
      goal: c.goal,
      fear: c.fear,
      habit: c.habit,
      speech_style: c.speech_style,
    });
  }

  async function handleSaveChar() {
    if (!editingChar) return;
    const prevCharacters = [...characters];
    try {
      const updated = await api.updateCharacter(editingChar.id, editCharData);
      setCharacters(prevCharacters.map(c => c.id === editingChar.id ? updated : c));
      setEditingChar(null);
      showToast("人物已更新", { type: "success" });
    } catch (e) {
      setCharacters(prevCharacters);
      const message = e instanceof Error ? e.message : "保存失败";
      showToast(`保存人物失败: ${message}`, { type: "error" });
    }
  }

  function openWorldEdit(w: World) {
    setEditingWorld(w);
    setEditWorldName(w.name);
  }

  async function handleSaveWorld() {
    if (!editingWorld) return;
    const prevWorlds = [...worlds];
    try {
      const updated = await api.updateWorld(editingWorld.id, { name: editWorldName });
      setWorlds(prevWorlds.map(w => w.id === editingWorld.id ? updated : w));
      setEditingWorld(null);
      showToast("世界观已更新", { type: "success" });
    } catch (e) {
      setWorlds(prevWorlds);
      const message = e instanceof Error ? e.message : "保存失败";
      showToast(`保存世界观失败: ${message}`, { type: "error" });
    }
  }

  function getConsistencyColor(score?: number): string {
    if (score === undefined) return "text-gray-500";
    if (score >= 90) return "text-green-400";
    if (score >= 70) return "text-yellow-400";
    if (score >= 50) return "text-orange-400";
    return "text-red-400";
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center">
        <p className="text-gray-500">加载中...</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col items-center justify-center gap-4">
        <p className="text-red-400">{loadError}</p>
        <button
          onClick={loadAll}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium"
        >
          重试
        </button>
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

      {/* Status Overview */}
      <div className="border-b border-gray-800 px-6 py-4 bg-gray-900/50">
        <div className="max-w-5xl mx-auto flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-indigo-400">{chapters.length}</span>
            <span className="text-sm text-gray-500">章节</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-emerald-400">{characters.length}</span>
            <span className="text-sm text-gray-500">人物</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-amber-400">{worlds.length}</span>
            <span className="text-sm text-gray-500">世界观</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-violet-400">
              {chapters.reduce((sum, ch) => sum + (ch.summary?.one_line ? 1 : 0), 0)}
            </span>
            <span className="text-sm text-gray-500">场景</span>
          </div>
          <div className="ml-auto">
            {chapters.length > 0 && (
              <a
                href={`/novels/${novelId}/chapters/${chapters[0].id}`}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-500 rounded-lg text-sm font-medium transition-colors"
              >
                开始写作
              </a>
            )}
          </div>
        </div>
      </div>

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
                    <div className="flex-1 min-w-0">
                      <span className="font-medium block">{ch.title}</span>
                      {ch.summary?.one_line && (
                        <span className="text-xs text-gray-500 truncate block">
                          {ch.summary.one_line}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      {ch.consistency?.score !== undefined && (
                        <span className={`text-xs font-medium ${getConsistencyColor(ch.consistency.score)}`}>
                          一致性: {ch.consistency.score}%
                        </span>
                      )}
                      <span className="text-xs text-gray-600">
                        {ch.metadata?.status || "draft"}
                      </span>
                      <button
                        onClick={(e) => { e.preventDefault(); handleDeleteChapter(ch.id); }}
                        className="text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-all text-xs ml-2"
                      >
                        删除
                      </button>
                    </div>
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
                    className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg group"
                  >
                    <span className="font-medium">{c.name}</span>
                    {c.age && <span className="text-sm text-gray-400">{c.age}岁</span>}
                    {c.occupation && (
                      <span className="text-sm text-gray-500">{c.occupation}</span>
                    )}
                    <div className="ml-auto flex gap-1 items-center">
                      {c.personality.slice(0, 3).map((t, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-gray-800 rounded text-xs text-gray-400"
                        >
                          {t}
                        </span>
                      ))}
                      <button
                        onClick={() => openCharEdit(c)}
                        className="text-indigo-400 hover:text-indigo-300 text-xs opacity-0 group-hover:opacity-100 transition-all"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => handleDeleteCharacter(c.id)}
                        className="text-red-400 hover:text-red-300 text-xs opacity-0 group-hover:opacity-100 transition-all"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "worlds" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">世界观</h2>
              <button
                onClick={() => setShowCreateWorld(true)}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
              >
                + 新建世界观
              </button>
            </div>
            {worlds.length === 0 ? (
              <div className="text-center py-12 text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
                <p>还没有世界观设定</p>
              </div>
            ) : (
              <div className="grid gap-2">
                {worlds.map((w) => (
                  <div
                    key={w.id}
                    className="flex items-center justify-between p-3 bg-gray-900 border border-gray-800 rounded-lg group"
                  >
                    <span className="font-medium">{w.name}</span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => openWorldEdit(w)}
                        className="text-indigo-400 hover:text-indigo-300 text-xs opacity-0 group-hover:opacity-100 transition-all"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => handleDeleteWorld(w.id)}
                        className="text-red-400 hover:text-red-300 text-xs opacity-0 group-hover:opacity-100 transition-all"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "styles" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">写作风格</h2>
              <button
                onClick={() => setShowCreateStyle(true)}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
              >
                + 新建风格
              </button>
            </div>
            {styles.length === 0 ? (
              <div className="text-center py-12 text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
                <p>还没有风格配置</p>
              </div>
            ) : (
              <div className="grid gap-2">
                {styles.map((s) => (
                  <div
                    key={s.id}
                    className="flex items-center justify-between p-3 bg-gray-900 border border-gray-800 rounded-lg group"
                  >
                    <div className="flex-1">
                      <span className="font-medium">{s.name}</span>
                      {/* Style profile visual indicators */}
                      {s.profile && (
                        <div className="flex gap-2 mt-1.5">
                          {s.profile.pace && (
                            <span className="text-xs px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">
                              节奏: {s.profile.pace}
                            </span>
                          )}
                          {s.profile.emotion && (
                            <span className="text-xs px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">
                              情感: {s.profile.emotion}
                            </span>
                          )}
                          {s.profile.sentence && (
                            <span className="text-xs px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">
                              句式: {s.profile.sentence}
                            </span>
                          )}
                          {s.profile.humor && (
                            <span className="text-xs px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">
                              幽默: {s.profile.humor}
                            </span>
                          )}
                          {s.profile.dialog_ratio !== undefined && (
                            <span className="text-xs px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">
                              对话: {Math.round(s.profile.dialog_ratio * 100)}%
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => openStyleEdit(s)}
                          className="text-indigo-400 hover:text-indigo-300 text-xs opacity-0 group-hover:opacity-100 transition-all"
                        >
                          编辑
                        </button>
                        <button
                          onClick={() => handleDeleteStyle(s.id)}
                          className="text-red-400 hover:text-red-300 text-xs opacity-0 group-hover:opacity-100 transition-all"
                        >
                          删除
                        </button>
                      </div>
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

      {/* Edit Character Modal */}
      {editingChar && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">编辑人物</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">名称</label>
                <input
                  value={editCharData.name || ""}
                  onChange={(e) => setEditCharData({ ...editCharData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">年龄</label>
                <input
                  type="number"
                  value={editCharData.age ?? ""}
                  onChange={(e) => setEditCharData({ ...editCharData, age: e.target.value ? parseInt(e.target.value) : undefined })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">职业</label>
                <input
                  value={editCharData.occupation || ""}
                  onChange={(e) => setEditCharData({ ...editCharData, occupation: e.target.value || undefined })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">性格特质 (逗号分隔)</label>
                <input
                  value={(editCharData.personality || []).join(", ")}
                  onChange={(e) => setEditCharData({ ...editCharData, personality: e.target.value.split(",").map(s => s.trim()).filter(Boolean) })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">目标</label>
                <input
                  value={editCharData.goal || ""}
                  onChange={(e) => setEditCharData({ ...editCharData, goal: e.target.value || undefined })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">恐惧</label>
                <input
                  value={editCharData.fear || ""}
                  onChange={(e) => setEditCharData({ ...editCharData, fear: e.target.value || undefined })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">习惯 (逗号分隔)</label>
                <input
                  value={(editCharData.habit || []).join(", ")}
                  onChange={(e) => setEditCharData({ ...editCharData, habit: e.target.value.split(",").map(s => s.trim()).filter(Boolean) })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">说话风格</label>
                <input
                  value={editCharData.speech_style || ""}
                  onChange={(e) => setEditCharData({ ...editCharData, speech_style: e.target.value || undefined })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setEditingChar(null)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300"
              >
                取消
              </button>
              <button
                onClick={handleSaveChar}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create World Modal */}
      {showCreateWorld && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">新建世界观</h3>
            <input
              autoFocus
              value={worldName}
              onChange={(e) => setWorldName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateWorld()}
              placeholder="输入世界观名称"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm mb-4 focus:outline-none focus:border-indigo-500"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowCreateWorld(false); setWorldName(""); }}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300"
              >
                取消
              </button>
              <button
                onClick={handleCreateWorld}
                disabled={!worldName.trim()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded-lg text-sm font-medium"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit World Modal */}
      {editingWorld && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">编辑世界观</h3>
            <div>
              <label className="block text-sm text-gray-400 mb-1">名称</label>
              <input
                value={editWorldName}
                onChange={(e) => setEditWorldName(e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm mb-4 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setEditingWorld(null)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300"
              >
                取消
              </button>
              <button
                onClick={handleSaveWorld}
                disabled={!editWorldName.trim()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded-lg text-sm font-medium"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Style Modal */}
      {showCreateStyle && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">新建风格</h3>
            <input
              autoFocus
              value={styleName}
              onChange={(e) => setStyleName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateStyle()}
              placeholder="输入风格名称"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm mb-4 focus:outline-none focus:border-indigo-500"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowCreateStyle(false); setStyleName(""); }}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300"
              >
                取消
              </button>
              <button
                onClick={handleCreateStyle}
                disabled={!styleName.trim()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded-lg text-sm font-medium"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Style Edit Modal */}
      {editingStyle && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">编辑风格: {editingStyle.name}</h3>

            <div className="space-y-5">
              {/* dialog_ratio: slider 0-1, step 0.05 */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  对话比例: {Math.round((editProfile.dialog_ratio ?? 0) * 100)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={editProfile.dialog_ratio ?? 0}
                  onChange={(e) => setEditProfile({ ...editProfile, dialog_ratio: parseFloat(e.target.value) })}
                  className="w-full accent-indigo-500"
                />
                <div className="flex justify-between text-xs text-gray-600 mt-1">
                  <span>0%</span>
                  <span>100%</span>
                </div>
              </div>

              {/* emotion */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">情感表达</label>
                <select
                  value={editProfile.emotion ?? ""}
                  onChange={(e) => setEditProfile({ ...editProfile, emotion: e.target.value || undefined })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="">未设置</option>
                  <option value="implicit">implicit</option>
                  <option value="explicit">explicit</option>
                </select>
              </div>

              {/* sentence */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">句式</label>
                <select
                  value={editProfile.sentence ?? ""}
                  onChange={(e) => setEditProfile({ ...editProfile, sentence: e.target.value || undefined })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="">未设置</option>
                  <option value="short">short</option>
                  <option value="long">long</option>
                  <option value="mixed">mixed</option>
                </select>
              </div>

              {/* description */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">描写方式</label>
                <select
                  value={editProfile.description ?? ""}
                  onChange={(e) => setEditProfile({ ...editProfile, description: e.target.value || undefined })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="">未设置</option>
                  <option value="concrete">concrete</option>
                  <option value="abstract">abstract</option>
                </select>
              </div>

              {/* psychology */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">心理描写</label>
                <select
                  value={editProfile.psychology ?? ""}
                  onChange={(e) => setEditProfile({ ...editProfile, psychology: e.target.value || undefined })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="">未设置</option>
                  <option value="low">low</option>
                  <option value="high">high</option>
                </select>
              </div>

              {/* humor */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">幽默风格</label>
                <select
                  value={editProfile.humor ?? ""}
                  onChange={(e) => setEditProfile({ ...editProfile, humor: e.target.value || undefined })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="">未设置</option>
                  <option value="dry">dry</option>
                  <option value="warm">warm</option>
                  <option value="dark">dark</option>
                  <option value="none">none</option>
                </select>
              </div>

              {/* pace */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">节奏</label>
                <select
                  value={editProfile.pace ?? ""}
                  onChange={(e) => setEditProfile({ ...editProfile, pace: e.target.value || undefined })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="">未设置</option>
                  <option value="fast">fast</option>
                  <option value="slow">slow</option>
                  <option value="varied">varied</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setEditingStyle(null)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300"
              >
                取消
              </button>
              <button
                onClick={handleSaveStyle}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
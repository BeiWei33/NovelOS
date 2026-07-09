"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { showToast } from "@/lib/toast";
import type { Character } from "@/types/domain";

export default function CharacterDetail() {
  const params = useParams();
  const router = useRouter();
  const novelId = params.id as string;
  const characterId = params.characterId as string;

  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Edit state
  const [name, setName] = useState("");
  const [age, setAge] = useState<string>("");
  const [occupation, setOccupation] = useState("");
  const [personality, setPersonality] = useState<string[]>([]);
  const [personalityInput, setPersonalityInput] = useState("");
  const [goal, setGoal] = useState("");
  const [fear, setFear] = useState("");
  const [habit, setHabit] = useState<string[]>([]);
  const [habitInput, setHabitInput] = useState("");
  const [speechStyle, setSpeechStyle] = useState("");

  async function loadCharacter() {
    setLoading(true);
    try {
      const char = await api.getCharacter(characterId);
      setCharacter(char);
      setName(char.name);
      setAge(char.age !== undefined ? String(char.age) : "");
      setOccupation(char.occupation || "");
      setPersonality(char.personality || []);
      setGoal(char.goal || "");
      setFear(char.fear || "");
      setHabit(char.habit || []);
      setSpeechStyle(char.speech_style || "");
    } catch (e) {
      const message = e instanceof Error ? e.message : "加载失败";
      showToast(`加载人物失败: ${message}`, { type: "error" });
      router.push(`/novels/${novelId}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCharacter();
  }, [characterId, novelId]);

  function addPersonality() {
    const trimmed = personalityInput.trim();
    if (trimmed && !personality.includes(trimmed)) {
      setPersonality([...personality, trimmed]);
      setPersonalityInput("");
    }
  }

  function removePersonality(tag: string) {
    setPersonality(personality.filter((t) => t !== tag));
  }

  function addHabit() {
    const trimmed = habitInput.trim();
    if (trimmed && !habit.includes(trimmed)) {
      setHabit([...habit, trimmed]);
      setHabitInput("");
    }
  }

  function removeHabit(tag: string) {
    setHabit(habit.filter((t) => t !== tag));
  }

  async function handleSave() {
    if (!name.trim()) {
      showToast("姓名不能为空", { type: "error" });
      return;
    }

    setSaving(true);
    try {
      const updated = await api.updateCharacter(characterId, {
        name: name.trim(),
        age: age ? parseInt(age, 10) : undefined,
        occupation: occupation.trim() || undefined,
        personality: personality.length > 0 ? personality : undefined,
        goal: goal.trim() || undefined,
        fear: fear.trim() || undefined,
        habit: habit.length > 0 ? habit : undefined,
        speech_style: speechStyle.trim() || undefined,
      });
      setCharacter(updated);
      showToast("人物已保存", { type: "success" });
    } catch (e) {
      const message = e instanceof Error ? e.message : "保存失败";
      showToast(`保存人物失败: ${message}`, { type: "error" });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center">
        <p className="text-gray-500">加载中...</p>
      </div>
    );
  }

  if (!character) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col items-center justify-center gap-4">
        <p className="text-red-400">人物未找到</p>
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
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <a
            href={`/novels/${novelId}`}
            className="text-gray-500 hover:text-gray-300 text-sm"
          >
            ← 返回
          </a>
          <h1 className="text-xl font-bold">编辑人物</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-3xl mx-auto px-6 py-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              姓名 <span className="text-red-400">*</span>
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="人物姓名"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600"
            />
          </div>

          {/* Age */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">年龄</label>
            <input
              type="number"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              placeholder="年龄"
              className="w-32 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600"
            />
          </div>

          {/* Occupation */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">职业</label>
            <input
              value={occupation}
              onChange={(e) => setOccupation(e.target.value)}
              placeholder="职业"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600"
            />
          </div>

          {/* Personality Tags */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">性格标签</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {personality.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 bg-indigo-900/50 border border-indigo-700/50 rounded text-sm text-indigo-300 flex items-center gap-1"
                >
                  {tag}
                  <button
                    onClick={() => removePersonality(tag)}
                    className="text-indigo-400 hover:text-indigo-200"
                  >
                    x
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                value={personalityInput}
                onChange={(e) => setPersonalityInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addPersonality())}
                placeholder="输入性格标签，按回车添加"
                className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600"
              />
              <button
                onClick={addPersonality}
                className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium"
              >
                添加
              </button>
            </div>
          </div>

          {/* Goal */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">目标</label>
            <textarea
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="这个人物想要达成什么目标？"
              rows={3}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600 resize-none"
            />
          </div>

          {/* Fear */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">恐惧</label>
            <textarea
              value={fear}
              onChange={(e) => setFear(e.target.value)}
              placeholder="这个人物害怕什么？"
              rows={3}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600 resize-none"
            />
          </div>

          {/* Habit Tags */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">习惯</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {habit.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 bg-emerald-900/50 border border-emerald-700/50 rounded text-sm text-emerald-300 flex items-center gap-1"
                >
                  {tag}
                  <button
                    onClick={() => removeHabit(tag)}
                    className="text-emerald-400 hover:text-emerald-200"
                  >
                    x
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                value={habitInput}
                onChange={(e) => setHabitInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addHabit())}
                placeholder="输入习惯，按回车添加"
                className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600"
              />
              <button
                onClick={addHabit}
                className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-medium"
              >
                添加
              </button>
            </div>
          </div>

          {/* Speech Style */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">说话风格</label>
            <div className="flex gap-2">
              <select
                value={speechStyle}
                onChange={(e) => setSpeechStyle(e.target.value)}
                className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value="">选择预设风格</option>
                <option value="formal">正式</option>
                <option value="casual">随意</option>
                <option value="humorous">幽默</option>
                <option value="sarcastic">讽刺</option>
                <option value="cold">冷淡</option>
                <option value="warm">热情</option>
                <option value="childish">幼稚</option>
                <option value="old-fashioned">老派</option>
              </select>
              <input
                value={speechStyle}
                onChange={(e) => setSpeechStyle(e.target.value)}
                placeholder="或自定义风格"
                className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 placeholder-gray-600"
              />
            </div>
          </div>

          {/* Timestamps */}
          <div className="text-sm text-gray-500 flex gap-6 pt-4 border-t border-gray-800">
            <span>创建于: {new Date(character.created_at).toLocaleString()}</span>
            <span>更新于: {new Date(character.updated_at).toLocaleString()}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={() => router.push(`/novels/${novelId}`)}
            className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded-lg text-sm font-medium"
          >
            {saving ? "保存中..." : "保存"}
          </button>
        </div>
      </main>
    </div>
  );
}

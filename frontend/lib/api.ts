/** API client for NovelOS backend */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`API ${res.status}: ${err}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

// ─── Novel ───────────────────────────────────────────────────────────────────

export const api = {
  async listNovels() {
    return request<{ novels: import("../types/domain").Novel[] }>("/novels")
  },

  async getNovel(id: string) {
    return request<import("../types/domain").Novel>(`/novels/${id}`)
  },

  async createNovel(title: string) {
    return request<import("../types/domain").Novel>("/novels", {
      method: "POST",
      body: JSON.stringify({ title }),
    })
  },

  async deleteNovel(id: string) {
    return request<void>(`/novels/${id}`, { method: "DELETE" })
  },

  // ─── Chapter ─────────────────────────────────────────────────────────────

  async listChapters(novelId: string) {
    return request<import("../types/domain").Chapter[]>(
      `/chapters?novel_id=${novelId}`
    )
  },

  async getChapter(id: string) {
    return request<import("../types/domain").Chapter>(`/chapters/${id}`)
  },

  async createChapter(data: {
    novel_id: string
    order: number
    title: string
  }) {
    return request<import("../types/domain").Chapter>("/chapters", {
      method: "POST",
      body: JSON.stringify(data),
    })
  },

  // ─── Scene ───────────────────────────────────────────────────────────────

  async listScenes(chapterId: string) {
    return request<import("../types/domain").Scene[]>(
      `/scenes?chapter_id=${chapterId}`
    )
  },

  async getScene(id: string) {
    return request<import("../types/domain").Scene>(`/scenes/${id}`)
  },

  async createScene(data: {
    chapter_id: string
    order: number
    document?: { blocks: import("../types/domain").SceneBlock[] }
  }) {
    return request<import("../types/domain").Scene>("/scenes", {
      method: "POST",
      body: JSON.stringify(data),
    })
  },

  async updateScene(id: string, data: {
    document?: { blocks: import("../types/domain").SceneBlock[] }
    planning?: Record<string, unknown>
  }) {
    return request<import("../types/domain").Scene>(`/scenes/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  },

  // ─── Characters ──────────────────────────────────────────────────────────

  async listCharacters(novelId: string) {
    return request<import("../types/domain").Character[]>(
      `/characters?novel_id=${novelId}`
    )
  },

  async createCharacter(data: {
    novel_id: string
    name: string
    personality?: string[]
    goal?: string
    fear?: string
  }) {
    return request<import("../types/domain").Character>("/characters", {
      method: "POST",
      body: JSON.stringify(data),
    })
  },

  // ─── Worlds ──────────────────────────────────────────────────────────────

  async listWorlds(novelId: string) {
    return request<import("../types/domain").World[]>(
      `/worlds?novel_id=${novelId}`
    )
  },

  // ─── Styles ──────────────────────────────────────────────────────────────

  async listStyles(novelId: string) {
    return request<import("../types/domain").Style[]>(
      `/styles?novel_id=${novelId}`
    )
  },
}
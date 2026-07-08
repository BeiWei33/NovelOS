/** NovelOS Domain Types — matching the backend Canonical Layer */

export interface Novel {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface Chapter {
  id: string
  novel_id: string
  order: number
  title: string
  planning: ChapterPlanning
  summary: ChapterSummary
  consistency: Consistency
  chapter_facts: ChapterFacts
  metadata: ChapterMetadata
  created_at: string
  updated_at: string
}

export interface ChapterPlanning {
  goal?: string
  theme?: string
  scene_plan?: string[]
}

export interface ChapterSummary {
  one_page?: string
  one_paragraph?: string
  one_line?: string
}

export interface Consistency {
  score?: number
  issues?: string[]
  fixed?: string[]
  warnings?: string[]
}

export interface ChapterFacts {
  relationship_changes?: string[]
  world_changes?: string[]
  timeline_changes?: string[]
  new_information?: string[]
}

export interface ChapterMetadata {
  status: "draft" | "written" | "edited" | "frozen"
}

export interface Scene {
  id: string
  chapter_id: string
  order: number
  version: number
  planning: ScenePlanning
  document: SceneDocument
  body_history: BodyHistory
  provenance: Provenance
  created_at: string
  updated_at: string
}

export interface ScenePlanning {
  goal?: string
  conflict?: string
  stakes?: string
  turning_point?: string
  ending?: string
  foreshadow?: string
}

export interface SceneDocument {
  blocks: SceneBlock[]
}

export interface SceneBlock {
  id: string
  type: BlockType
  content: string
  metadata?: Record<string, unknown>
}

export type BlockType =
  | "narration"
  | "dialogue"
  | "description"
  | "inner_monologue"
  | "emotion"
  | "letter"
  | "phone_message"
  | "flashback"
  | "system_message"

export interface BodyHistory {
  draft?: SceneDocument
  edited?: SceneDocument
  published?: SceneDocument
}

export interface Provenance {
  execution_role?: string
  execution_profile?: string
  provider?: string
  model?: string
  temperature?: number
  tokens?: number
  duration_ms?: number
  version?: string
  status?: string
}

export interface Character {
  id: string
  novel_id: string
  name: string
  age?: number
  occupation?: string
  personality: string[]
  goal?: string
  fear?: string
  habit: string[]
  speech_style?: string
  created_at: string
  updated_at: string
}

export interface World {
  id: string
  novel_id: string
  name: string
  config: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface Style {
  id: string
  novel_id: string
  name: string
  profile: StyleProfile
  created_at: string
  updated_at: string
}

export interface StyleProfile {
  dialog_ratio?: number
  emotion?: string
  sentence?: string
  description?: string
  psychology?: string
  humor?: string
  pace?: string
}
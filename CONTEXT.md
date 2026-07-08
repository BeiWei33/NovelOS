# NovelOS — Domain Glossary

## Project

NovelOS ("小说操作系统") — 一个 AI Writer IDE，不是聊天机器人。

## Three-axis architecture

The system decomposes along three orthogonal axes:

- **Business Object** — Novel / Chapter / Scene / SceneDocument / Character / World / Style / RewriteSample / NarrativeEvent / Memory / Artifact
- **Service** — Planner / Writer / Editor / Artifact / Memory / Consistency (Chapter-level)
- **Skill** — SceneWriter / DialogueEnhancer / DescriptionEnhancer / EmotionEnhancer / SceneEditor / FactsExtractor / SummaryExtractor / ...

These three dimensions are orthogonal and never mixed.

## Business Objects

### Novel
Top-level container.

### Chapter
```yaml
Chapter:
  id
  novel_id
  order
  title
  planning:
    goal
    theme
    scene_plan: []
  summary:
    one_page
    one_paragraph
    one_line
  consistency:
    score, issues, fixed, warnings
  chapter_facts:
    relationship_changes, world_changes, timeline_changes, new_information
  metadata:
    status
```

### Scene
The **sole transaction boundary** — an **indivisible narrative transaction**.

```yaml
Scene:
  id
  chapter_id
  order
  version                 # incremented on each edit
  planning:
    goal, conflict, stakes, turning_point, ending, foreshadow
  document:               # SceneDocument (Domain AST) — JSONB
    blocks: []
  body_history:
    draft, edited, published
  provenance:
    execution_role, execution_profile, provider, model, temperature, tokens, duration_ms, version, status
```

### SceneDocument (Domain AST — Canonical Narrative Model)

The **single canonical narrative model** for the entire system. NOT designed for any editor — all editors and renderers are Adapters.

Block types (domain): `narration`, `dialogue`, `description`, `inner_monologue`, `emotion`, `letter`, `phone_message`, `flashback`, `system_message`.

**No block type is defined for an editor. All are defined for the narrative domain.**

### Presentation Adapter Layer
```
SceneDocument (Domain AST)
    ▼
ProseMirror Adapter (custom Node types — Option B)
Markdown / EPUB / PDF / Screenplay / Comic Script Renderers
```

### NarrativeEvent
```yaml
id, scene_id, type, actor, target, payload, sequence
```
Single source of truth for character state, relationships, consistency.

### Artifact (abstract)
All derived structured data. **Regeneratable.**

## Workflow

Per-Scene:
```
ScenePipeline:
  WriterService → EditorService → Freeze Scene
  ArtifactService → MemoryService
```

Chapter-level:
```
ChapterWorkflow:
  StoryPlanner → Scene List → foreach Scene (ScenePipeline)
  → ChapterConsistency → ChapterSummarizer → ChapterFactsAggregator → ChapterMemoryUpdater
```

## Services

- **PlannerService**, **WriterService**, **EditorService**, **ArtifactService**, **MemoryService**, **ConsistencyService**

## Prompt system

Skill Manifest (role only) → Context Assembler → Template → Builder

## Provider layer

Skill role → Role Registry → Execution Profile → Execution Policy → Model Router

## Knowledge Layer

Skill Manifest (knowledge section) → Knowledge Engine → Retrievers → Knowledge Objects → Context Assembler

Multiple Retrievers with different strategies: SceneRetriever (vector), FactRetriever (SQL), CharacterRetriever (graph+DB), RelationshipRetriever (graph), TimelineRetriever (index), etc.

## Database Layer (four-tier data architecture)

### Tier 1: Canonical Layer — Source of Truth

Stores authoritative domain objects. **Only this layer is the single source of truth.**

```
Table: novel
  id, title, created_at, updated_at

Table: chapter
  id, novel_id, order, title, planning (JSONB), metadata (JSONB), created_at, updated_at

Table: scene
  id, chapter_id, order, version,
  planning (JSONB),
  document (JSONB)            ← SceneDocument Domain AST — THE source of truth for narrative
  body_history (JSONB),
  provenance (JSONB),
  created_at, updated_at

Table: character
  id, novel_id, name, age, occupation, personality (JSONB),
  goal, fear, habit (JSONB), speech_style, created_at, updated_at

Table: world
  id, novel_id, name, config (JSONB), created_at, updated_at

Table: style
  id, novel_id, name, profile (JSONB), created_at, updated_at
```

**Scene.document is always JSONB.** Never decomposed into normalized tables. The canonical object is always complete — one query loads the entire Scene.

### Tier 2: Artifact Layer — Derived Structured Knowledge

Extracted from Canonical Layer by ArtifactService. **Regeneratable.**

```sql
-- Per-scene artifacts
Table: scene_artifact
  id, scene_id, scene_version,
  facts (JSONB),
  narrative_events (JSONB),
  summary (JSONB),
  keywords (TEXT[]),
  emotion_profile (JSONB),
  entities (JSONB),
  foreshadow_hints (JSONB),
  timeline_deltas (JSONB),
  embedding (vector),
  created_at

-- Chapter-level artifacts
Table: chapter_artifact
  id, chapter_id,
  summary (JSONB),          -- three-level
  facts (JSONB),
  consistency (JSONB),
  created_at
```

### Tier 3: Projection Layer — Read Models

Optimized for specific query patterns. **Reconstructible from Artifacts.**

```sql
-- Fact projection: who knows what, what happened
Table: fact_projection
  scene_id, fact_type, actor, target, payload (JSONB),
  confidence, sequence

-- Character state projection: character arcs + current state
Table: character_state_projection
  character_id, novel_id, chapter_id, scene_id,
  state (JSONB),            -- current emotion, goals, secrets known
  arc_summary (TEXT),
  updated_at

-- Relationship projection: relationship graph edges
Table: relationship_projection
  character_a, character_b, novel_id,
  trust, affection, fear,    -- numeric scores, -100..100
  status (TEXT),             -- "estranged", "close", "conflict"
  updated_at

-- Timeline projection: chronological narrative events
Table: timeline_projection
  chapter_id, scene_id, sequence,
  narrative_time (TEXT),     -- e.g. "day 3, evening"
  event_type, event_summary,
  characters (TEXT[])

-- Retrieval projection: for RAG
Table: retrieval_projection
  scene_id, chapter_id,
  one_line (TEXT),
  keywords (TEXT[]),
  embedding (vector(1536)),
  block_types (TEXT[])       -- which block types appear in this scene
```

### Tier 4: Runtime Layer — Ephemeral State

```text
Redis:
  workflow_state            -- active ChapterWorkflow state
  knowledge_cache           -- cached Knowledge Objects per role
  lock_manager              -- Scene transaction locks
  rate_limiter              -- Provider rate limit tracking

Job Queue:
  scene_pipeline            -- per-Scene pipeline jobs
  artifact_rebuild          -- full artifact rebuild on prose edit
  projection_rebuild        -- full projection rebuild
```

### Data lifecycle

```
SceneDocument (Canonical — single source of truth)
    │
    ▼  ArtifactService.run()
    │
scene_artifact table (Facts, Events, Summary, Keywords, Embedding)
    │
    ▼  ProjectionBuilder.run()
    │
fact_projection
character_state_projection
relationship_projection
timeline_projection
retrieval_projection
    │
    ▼
Knowledge Layer (Retrievers read from Projections + Artifacts)
    │
    ▼
Prompt Context
```

### Key principles

- **Canonical SceneDocument is always JSONB** — never decomposed; one query loads the full Scene
- **Artifacts are derived from SceneDocument and regeneratable** — delete scene_artifact, re-run ArtifactService
- **Projections are derived from Artifacts and regeneratable** — drop projections, re-run ProjectionBuilder
- **Knowledge Layer reads from Projections, not from Canonical** — no JSONB path queries in hot paths
- **If Scene version changes, Artifacts and Projections become stale** — ArtifactService invalidates on version mismatch
- **Full rebuild is safe and lossless** — Canonical is the only source of truth
- **Canonical layer (Novel, Chapter, Scene, Character, World, Style) is append-only for versions**
- **Only Chapter and Scene are user-editable** — artifacts and projections are machine-generated

## Database layout summary

```
Canonical Layer (source of truth)
  novel, chapter, scene (document JSONB), character, world, style

Artifact Layer (derived knowledge, regeneratable)
  scene_artifact (facts/events/summary/embedding), chapter_artifact

Projection Layer (read models, reconstructible)
  fact_projection, character_state_projection, relationship_projection,
  timeline_projection, retrieval_projection

Runtime Layer (ephemeral)
  Redis cache, job queue, workflow state
```

## Skills registry

| Skill | role | knowledge |
|-------|------|-----------|
| StoryPlanner | story-planner | scene_history, character_state, world_state |
| ScenePlanner | scene-planner | character_state, world_state |
| SceneWriter | scene-writer | scene_history, world_state, character_state, rewrite_samples |
| DialogueEnhancer | dialogue-enhancer | character_voice, recent_dialogue, relationship_state |
| DescriptionEnhancer | description-enhancer | scene_history, world_state |
| EmotionEnhancer | emotion-enhancer | character_state, recent_dialogue |
| SceneEditor | scene-editor | style |
| ArtifactService skills | structured-extraction | (none — always processes current scene) |
| ChapterConsistencyChecker | high-reasoning | facts, timeline, relationships |
| SceneMemoryUpdater | memory | facts, events |
| ChapterMemoryUpdater | memory | chapter_facts |

## Plugin Protocol

```yaml
name: <SkillName>
role: <role-name>
requires:
  - <context_slice>
knowledge:
  - <knowledge_type>
template: <file>
constraints:
  - <behavioral_constraint>
```

## Design principles (canonical list)

- **Workflow > Data > Prompt > Model**
- **Three-axis orthogonal decomposition:** Business Object / Service / Skill are never mixed
- **Scene is the sole transaction boundary**
- **Scene saves Facts, not Memory**
- **NarrativeEvents are the single source of truth** for state-dependent consumers
- **SceneDocument is Canonical Domain AST, never tied to any editor**
- **Block types are domain concepts**
- **Presentation Adapters project Domain AST into editor/export formats**
- **ProseMirror gets custom Node types (Option B)**
- **One Domain AST → multiple Projections**
- **Block IDs are stable UUIDs**
- **Only the Domain AST is human-editable. Artifacts and Projections are regeneratable.**
- **WriterService: one Generator, all others Enhancers outputting Patches**
- **Skill only knows its role** — no provider, no model, no profile
- **Role Registry → Execution Profile → Execution Policy → Model Router**
- **Switch models by changing YAML only**
- **No single RAG** — Knowledge Layer with multiple specialized Retrievers
- **Skill declares what knowledge it needs (knowledge section), not how to retrieve it**
- **Retriever returns Knowledge Objects, not DB records**
- **Four-tier database:** Canonical (JSONB) → Artifacts (derived) → Projections (read models) → Runtime (ephemeral)
- **Canonical SceneDocument is always JSONB** — never decomposed
- **Artifacts and Projections are discardable and reconstructible**
- **If Scene version changes, Artifacts and Projections become stale**
- **Full rebuild is safe and lossless**
- **Four-layer prompt system:** Manifest → Context Assembler → Template → Builder
- **No context pollution**
- **No universal prompt**
- **Editor is per-Scene**
- **Two-layer consistency:** Scene-level → Chapter-level
- **Three-level chapter summary:** one_page / one_paragraph / one_line
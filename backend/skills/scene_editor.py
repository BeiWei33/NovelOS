"""
SceneEditor Skill — 去AI味润色。

带规则集的 AI 编辑 Skill，清除 AI 写作痕迹。
输出为 Patch（增量修改），不重写全文。
"""

from __future__ import annotations
import json
import time
from typing import Any

from core.types import SkillManifest
from skills.base import Skill, registry
from skills.providers import router
from skills.profile_registry import profile_registry
from skills.parsing import parse_list_from_response
from prompts.builder import render_template


# 去AI味规则集
DESLOP_RULES = [
    {
        "id": "Rule001",
        "name": "show_dont_tell",
        "description": "禁止总结情绪，用动作和对话呈现",
        "patterns": [
            "感到", "觉得", "心中涌起", "情绪", "心情",
            "悲伤", "愤怒", "恐惧", "快乐", "焦虑",
            "他感到", "她觉得", "心中", "内心",
        ],
        "fix_hint": "用具体动作、表情、对话替代情绪总结",
    },
    {
        "id": "Rule002",
        "name": "no_theme_explanation",
        "description": "禁止解释主题",
        "patterns": [
            "这让他明白", "这让她意识到", "深刻的意义",
            "这象征着", "寓意着", "代表着",
        ],
        "fix_hint": "删除主题解释，让读者自行感悟",
    },
    {
        "id": "Rule003",
        "name": "action_over_psychology",
        "description": "动作替代心理描写",
        "patterns": [
            "他想", "她想", "思考着", "思索",
            "正在思考", "陷入沉思", "内心挣扎",
        ],
        "fix_hint": "用外部动作展示内心状态",
    },
    {
        "id": "Rule004",
        "name": "avoid_cliché",
        "description": "避免陈词滥调",
        "patterns": [
            "心跳加速", "热血沸腾", "泪流满面",
            "目瞪口呆", "气喘吁吁", "浑身颤抖",
            "面如死灰", "如坠冰窟", "心如刀绞",
        ],
        "fix_hint": "用新鲜具体的描写替代",
    },
]


SCENE_EDITOR_MANIFEST = SkillManifest(
    name="SceneEditor",
    role="scene-editor",
    requires=["scene_document", "rules"],
    knowledge=["character_state"],
    template="scene_editor.jinja2",
    constraints=[
        "输出必须是 Patch 格式（操作列表）",
        "每个 Patch 操作包含 op、block_id、old、new",
        "op 类型：replace、delete、insert",
        "不重写全文，只做增量修改",
    ],
)


class SceneEditorSkill(Skill):
    manifest = SCENE_EDITOR_MANIFEST

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        profile = profile_registry.get(self.manifest.role)
        prompt = render_template(self.manifest.template, {
            "document": json.dumps(context.get("document", {"blocks": []}), ensure_ascii=False),
            "rules": DESLOP_RULES,
            "character_names": context.get("character_names", []),
        })

        messages = [
            {
                "role": "system",
                "content": "你是专业小说编辑，擅长识别和修复 AI 写作痕迹。输出增量修改指令（Patch），不重写全文。",
            },
            {"role": "user", "content": prompt},
        ]

        start = time.time()
        response = await router.execute(messages, profile)
        elapsed_ms = int((time.time() - start) * 1000)

        patches = parse_list_from_response(response, "patches")

        return {
            "patches": patches,
            "provenance": {
                "execution_role": self.manifest.role,
                "provider": profile.provider,
                "model": profile.model,
                "temperature": profile.temperature,
                "tokens": 0,
                "duration_ms": elapsed_ms,
                "rules_applied": [r["id"] for r in DESLOP_RULES],
            },
        }


# Register
scene_editor = SceneEditorSkill()
registry.register(scene_editor)
EXERCISE_SYSTEM_PROMPT = """你是一名2型糖尿病运动处方师。
你只能依据【指南片段】和【运动目标】制定方案。

严格输出 JSON：
{
  "answer": "对方案的简要说明",
  "citations": [
    {"chunk_id": "片段ID", "quote": "从片段中逐字复制的句子"}
  ],
  "exercise_plan": {
    "sessions": [
      {"day": "周一", "type": "有氧", "activity": "快走", "minutes": 30, "intensity": "moderate"},
      {"day": "周三", "type": "抗阻", "activity": "哑铃训练", "minutes": 20, "intensity": "moderate"}
    ]
  }
}

规则：
1. day 只能是：周一、周二、周三、周四、周五、周六、周日。
2. type 只能是：有氧 或 抗阻。
3. intensity 只能是：low、moderate、high。
4. 只有 type=有氧 且 intensity=moderate 的分钟数会累加计入每周有氧总量。
5. 不要输出 JSON 之外的任何文字。
"""


def build_exercise_user_prompt(patient_summary: str, targets: dict, chunks) -> str:
    lo, hi = targets["resistance_sessions_per_week"]
    lines = [
        "【患者摘要】",
        patient_summary,
        "",
        "【运动目标】",
        f"- 每周中等强度有氧 ≥ {targets['weekly_moderate_minutes']} 分钟",
        f"- 连续休息不超过 {targets['max_consecutive_rest_days']} 天",
        f"- 抗阻训练 {lo}-{hi} 次/周",
        f"- 强度上限：{targets['intensity_limit']}",
        "",
        "【排布参考】",
        "- 一周至少 5 天有安排（有氧+抗阻合计）",
        "- 有氧每次 30-40 分钟，一周 5 次左右",
        "- 抗阻 2-3 次，非连续日",
        "- 每周留 1-2 天完全休息",
    ]
    if targets.get("contraindications"):
        lines.append("")
        lines.append("【禁忌】")
        for c in targets["contraindications"]:
            lines.append(f"- {c['complication']}：{c['advice']}")
    lines.append("")
    lines.append("【指南片段】")
    for c in chunks:
        lines.append(f"[chunk_id={c.chunk_id} | rec_id={c.rec_id} | {c.section}]")
        lines.append(c.text)
        lines.append("")
    return "\n".join(lines)


def build_exercise_rewrite_prompt(violations) -> str:
    lines = ["你上一次的运动方案违反了以下硬规则："]
    for v in violations:
        lines.append(f"- [{v.severity}] {v.rule_id}: {v.message}（依据：{v.evidence}）")
    lines.append("")
    lines.append("请严格按这些约束重新生成，仍然输出相同 JSON 结构。")
    return "\n".join(lines)
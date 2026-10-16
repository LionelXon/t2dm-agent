from src.rules.schema import Violation


WEEK_DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _minutes(session: dict) -> int:
    try:
        return int(session.get("minutes", 0))
    except (TypeError, ValueError):
        return 0


def _is_aerobic(session: dict) -> bool:
    return "有氧" in str(session.get("type", ""))


def _is_resistance(session: dict) -> bool:
    return "抗阻" in str(session.get("type", ""))


def _max_consecutive_rest(day_has_session: dict) -> int:
    """计算一周内最长连续休息天数，包含跨周末的环绕。"""
    max_rest = 0
    current = 0
    for d in WEEK_DAYS:
        if day_has_session[d]:
            current = 0
        else:
            current += 1
            max_rest = max(max_rest, current)

    # 跨周末环绕
    wrap = 0
    for d in WEEK_DAYS:
        if not day_has_session[d]:
            wrap += 1
        else:
            break
    for d in reversed(WEEK_DAYS):
        if not day_has_session[d]:
            wrap += 1
        else:
            break
    max_rest = max(max_rest, wrap)
    return max_rest


def assert_exercise_plan(plan: dict, targets: dict) -> list[Violation]:
    v: list[Violation] = []
    sessions = plan.get("sessions", [])
    if not sessions:
        v.append(Violation(
            rule_id="CDS-EXE-EMPTY",
            severity="hard",
            message="运动方案为空",
            evidence="中国T2DM防治指南（2020）- 7.3 运动治疗",
        ))
        return v

    intensity_limit = targets.get("intensity_limit", "moderate")
    is_low_limit = intensity_limit == "low"

    # 1. 每周中等强度有氧分钟
    # 注意：intensity_limit="low" 时（例如增殖期视网膜病变），
    # 指南不要求达到 150 分钟中等强度，故跳过此断言。
    if not is_low_limit:
        aerobic_minutes = sum(
            _minutes(s) for s in sessions
            if _is_aerobic(s) and str(s.get("intensity", "moderate")) == "moderate"
        )
        if aerobic_minutes < targets["weekly_moderate_minutes"]:
            v.append(Violation(
                rule_id="CDS-EXE-001",
                severity="hard",
                message=(
                    f"每周中等强度有氧 {aerobic_minutes} 分钟 "
                    f"< {targets['weekly_moderate_minutes']} 分钟"
                ),
                evidence="中国T2DM防治指南（2020）- 7.3",
            ))

    # 2. 连续休息日
    day_has_session = {d: False for d in WEEK_DAYS}
    for s in sessions:
        d = s.get("day", "")
        if d in day_has_session:
            day_has_session[d] = True

    max_rest = _max_consecutive_rest(day_has_session)
    if max_rest > targets["max_consecutive_rest_days"]:
        v.append(Violation(
            rule_id="CDS-EXE-002",
            severity="hard",
            message=(
                f"最长连续休息 {max_rest} 天 "
                f"> {targets['max_consecutive_rest_days']} 天"
            ),
            evidence="中国T2DM防治指南（2020）- 7.3",
        ))

    # 3. 抗阻次数
    resistance_days = sum(1 for s in sessions if _is_resistance(s))
    lo, hi = targets["resistance_sessions_per_week"]
    if not (lo <= resistance_days <= hi):
        v.append(Violation(
            rule_id="CDS-EXE-003",
            severity="hard",
            message=f"抗阻训练 {resistance_days} 次/周 不在 {lo}-{hi} 次",
            evidence="中国T2DM防治指南（2020）- 7.3",
        ))

    # 4. 禁忌：intensity_limit="low" 时不允许 moderate/high
    if is_low_limit:
        risky = [
            s for s in sessions
            if str(s.get("intensity", "moderate")) in ("moderate", "high")
        ]
        if risky:
            v.append(Violation(
                rule_id="CDS-EXE-004",
                severity="hard",
                message=(
                    f"存在运动禁忌，但方案包含 {len(risky)} 项中等及以上强度运动"
                ),
                evidence="中国T2DM防治指南（2020）- 7.3 运动禁忌",
            ))

    return v
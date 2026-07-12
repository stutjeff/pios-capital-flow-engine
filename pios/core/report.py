from __future__ import annotations

import pandas as pd

from .scoring import flow_map, ranked_rotation

IMPORTANT_POSITIONS = ["DXY_PROXY", "US_10Y_YIELD", "HY_OAS", "VIX", "QQQ", "SOXX", "GLD", "TLT"]
STATE_ICON = {"NORMAL": "🟢", "ROTATION": "🔵", "RISK_OFF": "🟡", "CREDIT_STRESS": "🟠", "LIQUIDITY_STRESS": "🔴", "SYSTEMIC": "🚨"}


def _fmt(value):
    return "資料不足" if pd.isna(value) else f"{value:+.1f}%"


def _stars(number: int) -> str:
    value = max(0, min(5, int(number)))
    return "★" * value + "☆" * (5 - value)


def _bar(percent: float | int | None, blocks: int = 10) -> str:
    if percent is None or pd.isna(percent):
        return "□□□□□□□□□□"
    filled = max(0, min(blocks, round(float(percent) / 100 * blocks)))
    return "■" * filled + "□" * (blocks - filled)


def _rotation_lines(items):
    output = []
    for index, item in enumerate(items, 1):
        name, change20, change5, change60, change120, percentile, stars = item
        strength = "資料不足" if pd.isna(percentile) else f"強度{percentile:.0f}% {_stars(stars)}"
        output.append(
            f"{index}. {name}｜5D {_fmt(change5)}｜20D {_fmt(change20)}｜60D {_fmt(change60)}｜120D {_fmt(change120)}｜{strength}"
        )
    return output or ["資料不足"]


def _state_summary(decision):
    state = decision.get("state_engine", {})
    momentum = state.get("momentum", {})
    velocity = state.get("velocity", {})
    persistence = state.get("persistence", {})
    breadth = state.get("breadth", {})
    scores = "→".join(f"{x:.1f}" for x in state.get("recent_scores", [])[-7:]) or "資料不足"
    percentile = state.get("risk_percentile_180d")
    accumulation = state.get("accumulation_score")
    return [
        f"{STATE_ICON.get(state.get('state'), '⚪')} 市場狀態：{state.get('state_zh', '未知')}（{state.get('state', 'UNKNOWN')}）",
        f"風險 {state.get('risk_score', 0):.1f}/100｜180D {percentile if percentile is not None else '--'}%｜排名第 {state.get('risk_rank_180d', '--')}/{state.get('history_count', '--')}",
        f"累積度：{accumulation if accumulation is not None else '--'}% {_bar(accumulation)}",
        f"近7日：{scores}",
        f"速度：3D {velocity.get('daily_velocity_3d')}／日｜5D {velocity.get('daily_velocity_5d')}／日｜加速度 {velocity.get('acceleration')}｜{velocity.get('label', '')}",
        f"持續性：≥15分 {persistence.get('above_observe', 0)}天｜≥25分 {persistence.get('above_alert', 0)}天｜≥35分 {persistence.get('above_risk_off', 0)}天｜連升 {persistence.get('strictly_rising', 0)}天",
        f"廣度：{breadth.get('active_count', 0)}/{breadth.get('total_modules', 5)} 模組同步升溫（{breadth.get('breadth_pct', 0):.0f}%）",
    ]


def _state_reason_lines(decision):
    state = decision.get("state_engine", {})
    reasons = state.get("reasons", {})
    lines = [reasons.get("summary", "尚無狀態解釋。")]
    confirmed = reasons.get("confirmed", [])
    blockers = reasons.get("blockers", [])
    if confirmed:
        lines.append("已確認：")
        lines.extend(f"✓ {item}" for item in confirmed)
    if blockers:
        lines.append("尚未升級原因：")
        lines.extend(f"· {item}" for item in blockers)
    transition = state.get("transition_note")
    if transition:
        lines.append(f"狀態遲滯：{transition}")
    return lines


def _one_line(decision, analysis):
    state = decision.get("state_engine", {})
    persistence = state.get("persistence", {})
    velocity = state.get("velocity", {})
    paths = flow_map(analysis, limit=2)
    route = "；".join(f"{item['from']}→{item['to']}" for item in paths) if paths else "尚無清楚資金路徑"
    market_state = state.get("state", "NORMAL")
    accumulation = state.get("accumulation_score", 0)

    if market_state in {"SYSTEMIC", "LIQUIDITY_STRESS"}:
        return f"{state.get('state_zh')}已形成，風險累積度 {accumulation:.0f}%、高風險持續 {persistence.get('above_risk_off', 0)} 天；{route}。"
    if market_state in {"CREDIT_STRESS", "RISK_OFF"}:
        return f"風險撤退正在確認，≥25分已持續 {persistence.get('above_alert', 0)} 天，風險速度 {velocity.get('daily_velocity_5d')}／日；{route}。"
    if market_state == "ROTATION":
        return f"目前仍屬板塊輪動；風險累積度 {accumulation:.0f}%，但同步惡化廣度不足，尚未轉為全面避險；{route}。"
    return f"市場狀態正常，風險沒有形成持續且廣泛的撤退；{route}。"


def _analog_lines(decision):
    analogs = decision.get("historical_analogs", {})
    if not analogs.get("available"):
        return [f"尚未取得可用類比：{analogs.get('reason', '未知')}（可手動重建 analog library）"]
    output = []
    for index, match in enumerate(analogs.get("matches", []), 1):
        phase = f"Day {match.get('phase_day')}" if match.get("phase_day") else "階段未知"
        stage = match.get("next_stage", {})
        next_text = ""
        if stage.get("available"):
            leading = "、".join(stage.get("leading_components", [])) or "構成變化不明顯"
            next_text = f"｜後續{stage.get('horizon_days')}日：{stage.get('direction')}（風險{stage.get('risk_change'):+.1f}；{leading}）"
        else:
            next_text = f"｜後續：{stage.get('reason', '資料不足')}"
        output.append(
            f"{index}. {match['label']}｜相似 {match['similarity_pct']:.0f}%｜約 {phase}（{match.get('phase_date') or '--'}）｜軌跡 {match.get('trajectory_pct', '--')}%｜構成 {match.get('component_pct', '--')}%{next_text}"
        )
    return output


def telegram_message(version, generated, decision, analysis, statuses, history_rows, risk_history):
    inflow, outflow = ranked_rotation(analysis, limit=5)
    paths = flow_map(analysis, limit=3)
    lines = [
        f"🧠 PIOS 市場狀態引擎 V{version}",
        f"{decision['lamp']} OS 3.1.1：{decision['mode']}｜決策可信度 {decision['decision_confidence_pct']:.1f}%",
        f"時間：{generated}",
        "",
        "【今日一句話】",
        _one_line(decision, analysis),
        "",
        "【市場狀態】",
        *_state_summary(decision),
        "",
        "【狀態判斷依據】",
        *_state_reason_lines(decision),
        "",
        "【OS 建議】",
        decision["action"],
        "",
        "【資金流向地圖｜20D】",
    ]
    if paths:
        for index, path in enumerate(paths, 1):
            lines.append(
                f"{index}. {path['from']} {_fmt(path['from_change_20d'])} → {path['to']} {_fmt(path['to_change_20d'])}｜差 {path['spread_20d']:+.1f}｜強度 {path['strength_percentile']:.0f}% {_stars(path['stars'])}"
            )
    else:
        lines.append("資料不足")

    lines += ["", "【風險分數與貢獻】"]
    for component in decision["components"]:
        lines.append(f"- {component['name']}：{component['score']:.1f}/{component['max']}｜{component['regime']}")
        for part in component["parts"]:
            value = "缺資料" if pd.isna(part["value"]) else f"{part['value']:+.1f}"
            lines.append(f"  · {part['factor']} {value} → +{part['risk_points']:.1f}（{part['rule']}）")

    lines += [
        "",
        "【Top 5 流入領先｜多週期】",
        *_rotation_lines(inflow),
        "",
        "【Top 5 流出落後｜多週期】",
        *_rotation_lines(outflow),
        "",
        "【180天位置】",
    ]
    for factor in IMPORTANT_POSITIONS:
        row = analysis[analysis.factor == factor]
        if row.empty:
            continue
        item = row.iloc[0]
        if pd.notna(item.percentile_180d):
            lines.append(
                f"- {item.label}：{item.percentile_180d:.0f}%｜20D {_fmt(item.change_20d_pct)}｜強度 {item.strength_20d_pctile:.0f}% {_stars(item.strength_stars_20d)}｜{item.trend_phase}"
            )

    lines += ["", "【歷史相似度與階段】", *_analog_lines(decision)]
    anomalies = analysis[pd.to_numeric(analysis.zscore_180d, errors="coerce").abs() >= 2]
    lines += ["", "【180天事件時間軸】"]
    if anomalies.empty:
        lines.append("目前沒有 |Z|≥2 的異常事件。")
    else:
        for _, item in anomalies.head(6).iterrows():
            if bool(item.event_active):
                timeline = f"自 {item.event_start_date or '未知'} 起 {int(item.event_duration_days)} 天，{item.event_state}"
            else:
                timeline = f"已解除；最近 {item.last_z_event_date or '無'}"
            lines.append(
                f"⚠️ {item.label} Z {item.zscore_180d:+.2f}｜{timeline}｜180D共 {int(item.z_event_count_180d)} 天｜排名 {item.z_rank_abs_180d:.0f}%"
            )

    healthy = {"OK", "STANDBY", "SDK_AVAILABLE", "DISABLED"}
    implemented = [s for s in statuses if getattr(s, "adapter_state", "").startswith(("IMPLEMENTED", "OFFICIAL", "DERIVED"))]
    core = [s for s in implemented if getattr(s, "used_in_model", "NO") == "YES"]
    core_bad = [s for s in core if s.status not in healthy]
    lines += [
        "",
        "【資料品質】",
        f"核心模型來源 {sum(s.status in healthy for s in core)}/{len(core)} 正常｜市場歷史 {history_rows}/180｜風險歷史 {len(risk_history)}/180",
    ]
    if decision.get("missing_model_factors"):
        lines.append("缺模型因子：" + "、".join(decision["missing_model_factors"]))
    for provider_status in core_bad[:5]:
        lines.append(f"- {provider_status.source}：{provider_status.error_type or provider_status.status}")
    lines.append("完整診斷：data/source_status.csv")
    return "\n".join(lines)

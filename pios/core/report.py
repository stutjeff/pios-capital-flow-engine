from __future__ import annotations
import pandas as pd
from .scoring import ranked_rotation,flow_map

IMPORTANT_POSITIONS=["DXY_PROXY","US_10Y_YIELD","HY_OAS","VIX","QQQ","SOXX","GLD","TLT"]
STATE_ICON={"NORMAL":"🟢","ROTATION":"🔵","RISK_OFF":"🟡","CREDIT_STRESS":"🟠","LIQUIDITY_STRESS":"🔴","SYSTEMIC":"🚨"}


def _fmt(v):return "資料不足" if pd.isna(v) else f"{v:+.1f}%"
def _stars(n:int)->str:return "★"*max(0,min(5,int(n)))+"☆"*(5-max(0,min(5,int(n))))


def _rotation_lines(items):
    out=[]
    for i,item in enumerate(items,1):
        name,c20,c5,c60,c120,pctl,stars=item
        strength="資料不足" if pd.isna(pctl) else f"強度{pctl:.0f}% {_stars(stars)}"
        out.append(f"{i}. {name}｜5D {_fmt(c5)}｜20D {_fmt(c20)}｜60D {_fmt(c60)}｜120D {_fmt(c120)}｜{strength}")
    return out or ["資料不足"]


def _state_summary(d):
    s=d.get('state_engine',{}); m=s.get('momentum',{}); p=s.get('persistence',{}); b=s.get('breadth',{})
    scores="→".join(f"{x:.1f}" for x in s.get('recent_scores',[])[-7:]) or "資料不足"
    return [
        f"{STATE_ICON.get(s.get('state'),'⚪')} 市場狀態：{s.get('state_zh','未知')}（{s.get('state','UNKNOWN')}）",
        f"風險 {s.get('risk_score',0):.1f}/100｜180D {s.get('risk_percentile_180d','--')}%｜排名第 {s.get('risk_rank_180d','--')}/{s.get('history_count','--')}",
        f"近7日：{scores}",
        f"動能：1D {m.get('1d')}｜3D {m.get('3d')}｜5D {m.get('5d')}｜{m.get('label','')}",
        f"持續性：≥15分 {p.get('above_observe',0)}天｜≥25分 {p.get('above_alert',0)}天｜≥35分 {p.get('above_risk_off',0)}天",
        f"廣度：{b.get('active_count',0)}/{b.get('total_modules',5)} 模組同步升溫（{b.get('breadth_pct',0):.0f}%）",
    ]


def _one_line(d,a):
    s=d.get('state_engine',{}); p=s.get('persistence',{}); m=s.get('momentum',{})
    paths=flow_map(a,limit=2); route="；".join(f"{x['from']}→{x['to']}" for x in paths) if paths else "尚無清楚資金路徑"
    state=s.get('state','NORMAL')
    if state in {'SYSTEMIC','LIQUIDITY_STRESS'}:
        return f"{s.get('state_zh')}已形成，風險高檔持續 {p.get('above_risk_off',0)} 天；{route}。"
    if state in {'CREDIT_STRESS','RISK_OFF'}:
        return f"風險撤退正在確認，≥25分已持續 {p.get('above_alert',0)} 天，5日動能 {m.get('5d')}；{route}。"
    if state=='ROTATION':
        return f"目前仍屬板塊輪動，風險尚未擴散為全面避險；{route}。"
    return f"市場狀態正常，尚未形成持續且廣泛的撤退；{route}。"


def _analog_lines(d):
    x=d.get('historical_analogs',{})
    if not x.get('available'):
        return [f"尚未取得可用類比：{x.get('reason','未知')}（可手動重建 analog library）"]
    out=[]
    for i,m in enumerate(x.get('matches',[]),1):
        out.append(f"{i}. {m['label']}｜相似 {m['similarity_pct']:.0f}%｜軌跡 {m.get('trajectory_pct','--')}%｜構成 {m.get('component_pct','--')}%｜覆蓋 {m.get('coverage_pct','--')}%")
    return out


def _fusion_lines(d):
    f=d.get('radar_fusion',{}); inputs=f.get('inputs',{})
    out=[f"融合分數 {f.get('fused_score','--')}/100｜可用：{','.join(f.get('available_radars',[]))}"]
    for key,label in [('capital_flow','資金流'),('macro','宏觀'),('news','新聞')]:
        item=inputs.get(key)
        out.append(f"- {label}：{item['score']:.1f}（信心 {item['confidence']:.0f}%）" if item else f"- {label}：尚未接入快照")
    return out


def telegram_message(version,generated,d,a,statuses,history_rows,risk_history):
    inflow,outflow=ranked_rotation(a,limit=5); paths=flow_map(a,limit=3)
    lines=[
        f"🧠 PIOS 市場狀態引擎 V{version}",
        f"{d['lamp']} OS 3.1.1：{d['mode']}｜決策可信度 {d['decision_confidence_pct']:.1f}%",
        f"時間：{generated}","",
        "【今日一句話】",_one_line(d,a),"",
        "【市場狀態】",*_state_summary(d),"",
        "【OS 建議】",d['action'],"",
        "【資金流向地圖｜20D】",
    ]
    if paths:
        for i,p in enumerate(paths,1):lines.append(f"{i}. {p['from']} {_fmt(p['from_change_20d'])} → {p['to']} {_fmt(p['to_change_20d'])}｜差 {p['spread_20d']:+.1f}｜強度 {p['strength_percentile']:.0f}% {_stars(p['stars'])}")
    else:lines.append("資料不足")
    lines += ["","【風險分數與貢獻】"]
    for c in d['components']:
        lines.append(f"- {c['name']}：{c['score']:.1f}/{c['max']}｜{c['regime']}")
        for p in c['parts']:
            val="缺資料" if pd.isna(p['value']) else f"{p['value']:+.1f}"
            lines.append(f"  · {p['factor']} {val} → +{p['risk_points']:.1f}（{p['rule']}）")
    lines += ["","【Top 5 流入領先｜多週期】",*_rotation_lines(inflow),"","【Top 5 流出落後｜多週期】",*_rotation_lines(outflow),"","【180天位置】"]
    for f in IMPORTANT_POSITIONS:
        r=a[a.factor==f]
        if r.empty:continue
        x=r.iloc[0]
        if pd.notna(x.percentile_180d):lines.append(f"- {x.label}：{x.percentile_180d:.0f}%｜20D {_fmt(x.change_20d_pct)}｜強度 {x.strength_20d_pctile:.0f}% {_stars(x.strength_stars_20d)}｜{x.trend_phase}")
    lines += ["","【歷史相似度】",*_analog_lines(d),"","【三雷達融合】",*_fusion_lines(d)]
    anomalies=a[pd.to_numeric(a.zscore_180d,errors='coerce').abs()>=2]
    lines += ["","【180天事件時間軸】"]
    if anomalies.empty:lines.append("目前沒有 |Z|≥2 的異常事件。")
    else:
        for _,x in anomalies.head(6).iterrows():
            timeline=f"自 {x.event_start_date or '未知'} 起 {int(x.event_duration_days)} 天，{x.event_state}" if bool(x.event_active) else f"已解除；最近 {x.last_z_event_date or '無'}"
            lines.append(f"⚠️ {x.label} Z {x.zscore_180d:+.2f}｜{timeline}｜180D共 {int(x.z_event_count_180d)} 天｜排名 {x.z_rank_abs_180d:.0f}%")
    healthy={'OK','STANDBY','SDK_AVAILABLE','DISABLED'}
    implemented=[s for s in statuses if getattr(s,'adapter_state','').startswith(('IMPLEMENTED','OFFICIAL','DERIVED'))]
    core=[s for s in implemented if getattr(s,'used_in_model','NO')=='YES']
    core_bad=[s for s in core if s.status not in healthy]
    lines += ["","【資料品質】",f"核心模型來源 {sum(s.status in healthy for s in core)}/{len(core)} 正常｜市場歷史 {history_rows}/180｜風險歷史 {len(risk_history)}/180"]
    if d.get('missing_model_factors'):lines.append("缺模型因子："+'、'.join(d['missing_model_factors']))
    for s in core_bad[:5]:lines.append(f"- {s.source}：{s.error_type or s.status}")
    lines.append("完整診斷：data/source_status.csv")
    return "\n".join(lines)

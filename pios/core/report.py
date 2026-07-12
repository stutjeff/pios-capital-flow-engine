from __future__ import annotations
import os
import requests
import pandas as pd
from .scoring import ranked_rotation, one_line_summary, flow_map

IMPORTANT_POSITIONS=["DXY_PROXY","US_10Y_YIELD","HY_OAS","VIX","QQQ","SOXX","GLD","TLT"]

def _fmt(v): return "資料不足" if pd.isna(v) else f"{v:+.1f}%"
def _stars(n:int)->str:return "★"*max(0,min(5,int(n)))+"☆"*(5-max(0,min(5,int(n))))
def _rotation_lines(items):
    out=[]
    for i,item in enumerate(items,1):
        name,c20,c5,c60,c120,pctl,stars=item
        strength="資料不足" if pd.isna(pctl) else f"強度{pctl:.0f}% {_stars(stars)}"
        out.append(f"{i}. {name}｜5D {_fmt(c5)}｜20D {_fmt(c20)}｜60D {_fmt(c60)}｜120D {_fmt(c120)}｜{strength}")
    return out or ["資料不足"]

def _switch_lines(d):
    out=[]
    for mode in ("514","433"):
        p=d.get("switch_progress",{}).get(mode,{})
        if not p:continue
        if p.get("eligible"):
            out.append(f"- {mode}：條件已達標，仍需 crisis_memory／確認規則")
        else:
            out.append(f"- 距離 {mode}：風險還差 {p.get('risk_points_needed',0):.1f} 分；可信度還差 {p.get('confidence_points_needed',0):.1f} 分（進度 {p.get('risk_progress_pct',0):.0f}%／{p.get('confidence_progress_pct',0):.0f}%）")
    return out

def telegram_message(version,generated,d,a,statuses,history_rows):
    inflow,outflow=ranked_rotation(a,limit=5)
    paths=flow_map(a,limit=3)
    lines=[
        f"📡 PIOS 資金流主雷達 V{version}",
        f"{d['lamp']} OS 3.1.1：{d['mode']}｜風險 {d['risk_score']:.1f}/100",
        f"可信度 {d['decision_confidence_pct']:.1f}%（資料 {d['data_completeness_pct']:.1f}%／一致性 {d['signal_consistency_pct']:.1f}%）",
        f"時間：{generated}","",
        "【今日一句話】",one_line_summary(a),"",
        "【資金流向地圖｜20D】",
    ]
    if paths:
        for i,p in enumerate(paths,1):
            lines.append(f"{i}. {p['from']} {_fmt(p['from_change_20d'])} → {p['to']} {_fmt(p['to_change_20d'])}｜相對差 {p['spread_20d']:+.1f}｜強度 {p['strength_percentile']:.0f}% {_stars(p['stars'])}")
    else:lines.append("資料不足")
    lines += ["", "【OS 建議】",d["action"],*_switch_lines(d),"", "【風險分數與貢獻】"]
    for c in d["components"]:
        lines.append(f"- {c['name']}：{c['score']:.1f}/{c['max']}｜{c['regime']}")
        for p in c["parts"]:
            val="缺資料" if pd.isna(p['value']) else f"{p['value']:+.1f}"
            lines.append(f"  · {p['factor']} {val} → +{p['risk_points']:.1f}（{p['rule']}）")
    lines += ["", "【Top 5 流入領先｜多週期】", *_rotation_lines(inflow), "", "【Top 5 流出落後｜多週期】", *_rotation_lines(outflow), "", "【180天位置】"]
    for f in IMPORTANT_POSITIONS:
        r=a[a.factor==f]
        if r.empty: continue
        x=r.iloc[0]
        if pd.notna(x.percentile_180d): lines.append(f"- {x.label}：{x.percentile_180d:.0f}%｜20D {_fmt(x.change_20d_pct)}｜強度 {x.strength_20d_pctile:.0f}% {_stars(x.strength_stars_20d)}｜{x.trend_phase}")
    anomalies=a[pd.to_numeric(a.zscore_180d,errors='coerce').abs()>=2]
    lines += ["", "【180天事件時間軸】"]
    if anomalies.empty: lines.append("目前沒有 |Z|≥2 的異常事件。")
    else:
        for _,x in anomalies.head(8).iterrows():
            if bool(x.event_active):
                timeline=f"本次自 {x.event_start_date or '未知'} 起，已持續 {int(x.event_duration_days)} 天，{x.event_state}"
            else:
                timeline=f"目前已解除；最近一次 {x.last_z_event_date or '無'}"
            previous=f"｜近期事件 {x.previous_event_dates}" if str(x.previous_event_dates or '').strip() else ""
            lines.append(f"⚠️ {x.label} Z {x.zscore_180d:+.2f}｜{timeline}｜180天共 {int(x.z_event_count_180d)} 天｜強度排名 {x.z_rank_abs_180d:.0f}%{previous}")
    healthy={"OK","STANDBY","SDK_AVAILABLE","DISABLED"}
    implemented=[s for s in statuses if getattr(s,'adapter_state','').startswith(('IMPLEMENTED','OFFICIAL','DERIVED'))]
    core=[s for s in implemented if getattr(s,'used_in_model','NO')=='YES']
    core_bad=[s for s in core if s.status not in healthy]
    lines += ["", "【資料品質】",f"核心模型來源 {sum(s.status in healthy for s in core)}/{len(core)} 正常｜歷史視窗 {history_rows}/180"]
    if d['missing_model_factors']: lines.append("缺模型因子："+"、".join(d['missing_model_factors']))
    if core_bad:
        for s in core_bad[:6]: lines.append(f"- {s.source}：{s.error_type or s.status}"+(f" HTTP{s.http_code}" if s.http_code else ""))
    lines.append("完整診斷：data/source_status.csv")
    return "\n".join(lines)

def send_telegram(text:str)->tuple[bool,str]:
    token=os.getenv("TELEGRAM_BOT_TOKEN","").strip(); chat=os.getenv("TELEGRAM_CHAT_ID","").strip()
    if not token or not chat: return False,"MISSING_TELEGRAM_SECRET"
    try:
        r=requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":chat,"text":text,"disable_web_page_preview":True},timeout=30)
        return (True,"SENT") if r.ok else (False,f"HTTP_{r.status_code}:{r.text[:200]}")
    except requests.RequestException as e: return False,f"NETWORK_ERROR:{e}"

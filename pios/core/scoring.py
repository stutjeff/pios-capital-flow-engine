from __future__ import annotations

from typing import Any
from .config import load_yaml
import numpy as np
import pandas as pd

LABELS = {
    "DXY_PROXY":"美元","US_10Y_YIELD":"美國10年債殖利率","US_2Y_YIELD":"美國2年債殖利率",
    "US_3M_YIELD":"美國3月債殖利率","US_30Y_YIELD":"美國30年債殖利率",
    "HY_OAS":"高收益債利差","IG_OAS":"投資級債利差","BAA_10Y_SPREAD":"BAA信用利差",
    "VIX":"VIX","MOVE_PROXY":"債市波動代理","WTI_OIL":"WTI原油","SPY":"美股大盤",
    "QQQ":"Nasdaq 100","IWM":"美國小型股","SOXX":"半導體","SMH":"半導體ETF",
    "GLD":"黃金","TLT":"長天期美債","HYG":"高收益債ETF","LQD":"投資級債ETF",
    "EEM":"新興市場","FXI":"中國大型股","XLF_FINANCIALS":"金融","XLE_ENERGY":"能源",
    "XLU_UTILITIES":"公用事業","XLK_TECH":"科技","XLP_STAPLES":"必需消費",
    "CFTC_SP500_ASSET_MGR_NET":"CFTC S&P500資產管理人淨部位",
}
MODEL_FACTORS = load_yaml("scoring.yaml").get("model_factors", ["DXY_PROXY","US_10Y_YIELD","HY_OAS","IG_OAS","VIX","SPY","QQQ","IWM","SOXX","GLD","TLT","EEM","XLF_FINANCIALS"])
ROTATION_FACTORS = {
    "金融":"XLF_FINANCIALS","能源":"XLE_ENERGY","公用事業":"XLU_UTILITIES",
    "科技":"XLK_TECH","半導體":"SOXX","新興市場":"EEM","中國":"FXI",
    "黃金":"GLD","長債":"TLT","美股大盤":"SPY","小型股":"IWM",
    "高收益債":"HYG","投資級債":"LQD","必需消費":"XLP_STAPLES",
}

ANALYSIS_COLUMNS = [
    "factor","label","latest","rows","change_5d_pct","change_20d_pct","change_60d_pct","change_120d_pct",
    "strength_5d_pctile","strength_20d_pctile","strength_60d_pctile","strength_120d_pctile","strength_stars_20d",
    "percentile_180d","zscore_180d","min_180d","max_180d","z_event_count_180d","z_rank_abs_180d",
    "last_z_event_date","event_active","event_start_date","event_duration_days","event_state","previous_event_dates",
    "trend_phase"
]

def _series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").dropna()

def pct_change(s: pd.Series, n: int) -> float:
    x=_series(s)
    if len(x)<=n or x.iloc[-n-1]==0: return float("nan")
    return float((x.iloc[-1]/x.iloc[-n-1]-1)*100)

def rolling_return(s: pd.Series, n: int) -> pd.Series:
    x=pd.to_numeric(s,errors="coerce")
    return x.pct_change(n,fill_method=None)*100

def absolute_strength_percentile(s: pd.Series,n:int)->float:
    r=rolling_return(s,n).dropna()
    if len(r)<20:return float("nan")
    latest=abs(float(r.iloc[-1])); hist=r.abs()
    return float((hist<=latest).mean()*100)

def strength_stars(percentile_value:float)->int:
    if pd.isna(percentile_value):return 0
    if percentile_value>=95:return 5
    if percentile_value>=80:return 4
    if percentile_value>=60:return 3
    if percentile_value>=35:return 2
    return 1

def percentile(s: pd.Series) -> float:
    x=_series(s)
    return float((x<=x.iloc[-1]).mean()*100) if len(x)>=20 else float("nan")

def zscore_series(s: pd.Series) -> pd.Series:
    x=pd.to_numeric(s,errors="coerce")
    mean=x.rolling(180,min_periods=20).mean(); std=x.rolling(180,min_periods=20).std(ddof=0)
    return (x-mean)/std.replace(0,np.nan)

def trend_phase(c5:float,c20:float,c60:float)->str:
    vals=[c5,c20,c60]
    if any(pd.isna(v) for v in vals): return "資料不足"
    if c5>0 and c20>0 and c60>0: return "多週期上升"
    if c5<0 and c20<0 and c60<0: return "多週期下降"
    if c5>0 and c20<0: return "短線反彈"
    if c5<0 and c20>0: return "短線轉弱"
    return "輪動交錯"

def _event_metadata(z:pd.Series,dates:pd.Series)->dict[str,Any]:
    active=(z.abs()>=2).fillna(False)
    event_dates=dates[active] if len(dates)==len(active) else pd.Series(dtype="datetime64[ns]")
    latest_active=bool(active.iloc[-1]) if len(active) else False
    duration=0; start=""; state="無異常"
    if latest_active:
        idx=len(active)-1
        while idx>=0 and bool(active.iloc[idx]):
            duration+=1; idx-=1
        start_date=dates.iloc[len(active)-duration] if len(dates)==len(active) else pd.NaT
        start=str(start_date.date()) if pd.notna(start_date) else ""
        current_abs=abs(float(z.iloc[-1])) if pd.notna(z.iloc[-1]) else np.nan
        prev_abs=abs(float(z.iloc[-2])) if len(z)>1 and pd.notna(z.iloc[-2]) else np.nan
        if pd.notna(current_abs) and pd.notna(prev_abs):
            state="擴大中" if current_abs>prev_abs+0.05 else "消退中" if current_abs<prev_abs-0.05 else "持平"
        else: state="持續中"
    prior=[]
    if not event_dates.empty:
        unique=[str(x.date()) for x in event_dates.dropna().tail(8)]
        if latest_active and unique: unique=unique[:-1]
        prior=unique[-5:]
    return {"event_active":latest_active,"event_start_date":start,"event_duration_days":duration,"event_state":state,"previous_event_dates":"、".join(prior)}

def analyze(ts: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    dates=pd.to_datetime(ts.get("date"),errors="coerce")
    for col in ts.columns:
        if col=="date": continue
        raw=pd.to_numeric(ts[col],errors="coerce")
        valid=raw.dropna(); z=zscore_series(raw)
        latest_z=float(z.dropna().iloc[-1]) if not z.dropna().empty else float("nan")
        events=z.abs()>=2
        event_count=int(events.fillna(False).sum())
        event_dates=dates[events.fillna(False)] if len(dates)==len(events) else pd.Series(dtype="datetime64[ns]")
        last_event=str(event_dates.max().date()) if not event_dates.empty and pd.notna(event_dates.max()) else ""
        abs_z=z.abs().dropna()
        rank=float((abs_z<=abs(latest_z)).mean()*100) if len(abs_z) and pd.notna(latest_z) else float("nan")
        c5,c20,c60,c120=[pct_change(raw,n) for n in (5,20,60,120)]
        s5,s20,s60,s120=[absolute_strength_percentile(raw,n) for n in (5,20,60,120)]
        event_meta=_event_metadata(z,dates)
        rows.append({
            "factor":col,"label":LABELS.get(col,col),"latest":valid.iloc[-1] if len(valid) else np.nan,
            "rows":len(valid),"change_5d_pct":c5,"change_20d_pct":c20,"change_60d_pct":c60,"change_120d_pct":c120,
            "strength_5d_pctile":s5,"strength_20d_pctile":s20,"strength_60d_pctile":s60,"strength_120d_pctile":s120,
            "strength_stars_20d":strength_stars(s20),
            "percentile_180d":percentile(raw),"zscore_180d":latest_z,
            "min_180d":valid.min() if len(valid) else np.nan,"max_180d":valid.max() if len(valid) else np.nan,
            "z_event_count_180d":event_count,"z_rank_abs_180d":rank,"last_z_event_date":last_event,
            **event_meta,
            "trend_phase":trend_phase(c5,c20,c60),
        })
    return pd.DataFrame(rows,columns=ANALYSIS_COLUMNS)

def av(a:pd.DataFrame,factor:str,field:str)->float:
    if a.empty or field not in a.columns: return float("nan")
    r=a.loc[a.factor==factor]
    return float(pd.to_numeric(r.iloc[0][field],errors="coerce")) if not r.empty else float("nan")

def _bounded(v:float,m:float)->float: return round(min(max(float(v),0.0),m),1)
def _regime(v:float,m:float)->str:
    ratio=v/m if m else 0
    return "高風險" if ratio>=.70 else "升溫" if ratio>=.35 else "正常"

def _switch_progress(risk:float,confidence:float,thresholds:dict)->dict[str,dict[str,float]]:
    out={}
    for mode,key in (("514","mode_514"),("433","mode_433")):
        cfg=thresholds.get(key,{})
        target_r=float(cfg.get("risk",30 if mode=="514" else 55)); target_c=float(cfg.get("confidence",65 if mode=="514" else 70))
        out[mode]={
            "risk_target":target_r,"confidence_target":target_c,
            "risk_points_needed":round(max(0,target_r-risk),1),
            "confidence_points_needed":round(max(0,target_c-confidence),1),
            "risk_progress_pct":round(min(100,risk/target_r*100),1) if target_r else 100,
            "confidence_progress_pct":round(min(100,confidence/target_c*100),1) if target_c else 100,
            "eligible":bool(risk>=target_r and confidence>=target_c),
        }
    return out

def decision(a:pd.DataFrame)->dict[str,Any]:
    present=[f for f in MODEL_FACTORS if pd.notna(av(a,f,"latest"))]
    missing=[f for f in MODEL_FACTORS if f not in present]
    completeness=len(present)/len(MODEL_FACTORS)*100
    comps=[]
    def add(name,max_score,parts):
        score=_bounded(sum(p["risk_points"] for p in parts),max_score)
        comps.append({"name":name,"max":max_score,"score":score,"regime":_regime(score,max_score),"parts":parts})

    hy,ig=av(a,"HY_OAS","change_20d_pct"),av(a,"IG_OAS","change_20d_pct")
    add("信用市場",20,[
        {"factor":"HY OAS","value":hy,"risk_points":max(0,hy if pd.notna(hy) else 0)*1.5,"rule":"20D 擴大×1.5"},
        {"factor":"IG OAS","value":ig,"risk_points":max(0,ig if pd.notna(ig) else 0)*1.5,"rule":"20D 擴大×1.5"},
    ])
    vixp=av(a,"VIX","percentile_180d")
    add("波動率",15,[{"factor":"VIX 180D位置","value":vixp,"risk_points":max(0,vixp if pd.notna(vixp) else 0)*.15,"rule":"百分位×0.15"}])
    dxy,y10=av(a,"DXY_PROXY","change_20d_pct"),av(a,"US_10Y_YIELD","change_20d_pct")
    add("美元與利率",20,[
        {"factor":"美元20D","value":dxy,"risk_points":max(0,dxy if pd.notna(dxy) else 0)*2,"rule":"正報酬×2"},
        {"factor":"10Y殖利率20D","value":y10,"risk_points":max(0,y10 if pd.notna(y10) else 0),"rule":"正變化×1"},
    ])
    q,soxx,spy=[av(a,f,"change_20d_pct") for f in ("QQQ","SOXX","SPY")]
    add("風險資產撤退",25,[
        {"factor":"QQQ20D","value":q,"risk_points":max(0,-q if pd.notna(q) else 0)*.8,"rule":"跌幅×0.8"},
        {"factor":"SOXX20D","value":soxx,"risk_points":max(0,-soxx if pd.notna(soxx) else 0)*.8,"rule":"跌幅×0.8"},
        {"factor":"SPY20D","value":spy,"risk_points":max(0,-spy if pd.notna(spy) else 0)*.8,"rule":"跌幅×0.8"},
    ])
    g,t=av(a,"GLD","change_20d_pct"),av(a,"TLT","change_20d_pct")
    add("避險與防禦輪動",20,[
        {"factor":"黃金20D","value":g,"risk_points":max(0,g if pd.notna(g) else 0)*.8,"rule":"上漲×0.8"},
        {"factor":"長債20D","value":t,"risk_points":max(0,t if pd.notna(t) else 0)*.8,"rule":"上漲×0.8"},
    ])
    risk=round(sum(x["score"] for x in comps),1)
    confirms=sum([pd.notna(hy) and hy>0,pd.notna(ig) and ig>0,pd.notna(q) and q<0,pd.notna(soxx) and soxx<0,pd.notna(g) and g>0,pd.notna(t) and t>0,pd.notna(dxy) and dxy>0])
    consistency=50+confirms/7*50
    confidence=.65*completeness+.35*consistency
    thresholds=load_yaml("scoring.yaml").get("thresholds", {})
    t433=thresholds.get("mode_433", {"risk":55,"confidence":70}); t514=thresholds.get("mode_514", {"risk":30,"confidence":65})
    if risk>=float(t433.get("risk",55)) and confidence>=float(t433.get("confidence",70)): mode,lamp,action="433","🔴","危機模式候選；先依 crisis_memory 與確認規則檢查，再執行切換。"
    elif risk>=float(t514.get("risk",30)) and confidence>=float(t514.get("confidence",65)): mode,lamp,action="514","🟡","市場升溫；降低槓桿、提高短債比例。"
    else: mode,lamp,action="452","🟢","維持正常配置；尚未形成足夠一致的全面撤退證據。"
    return {"mode":mode,"lamp":lamp,"risk_score":risk,"components":comps,"data_completeness_pct":round(completeness,1),"signal_consistency_pct":round(consistency,1),"decision_confidence_pct":round(confidence,1),"missing_model_factors":missing,"action":action,"switch_progress":_switch_progress(risk,confidence,thresholds)}

def ranked_rotation(a:pd.DataFrame,field="change_20d_pct",limit=5):
    vals=[]
    for name,f in ROTATION_FACTORS.items():
        v=av(a,f,field)
        if pd.notna(v): vals.append((name,v,av(a,f,"change_5d_pct"),av(a,f,"change_60d_pct"),av(a,f,"change_120d_pct"),av(a,f,"strength_20d_pctile"),int(av(a,f,"strength_stars_20d")) if pd.notna(av(a,f,"strength_stars_20d")) else 0))
    vals.sort(key=lambda x:x[1],reverse=True)
    return vals[:limit],list(reversed(vals[-limit:]))

def flow_map(a:pd.DataFrame,limit:int=3)->list[dict[str,Any]]:
    inflow,outflow=ranked_rotation(a,limit=limit)
    paths=[]
    for i in range(min(len(inflow),len(outflow),limit)):
        dst=inflow[i]; src=outflow[i]
        paths.append({
            "from":src[0],"to":dst[0],"from_change_20d":src[1],"to_change_20d":dst[1],
            "spread_20d":round(dst[1]-src[1],1),"strength_percentile":round(max(src[5] if pd.notna(src[5]) else 0,dst[5] if pd.notna(dst[5]) else 0),1),
            "stars":max(src[6],dst[6]),
        })
    return paths

def one_line_summary(a:pd.DataFrame)->str:
    paths=flow_map(a,limit=3)
    q=av(a,"QQQ","change_20d_pct"); soxx=av(a,"SOXX","change_20d_pct"); vixp=av(a,"VIX","percentile_180d"); hy=av(a,"HY_OAS","change_20d_pct")
    broad_retreat=sum(pd.notna(x) and x<0 for x in (q,soxx))>=2 and pd.notna(vixp) and vixp>=70 and pd.notna(hy) and hy>0
    if paths:
        route="；".join(f"{p['from']}→{p['to']}" for p in paths)
    else: route="目前無清楚路徑"
    if broad_retreat: return f"主要路徑：{route}；波動與信用壓力共振，較接近全面避險。"
    return f"主要路徑：{route}；目前較像板塊輪動，尚非全面避險。"

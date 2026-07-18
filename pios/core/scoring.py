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
    "TW_LARGE_CAP":"台灣大型股","TW_TECH":"台灣科技","TW_SEMICONDUCTOR":"台灣半導體",
    "JP_TOPIX":"日本TOPIX代理","JP_NIKKEI":"日本日經225代理","JP_BANKS":"日本銀行",
    "CN_CSI300":"中國滬深300代理","CN_CHINEXT":"中國創業板代理",
    "HK_HSI":"香港恆生代理","HK_TECH":"香港恆生科技代理",
}
MODEL_FACTORS = load_yaml("scoring.yaml").get("model_factors", ["DXY_PROXY","US_10Y_YIELD","HY_OAS","IG_OAS","VIX","SPY","QQQ","IWM","SOXX","GLD","TLT","EEM","XLF_FINANCIALS"])
ROTATION_FACTORS = {
    "金融":"XLF_FINANCIALS","能源":"XLE_ENERGY","公用事業":"XLU_UTILITIES",
    "科技":"XLK_TECH","半導體":"SOXX","新興市場":"EEM","中國":"FXI",
    "黃金":"GLD","長債":"TLT","美股大盤":"SPY","小型股":"IWM",
    "高收益債":"HYG","投資級債":"LQD","必需消費":"XLP_STAPLES",
    "台灣大型股":"TW_LARGE_CAP","台灣科技":"TW_TECH","台灣半導體":"TW_SEMICONDUCTOR",
    "日本大盤":"JP_TOPIX","日本日經":"JP_NIKKEI","中國滬深300":"CN_CSI300",
    "中國創業板":"CN_CHINEXT","香港大盤":"HK_HSI","香港科技":"HK_TECH",
}

ANALYSIS_COLUMNS = [
    "factor","label","latest","rows","change_1d_pct","change_5d_pct","change_20d_pct","change_60d_pct","change_120d_pct",
    "strength_5d_pctile","strength_20d_pctile","strength_60d_pctile","strength_120d_pctile","strength_stars_20d",
    "percentile_180d","zscore_180d","min_180d","max_180d","z_event_count_180d","z_rank_abs_180d",
    "last_z_event_date","event_active","event_start_date","event_duration_days","event_state","previous_event_dates",
    "trend_phase","latest_date","market_session","region","data_lag_hours","data_type","freshness_state"
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

def analyze(ts: pd.DataFrame, metadata: dict[str,dict] | None = None) -> pd.DataFrame:
    rows=[]
    metadata=metadata or {}
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
        c1,c5,c20,c60,c120=[pct_change(raw,n) for n in (1,5,20,60,120)]
        s5,s20,s60,s120=[absolute_strength_percentile(raw,n) for n in (5,20,60,120)]
        event_meta=_event_metadata(z,dates)
        meta=metadata.get(col,{})
        lag=meta.get("data_lag_hours")
        freshness="UNKNOWN" if lag is None else "FRESH" if float(lag)<=36 else "STALE" if float(lag)<=72 else "VERY_STALE"
        rows.append({
            "factor":col,"label":meta.get("label") or LABELS.get(col,col),"latest":valid.iloc[-1] if len(valid) else np.nan,
            "rows":len(valid),"change_1d_pct":c1,"change_5d_pct":c5,"change_20d_pct":c20,"change_60d_pct":c60,"change_120d_pct":c120,
            "strength_5d_pctile":s5,"strength_20d_pctile":s20,"strength_60d_pctile":s60,"strength_120d_pctile":s120,
            "strength_stars_20d":strength_stars(s20),
            "percentile_180d":percentile(raw),"zscore_180d":latest_z,
            "min_180d":valid.min() if len(valid) else np.nan,"max_180d":valid.max() if len(valid) else np.nan,
            "z_event_count_180d":event_count,"z_rank_abs_180d":rank,"last_z_event_date":last_event,
            **event_meta,
            "trend_phase":trend_phase(c5,c20,c60),
            "latest_date":meta.get("latest_date", ""),"market_session":meta.get("market_session", ""),
            "region":meta.get("region", ""),"data_lag_hours":lag,"data_type":meta.get("data_type", ""),
            "freshness_state":freshness,
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

def _direction_consistency(a:pd.DataFrame,factor:str,direction:int)->tuple[int,list[str]]:
    checks=[]; passed=0
    for field,label in (("change_1d_pct","1D"),("change_5d_pct","5D"),("change_20d_pct","20D")):
        value=av(a,factor,field)
        ok=pd.notna(value) and (value*direction)>0
        checks.append(f"{label}{'✓' if ok else '×'}")
        passed+=int(ok)
    return passed,checks


def _evidence_level(a:pd.DataFrame,src_factor:str,dst_factor:str)->dict[str,Any]:
    src_pass,src_checks=_direction_consistency(a,src_factor,-1)
    dst_pass,dst_checks=_direction_consistency(a,dst_factor,1)
    strength=max(av(a,src_factor,"strength_20d_pctile"),av(a,dst_factor,"strength_20d_pctile"))
    freshness=[]
    for factor in (src_factor,dst_factor):
        row=a.loc[a.factor==factor]
        freshness.append(str(row.iloc[0].freshness_state) if not row.empty and 'freshness_state' in row else 'UNKNOWN')
    fresh_ok=all(x in {'FRESH','UNKNOWN'} for x in freshness)
    score=src_pass+dst_pass+int(pd.notna(strength) and strength>=70)+int(fresh_ok)
    if score>=7: level='高度確認'
    elif score>=5: level='初步確認'
    else: level='推測'
    return {
        'level':level,'evidence_score':score,'max_evidence_score':8,
        'checks':src_checks+dst_checks,'freshness_ok':fresh_ok,
        'flow_type':'PRICE_ROTATION_PROXY','true_flow_confirmed':False,
        'disclaimer':'相對價格輪動代理，不等同ETF申購贖回或實際資金轉帳。',
    }


def flow_map(a:pd.DataFrame,limit:int=3)->list[dict[str,Any]]:
    inflow,outflow=ranked_rotation(a,limit=limit)
    paths=[]
    reverse={name:factor for name,factor in ROTATION_FACTORS.items()}
    for i in range(min(len(inflow),len(outflow),limit)):
        dst=inflow[i]; src=outflow[i]
        evidence=_evidence_level(a,reverse[src[0]],reverse[dst[0]])
        paths.append({
            "from":src[0],"to":dst[0],"from_change_20d":src[1],"to_change_20d":dst[1],
            "spread_20d":round(dst[1]-src[1],1),"strength_percentile":round(max(src[5] if pd.notna(src[5]) else 0,dst[5] if pd.notna(dst[5]) else 0),1),
            "stars":max(src[6],dst[6]),**evidence,
        })
    return paths


def rotation_evidence_summary(a:pd.DataFrame)->dict[str,Any]:
    paths=flow_map(a,limit=5)
    counts={"推測":0,"初步確認":0,"高度確認":0}
    for p in paths: counts[p['level']]+=1
    return {"paths":paths,"counts":counts,"confirmed_paths":sum(1 for p in paths if p['level']!='推測'),"all_price_proxy":True}


def _row_dict(a:pd.DataFrame,factor:str)->dict[str,Any]|None:
    row=a.loc[a.factor==factor]
    if row.empty:return None
    x=row.iloc[0]
    return {k:(None if pd.isna(x.get(k)) else x.get(k)) for k in a.columns}


def build_time_layers(a:pd.DataFrame)->dict[str,Any]:
    asia_factors=['TW_LARGE_CAP','TW_TECH','TW_SEMICONDUCTOR','JP_TOPIX','JP_NIKKEI','JP_BANKS','CN_CSI300','CN_CHINEXT','HK_HSI','HK_TECH']
    us_factors=['SPY','QQQ','SOXX','XLF_FINANCIALS','XLE_ENERGY','XLP_STAPLES']
    def items(factors,field):
        out=[]
        for f in factors:
            row=_row_dict(a,f)
            if row and row.get(field) is not None:
                out.append({"factor":f,"label":row.get('label'),"change_pct":round(float(row[field]),2),"latest_date":row.get('latest_date'),"freshness":row.get('freshness_state'),"lag_hours":row.get('data_lag_hours')})
        return sorted(out,key=lambda x:x['change_pct'])
    return {
        'latest_session':{'us_previous_close':items(us_factors,'change_1d_pct'),'asia_current_close':items(asia_factors,'change_1d_pct')},
        'short_term_5d':items(us_factors+asia_factors,'change_5d_pct'),
        'rotation_20d':items(list(ROTATION_FACTORS.values()),'change_20d_pct'),
        'medium_term_60d':items(list(ROTATION_FACTORS.values()),'change_60d_pct'),
        'definition':{'1d':'最近可得交易時段','5d':'短期','20d':'輪動代理','60d':'中期結構'},
    }


def build_contagion(a:pd.DataFrame)->dict[str,Any]:
    us_semis=[av(a,'SOXX','change_1d_pct'),av(a,'SOXX','change_5d_pct')]
    asia_semis=[]
    for f in ('TW_SEMICONDUCTOR','TW_TECH','JP_NIKKEI','HK_TECH','CN_CHINEXT'):
        v=av(a,f,'change_1d_pct')
        if pd.notna(v): asia_semis.append(v)
    broad=[]
    for f in ('SPY','TW_LARGE_CAP','JP_TOPIX','CN_CSI300','HK_HSI'):
        v=av(a,f,'change_1d_pct')
        if pd.notna(v): broad.append(v)
    us_shock=any(pd.notna(v) and v<=-2 for v in us_semis)
    asia_follow=bool(asia_semis) and sum(v<0 for v in asia_semis)/len(asia_semis)>=0.6
    broad_follow=bool(broad) and sum(v<0 for v in broad)/len(broad)>=0.6
    credit=av(a,'HY_OAS','change_20d_pct'); ig=av(a,'IG_OAS','change_20d_pct')
    credit_confirm=(pd.notna(credit) and credit>2) or (pd.notna(ig) and ig>2)
    vixp=av(a,'VIX','percentile_180d'); gld=av(a,'GLD','change_5d_pct'); tlt=av(a,'TLT','change_5d_pct')
    haven_confirm=(pd.notna(vixp) and vixp>=70) or ((pd.notna(gld) and gld>1) and (pd.notna(tlt) and tlt>1))
    stage=0
    if us_shock: stage=1
    if stage>=1 and asia_follow: stage=2
    if stage>=2 and broad_follow: stage=3
    if stage>=3 and (credit_confirm or haven_confirm): stage=4
    return {
        'stage':stage,'max_stage':4,'label':['未形成','單一市場衝擊','跨區域產業傳導','擴散至大盤','信用/避險確認'][stage],
        'us_semiconductor_shock':us_shock,'asia_sector_followthrough':asia_follow,'global_broadening':broad_follow,
        'credit_or_haven_confirmation':bool(credit_confirm or haven_confirm),'asia_observations':len(asia_semis),'broad_observations':len(broad),
        'interpretation':'跨市場傳導分數只描述擴散階段，不預測後續漲跌。',
    }

def one_line_summary(a:pd.DataFrame)->str:
    paths=flow_map(a,limit=3)
    q=av(a,"QQQ","change_20d_pct"); soxx=av(a,"SOXX","change_20d_pct"); vixp=av(a,"VIX","percentile_180d"); hy=av(a,"HY_OAS","change_20d_pct")
    broad_retreat=sum(pd.notna(x) and x<0 for x in (q,soxx))>=2 and pd.notna(vixp) and vixp>=70 and pd.notna(hy) and hy>0
    if paths:
        route="；".join(f"{p['from']}→{p['to']}" for p in paths)
    else: route="目前無清楚路徑"
    if broad_retreat: return f"主要路徑：{route}；波動與信用壓力共振，較接近全面避險。"
    return f"主要路徑：{route}；目前較像板塊輪動，尚非全面避險。"

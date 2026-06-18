#!/usr/bin/env python3
"""
Trợ Lý Tiết Kiệm Điện — Web App
pip install flask  ->  python web_app.py  ->  http://localhost:5000
"""

import json, math, os
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Tuple
from flask import Flask, jsonify, render_template, request

# ══════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════

@dataclass
class Device:
    id: str; name: str; power_w: int; priority: int
    max_daily_hours: float; category: str
    def kwh(self, h): return self.power_w * h / 1000
    def to_dict(self): return self.__dict__.copy()

@dataclass
class UsageEntry:
    device_id: str; date: str; hours: float; note: str = ""
    def to_dict(self): return self.__dict__.copy()

@dataclass
class Config:
    daily_budget_kwh: float = 2.0
    electricity_rate: float = 3500.0
    peak_hours: List[int] = field(default_factory=lambda: [17,18,19,20,21])
    def to_dict(self): return self.__dict__.copy()

DEFAULT_DEVICES: List[Device] = [
    Device("ac",      "Điều hòa",        900,  4,  8.0, "cooling"),
    Device("fan",     "Quạt điện",        55,  5, 12.0, "cooling"),
    Device("light",   "Đèn LED",          15,  5, 12.0, "lighting"),
    Device("laptop",  "Laptop",           65,  5, 10.0, "computing"),
    Device("phone",   "Sạc điện thoại",   10,  4,  4.0, "computing"),
    Device("heater",  "Bình nước nóng", 2000,  3,  1.0, "heating"),
    Device("tv",      "Tivi",            100,  2,  4.0, "entertainment"),
    Device("rice",    "Nồi cơm điện",    700,  5,  1.0, "cooking"),
    Device("fridge",  "Tủ lạnh mini",     80,  3, 24.0, "cooling"),
    Device("washing", "Máy giặt",        500,  4,  1.0, "cleaning"),
]

# ══════════════════════════════════════════════════════════════
# STORAGE
# ══════════════════════════════════════════════════════════════

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_DEVICES = os.path.join(_DIR, "devices.json")
_USAGE   = os.path.join(_DIR, "usage.json")
_CONFIG  = os.path.join(_DIR, "config.json")

def _ensure(): os.makedirs(_DIR, exist_ok=True)

def load_devices():
    _ensure()
    if not os.path.exists(_DEVICES): save_devices(list(DEFAULT_DEVICES)); return list(DEFAULT_DEVICES)
    with open(_DEVICES, encoding="utf-8") as f: return [Device(**d) for d in json.load(f)]

def save_devices(devs):
    _ensure()
    with open(_DEVICES,"w",encoding="utf-8") as f: json.dump([d.__dict__ for d in devs],f,ensure_ascii=False,indent=2)

def load_usage():
    _ensure()
    if not os.path.exists(_USAGE): return []
    with open(_USAGE, encoding="utf-8") as f: return [UsageEntry(**e) for e in json.load(f)]

def save_usage(entries):
    _ensure()
    with open(_USAGE,"w",encoding="utf-8") as f: json.dump([e.__dict__ for e in entries],f,ensure_ascii=False,indent=2)

def load_config():
    _ensure()
    if not os.path.exists(_CONFIG): return Config()
    with open(_CONFIG, encoding="utf-8") as f: return Config(**json.load(f))

def save_config(c):
    _ensure()
    with open(_CONFIG,"w",encoding="utf-8") as f: json.dump(c.__dict__,f,ensure_ascii=False,indent=2)

# ══════════════════════════════════════════════════════════════
# ALGORITHMS
# ══════════════════════════════════════════════════════════════

BUDGET_UNIT = 0.01
HOUR_STEP   = 0.5

def _opts(dev):
    r=[]; h=HOUR_STEP
    while h<=dev.max_daily_hours+1e-9:
        r.append((max(1,int(dev.kwh(h)/BUDGET_UNIT+0.5)), dev.priority*h, h)); h+=HOUR_STEP
    return r

def dp_optimize(devices, budget_kwh):
    n=len(devices); W=int(budget_kwh/BUDGET_UNIT)+1
    dp=[[0.0]*W for _ in range(n+1)]; ch=[[0.0]*W for _ in range(n)]
    for i,dev in enumerate(devices):
        opts=_opts(dev)
        for j in range(W):
            dp[i+1][j]=dp[i][j]
            for cu,val,h in opts:
                if j>=cu and dp[i][j-cu]+val>dp[i+1][j]:
                    dp[i+1][j]=dp[i][j-cu]+val; ch[i][j]=h
    bj=max(range(W),key=lambda j:dp[n][j]); sc=[]; j=bj
    for i in range(n-1,-1,-1):
        h=ch[i][j]
        if h>0:
            cu=max(1,int(devices[i].kwh(h)/BUDGET_UNIT+0.5))
            sc.append({"device":devices[i].to_dict(),"hours":h,
                       "kwh":round(devices[i].kwh(h),3),"comfort":round(devices[i].priority*h,1)})
            j-=cu
    no=max((len(_opts(d)) for d in devices),default=1)
    return {"schedule":sorted(sc,key=lambda x:-x["comfort"]),"total_comfort":round(dp[n][bj],1),
            "total_kwh":round(sum(s["kwh"] for s in sc),3),"algorithm":"DP — Group Knapsack",
            "complexity":f"O(n×W×H) = O({n}×{W}×{no}) ≈ {n*W*no:,} ops"}

def greedy_optimize(devices, budget_kwh):
    sc=[]; rem=budget_kwh
    for dev in sorted(devices,key=lambda d:d.priority/d.power_w,reverse=True):
        if rem<1e-9: break
        h=math.floor(min(dev.max_daily_hours,rem/(dev.power_w/1000))/HOUR_STEP)*HOUR_STEP
        if h>=HOUR_STEP:
            sc.append({"device":dev.to_dict(),"hours":h,"kwh":round(dev.kwh(h),3),"comfort":round(dev.priority*h,1)})
            rem-=dev.kwh(h)
    return {"schedule":sorted(sc,key=lambda x:-x["comfort"]),"total_comfort":round(sum(s["comfort"] for s in sc),1),
            "total_kwh":round(sum(s["kwh"] for s in sc),3),"algorithm":"Greedy — Ưu tiên/Công suất","complexity":"O(n log n)"}

def calc_evn(kwh):
    tiers=[(50,1806),(50,1866),(100,2167),(100,2729),(100,3050),(9999,3151)]
    cost=0; rem=kwh
    for lim,rate in tiers:
        used=min(rem,lim); cost+=used*rate; rem-=used
        if rem<=0: break
    return cost

def smart_tips(devices,usage,config):
    dev_map={d.id:d for d in devices}; tips=[]
    dates_used=set(e.date for e in usage)
    n_days=max(len(dates_used),1)
    for dev in sorted(devices,key=lambda d:-d.power_w):
        total_h=sum(e.hours for e in usage if e.device_id==dev.id)
        if not total_h: continue
        avg_h=total_h/n_days
        if avg_h>dev.max_daily_hours*0.75 and dev.power_w>=200:
            save=dev.kwh(avg_h*0.2)
            tips.append({"device":dev.name,"power":dev.power_w,
                "msg":f"Giảm 20% → tiết kiệm ~{save:.2f} kWh/ngày (~{save*30*config.electricity_rate:,.0f} VND/tháng)",
                "save_kwh":round(save,3),"level":"danger" if dev.power_w>=500 else "warning"})
        if len(tips)>=4: break
    return tips

# ══════════════════════════════════════════════════════════════
# FLASK ROUTES
# ══════════════════════════════════════════════════════════════

app = Flask(__name__)

@app.route("/")
def index(): return render_template("index.html")

@app.route("/flowchart")
def flowchart(): return render_template("flowchart.html")

# ── Devices ───────────────────────────────────────────────────
@app.route("/api/devices")
def r_devices(): return jsonify([d.to_dict() for d in load_devices()])

@app.route("/api/devices", methods=["POST"])
def r_add_device():
    d=request.json; devs=load_devices()
    if any(x.id==d["id"] for x in devs): return jsonify({"error":"ID đã tồn tại"}),400
    devs.append(Device(**d)); save_devices(devs); return jsonify({"ok":True})

@app.route("/api/devices/<dev_id>", methods=["DELETE"])
def r_del_device(dev_id):
    save_devices([d for d in load_devices() if d.id!=dev_id]); return jsonify({"ok":True})

@app.route("/api/devices/reset", methods=["POST"])
def r_reset_devices(): save_devices(list(DEFAULT_DEVICES)); return jsonify({"ok":True})

# ── Usage ─────────────────────────────────────────────────────
@app.route("/api/usage")
def r_usage(): return jsonify([e.to_dict() for e in load_usage()])

@app.route("/api/usage", methods=["POST"])
def r_save_usage():
    d=request.json; u=[e for e in load_usage() if not(e.date==d["date"] and e.device_id==d["device_id"])]
    if float(d.get("hours",0))>0: u.append(UsageEntry(d["device_id"],d["date"],float(d["hours"])))
    save_usage(u); return jsonify({"ok":True})

@app.route("/api/usage/<log_date>", methods=["DELETE"])
def r_del_day(log_date):
    save_usage([e for e in load_usage() if e.date!=log_date]); return jsonify({"ok":True})

# ── Config ────────────────────────────────────────────────────
@app.route("/api/config")
def r_config(): return jsonify(load_config().to_dict())

@app.route("/api/config", methods=["POST"])
def r_save_config():
    d=request.json; save_config(Config(float(d["daily_budget_kwh"]),float(d["electricity_rate"]),d["peak_hours"]))
    return jsonify({"ok":True})

# ── Stats ─────────────────────────────────────────────────────
@app.route("/api/stats")
def r_stats():
    devs=load_devices(); usage=load_usage(); cfg=load_config()
    dev_map={d.id:d for d in devs}; today=date.today()
    daily=[]
    for i in range(13,-1,-1):
        dd=(today-timedelta(days=i)).isoformat()
        kwh=sum(dev_map[e.device_id].kwh(e.hours) for e in usage if e.date==dd and e.device_id in dev_map)
        daily.append({"date":dd,"kwh":round(kwh,3),"cost":round(kwh*cfg.electricity_rate)})
    by_dev=[]
    for d in devs:
        h=sum(e.hours for e in usage if e.device_id==d.id)
        if h: kwh=round(d.kwh(h),2); by_dev.append({"name":d.name,"kwh":kwh,"hours":h,"cost":round(kwh*cfg.electricity_rate),"category":d.category})
    by_dev.sort(key=lambda x:-x["kwh"])
    dates_used=sorted(set(e.date for e in usage))
    total_kwh=sum(dev_map[e.device_id].kwh(e.hours) for e in usage if e.device_id in dev_map)
    avg=round(total_kwh/len(dates_used),3) if dates_used else 0
    today_kwh=sum(dev_map[e.device_id].kwh(e.hours) for e in usage if e.date==today.isoformat() and e.device_id in dev_map)
    return jsonify({"daily":daily,"by_device":by_dev,"avg_kwh":avg,"monthly_kwh":round(avg*30,1),
        "est_evn":round(calc_evn(avg*30)),"today_kwh":round(today_kwh,3),
        "budget":cfg.daily_budget_kwh,"budget_rem":round(max(0,cfg.daily_budget_kwh-today_kwh),3),
        "tips":smart_tips(devs,usage,cfg),"n_days":len(dates_used)})

# ── Optimize ──────────────────────────────────────────────────
@app.route("/api/optimize", methods=["POST"])
def r_optimize():
    budget=float(request.json.get("budget_kwh",2.0))
    devs=load_devices(); cfg=load_config()
    dp=dp_optimize(devs,budget); gr=greedy_optimize(devs,budget)
    for r in (dp,gr):
        r["daily_cost"]=round(r["total_kwh"]*cfg.electricity_rate)
        r["monthly_cost"]=round(r["total_kwh"]*30*cfg.electricity_rate)
    loa=Device("loa_d","Loa Bluetooth",200,3,1.0,"entertainment")
    dh =Device("dh_d", "Điều hòa nhỏ", 300,4,1.0,"cooling")
    ce_dp=dp_optimize([loa,dh],0.30); ce_gr=greedy_optimize([loa,dh],0.30)
    return jsonify({"dp":dp,"greedy":gr,"budget":budget,
        "counterexample":{"dp":ce_dp,"greedy":ce_gr,"dp_wins":ce_dp["total_comfort"]>ce_gr["total_comfort"]+1e-6}})

# ── Peak Schedule ─────────────────────────────────────────────
@app.route("/api/peak", methods=["POST"])
def r_peak():
    budget=float(request.json.get("budget_kwh",2.0))
    devs=load_devices(); cfg=load_config()
    dp=dp_optimize(devs,budget); peak_set=set(cfg.peak_hours)
    off=[h for h in range(24) if h not in peak_set]; pa=sorted(cfg.peak_hours)
    result={}
    for item in dp["schedule"]:
        did=item["device"]["id"]; left=item["hours"]; slots=[]
        pool=off if item["device"]["power_w"]>=500 else (off+pa)
        for h in pool:
            if left<1e-9: break
            used=min(1.0,left); slots.append({"start":h,"dur":used}); left-=used
        result[did]={**item,"slots":slots}
    return jsonify({"schedule":result,"peak_hours":cfg.peak_hours})

# ── Heatmap ───────────────────────────────────────────────────
@app.route("/api/heatmap")
def r_heatmap():
    devs=load_devices(); usage=load_usage()
    dev_map={d.id:d for d in devs}; today=date.today()
    days=[]
    for i in range(29,-1,-1):
        dd=(today-timedelta(days=i)).isoformat()
        kwh=sum(dev_map[e.device_id].kwh(e.hours) for e in usage if e.date==dd and e.device_id in dev_map)
        days.append({"date":dd,"kwh":round(kwh,3)})
    mx=max((d["kwh"] for d in days),default=1)
    return jsonify({"days":days,"max_kwh":round(mx,3)})

# ── Forecast ──────────────────────────────────────────────────
@app.route("/api/forecast")
def r_forecast():
    devs=load_devices(); usage=load_usage(); cfg=load_config()
    dev_map={d.id:d for d in devs}; dates_used=sorted(set(e.date for e in usage))
    if not dates_used: return jsonify({"months":[],"avg_daily_kwh":0,"saving":0})
    total=sum(dev_map[e.device_id].kwh(e.hours) for e in usage if e.device_id in dev_map)
    avg=total/len(dates_used); monthly=avg*30
    months=[{"label":f"Tháng +{i+1}","kwh":round(monthly,1),"evn":round(calc_evn(monthly))} for i in range(6)]
    dp=dp_optimize(devs,cfg.daily_budget_kwh); opt_monthly=dp["total_kwh"]*30
    return jsonify({"months":months,"avg_daily_kwh":round(avg,3),"monthly_kwh":round(monthly,1),
        "evn":round(calc_evn(monthly)),"opt_monthly_kwh":round(opt_monthly,1),
        "opt_evn":round(calc_evn(opt_monthly)),"saving":round(calc_evn(monthly)-calc_evn(opt_monthly))})

# ── EVN Calculator ────────────────────────────────────────────
@app.route("/api/evn", methods=["POST"])
def r_evn():
    kwh=float(request.json.get("kwh",0))
    tiers=[(50,1806),(50,1866),(100,2167),(100,2729),(100,3050),(9999,3151)]
    bk=[]; rem=kwh
    for i,(lim,rate) in enumerate(tiers):
        used=min(rem,lim)
        if used>0: bk.append({"bac":i+1,"kwh":round(used,2),"rate":rate,"cost":round(used*rate)})
        rem-=used
        if rem<=0: break
    return jsonify({"kwh":kwh,"total":round(calc_evn(kwh)),"breakdown":bk})

if __name__=="__main__":
    os.makedirs("templates",exist_ok=True)
    print("\n  🌐  http://localhost:5000\n")
    app.run(debug=False, host="0.0.0.0", port=5000)

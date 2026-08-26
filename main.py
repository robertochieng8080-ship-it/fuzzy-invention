import os, requests, math, time, json
from datetime import datetime, timezone, timedelta

try:
    BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID=os.getenv("TELEGRAM_CHANNEL_ID")
    EAT=timezone(timedelta(hours=3))
    TODAY=datetime.now(EAT)
    TOMORROW=TODAY+timedelta(days=1)
    YESTERDAY=TODAY-timedelta(days=1)

    STATS={
        "Arsenal": (2.39,0.76),"Man City": (2.53,0.89),"Liverpool": (2.26,1.08),"Chelsea": (2.03,1.63),
        "Man United": (1.85,1.45),"Tottenham": (2.10,1.55),"Newcastle": (1.95,1.20),
        "Real Madrid": (2.11,0.68),"Barcelona": (2.08,1.16),"Atletico": (1.75,0.85),
        "Bayern": (2.76,1.32),"Bayern Munich": (2.76,1.32),"Leverkusen": (2.35,0.71),"Dortmund": (2.20,1.30),
        "Inter": (2.32,0.58),"AC Milan": (1.85,1.10),"Napoli": (2.05,0.95),"Juventus": (1.65,0.75),
        "PSG": (2.26,0.85),"Marseille": (1.80,1.05),"PSV": (2.91,0.88),"Ajax": (2.40,1.20),
        "Benfica": (2.41,0.76),"Porto": (2.10,0.80),"Sporting": (2.30,0.90),
        "Stuttgart": (1.85,1.40),"VfB": (1.85,1.40)
    }
    def get_stats(name):
        n=name.lower()
        for k,v in STATS.items():
            if k.lower() in n or n in k.lower():
                return v
        return (1.35,1.35)

    def probs(eg1,eg2):
        lam=eg1+eg2
        p15=1-math.exp(-lam)*(1+lam)
        p25=1-math.exp(-lam)*(1+lam+lam*lam/2)
        btts=(1-math.exp(-eg1))*(1-math.exp(-eg2))
        return int(p15*100),int(p25*100),int(btts*100),lam

    def get_matches(code,d):
        try:
            ds=d.strftime("%Y%m%d")
            url="https://site.api.espn.com/apis/site/v2/sports/soccer/"+code+"/scoreboard?dates="+ds
            j=requests.get(url,timeout=15).json()
            return j.get("events",[])[:8]
        except:
            return []

    def get_score(ev):
        try:
            c=ev["competitions"][0]
            s0=int(c["competitors"][0].get("score","0"))
            s1=int(c["competitors"][1].get("score","0"))
            return s0+s1,s0>0 and s1>0
        except:
            return None,None

    def get_time(s):
        try:
            dt=datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(EAT)
            return dt.strftime("%d %b %H:%M")
        except:
            return ""

    LEAGUES={"EPL":"eng.1","LaLiga":"esp.1","Bundes":"ger.1","SerieA":"ita.1","Ligue1":"fra.1","Erediv":"ned.1","Portugal":"por.1","UCL":"uefa.champions"}

    yesterday_report=""
    try:
        with open("tips_history.json","r") as f:
            hist=json.load(f)
        wins=0
        total=0
        details=[]
        for tip in hist.get("tips",[])[:10]:
            for lcode in LEAGUES.values():
                for ev in get_matches(lcode,YESTERDAY):
                    try:
                        comp=ev["competitions"][0]
                        t1=comp["competitors"][0]["team"]["displayName"]
                        if tip["match"].split(" vs ")[0][:6].lower() in t1.lower():
                            tot,btts=get_score(ev)
                            if tot is None: continue
                            ok=False
                            if "Over 1.5" in tip["m"]: ok=tot>1.5
                            elif "Over 2.5" in tip["m"]: ok=tot>2.5
                            elif "BTTS" in tip["m"]: ok=btts
                            total+=1
                            if ok: wins+=1
                            details.append(tip["match"][:18]+" "+("✅" if ok else "❌"))
                            break
                    except: continue
        if total>0:
            yesterday_report="📊 <b>YESTERDAY "+str(wins)+"/"+str(total)+" WON</b>\n"+" | ".join(details[:5])+"\n\n"
    except:
        yesterday_report=""

    bets=[]
    for label,day in [("TODAY",TODAY),("TOMORROW",TOMORROW)]:
        for lname,lcode in LEAGUES.items():
            time.sleep(0.6)
            for ev in get_matches(lcode,day):
                try:
                    comp=ev["competitions"][0]
                    t1=comp["competitors"][0]["team"]["displayName"]
                    t2=comp["competitors"][1]["team"]["displayName"]
                    s1,c1=get_stats(t1)
                    s2,c2=get_stats(t2)
                    eg1=(s1+c2)/2
                    eg2=(s2+c1)/2
                    p15,p25,btts,xg=probs(eg1,eg2)

                    if p15>=85:
                        bets.append({"tier":"GOLD","day":label,"lg":lname,"match":t1+" vs "+t2,"time":get_time(ev.get("date","")),"m":"Over 1.5","pr":p15,"od":1.32,"xg":xg,"reason":t1+" "+str(s1)+" avg"})
                    elif p15>=75:
                        bets.append({"tier":"SILVER","day":label,"lg":lname,"match":t1+" vs "+t2,"time":get_time(ev.get("date","")),"m":"Over 1.5","pr":p15,"od":1.32,"xg":xg,"reason":"Safe Over "+str(round(xg,1))+" xG"})

                    if p25>=75:
                        bets.append({"tier":"SILVER","day":label,"lg":lname,"match":t1+" vs "+t2,"time":get_time(ev.get("date","")),"m":"Over 2.5","pr":p25,"od":1.85,"xg":xg,"reason":"xG "+str(round(xg,2))+" expected"})

                    if btts>=75:
                        bets.append({"tier":"SILVER","day":label,"lg":lname,"match":t1+" vs "+t2,"time":get_time(ev.get("date","")),"m":"BTTS","pr":btts,"od":1.90,"xg":xg,"reason":"Both score "+str(s1)+" vs "+str(s2)})

                except: continue

    bets.sort(key=lambda x:x["pr"],reverse=True)
    gold=[b for b in bets if b["tier"]=="GOLD"][:5]
    silver=[b for b in bets if b["tier"]=="SILVER"][:6]

    today_str=TODAY.strftime("%d %b")
    tom_str=TOMORROW.strftime("%d %b")
    msg="⚽ <b>PRO MAX - 80%+ TIPS</b>\n"+today_str+" + "+tom_str+" EAT\n\n"
    msg+=yesterday_report

    if gold:
        msg+="🥇 <b>GOLD 85%+ - SUPER SAFE</b>\n"
        for b in gold:
            msg+="<b>"+b["day"]+" "+b["lg"]+" | "+b["time"]+"</b>\n"+b["match"]+"\n"
            msg+=b["m"]+" "+str(b["pr"])+"% @ "+str(b["od"])+" | xG "+str(round(b["xg"],1))+"\n"
            msg+="<i>"+b["reason"]+"</i>\n\n"

    if silver:
        msg+="🥈 <b>SILVER 75%+ - VALUE</b>\n"
        for b in silver[:5]:
            msg+="<b>"+b["day"]+" "+b["lg"]+" | "+b["time"]+"</b>\n"+b["match"]+"\n"
            msg+=b["m"]+" "+str(b["pr"])+"% @ "+str(b["od"])+" | xG "+str(round(b["xg"],1))+"\n"
            msg+="<i>"+b["reason"]+"</i>\n\n"

    # ALWAYS SAFE ACCA - 4 picks = 3.03 odds
    if len(bets)>=3:
        safe_picks=bets[:4] if len(bets)>=4 else bets[:3]
        tot=1
        for p in safe_picks: tot*=p["od"]
        msg+="🔒 <b>SAFE ACCA "+str(round(tot,2))+" ODDS</b>\n"
        for p in safe_picks:
            msg+="• "+p["match"][:22]+" - "+p["m"]+" @ "+str(p["od"])+"\n"
        msg+="<b>Total "+str(round(tot,2))+" | 1000 -> "+str(int(tot*1000))+"</b>\n\n"

    # ALWAYS RISKY ACCA - try high odds first, else 6 picks
    if len(bets)>=3:
        high=[b for b in bets if b["od"]>=1.8]
        if len(high)>=3:
            risky_picks=high[:3]
        else:
            risky_picks=bets[:6] if len(bets)>=6 else bets[:5] if len(bets)>=5 else bets[:3]
        tot2=1
        for p in risky_picks: tot2*=p["od"]
        msg+="🔥 <b>RISKY ACCA "+str(round(tot2,2))+" ODDS</b>\n"
        for p in risky_picks:
            msg+="• "+p["match"][:22]+" - "+p["m"]+" @ "+str(p["od"])+"\n"
        msg+="<b>Total "+str(round(tot2,2))+" | 1000 -> "+str(int(tot2*1000))+"</b>\n\n"

    if not bets:
        msg+="No 75%+ tips - very quiet day\n\n"
    msg+="<i>Gold 85%+ | Silver 75%+ | Safe 3-4 | Risky 5-8 | xG | EAT | 18+</i>"

    try:
        with open("tips_history.json","w") as f:
            json.dump({"date": TODAY.strftime("%Y-%m-%d"), "tips": bets[:10]}, f)
    except: pass

    url="https://api.telegram.org/bot"+BOT_TOKEN+"/sendMessage"
    r=requests.post(url,json={"chat_id":CHAT_ID,"text":msg,"parse_mode":"HTML"},timeout=20)
    print("SENT: "+r.text[:300])

except Exception as e:
    print("ERROR "+str(e))
    import traceback; traceback.print_exc()

import os, requests, math, time
from datetime import datetime, timezone, timedelta

try:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHANNEL_ID")
    EAT = timezone(timedelta(hours=3))
    TODAY = datetime.now(EAT)
    TOMORROW = TODAY + timedelta(days=1)

    STATS = {
        "Arsenal": (2.39,0.76), "Man City": (2.53,0.89), "Liverpool": (2.26,1.08),
        "Chelsea": (2.03,1.63), "Real Madrid": (2.11,0.68), "Barcelona": (2.08,1.16),
        "Bayern": (2.76,1.32), "Bayern Munich": (2.76,1.32), "Leverkusen": (2.35,0.71),
        "Inter": (2.32,0.58), "PSG": (2.26,0.85), "PSV": (2.91,0.88), "Benfica": (2.41,0.76)
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
            return requests.get(url,timeout=15).json().get("events",[])[:5]
        except:
            return []

    def get_time(s):
        try:
            dt=datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(EAT)
            return dt.strftime("%d %b %H:%M")
        except:
            return ""

    LEAGUES={"EPL":"eng.1","LaLiga":"esp.1","Bundes":"ger.1","SerieA":"ita.1","Ligue1":"fra.1","Erediv":"ned.1","Portugal":"por.1","UCL":"uefa.champions"}
    MIN=80
    bets=[]

    today_str=TODAY.strftime("%d %b")
    tom_str=TOMORROW.strftime("%d %b")
    msg="⚽ <b>80%+ TIPS + 3-5 ODDS</b>\n"
    msg+=today_str+" + "+tom_str+" EAT\n\n"

    for label,day in [("TODAY",TODAY),("TOMORROW",TOMORROW)]:
        for lname,lcode in LEAGUES.items():
            time.sleep(0.8)
            for ev in get_matches(lcode,day):
                try:
                    comp=ev["competitions"][0]
                    t1=comp["competitors"][0]["team"]["displayName"]
                    t2=comp["competitors"][1]["team"]["displayName"]
                    s1,c1=get_stats(t1)
                    s2,c2=get_stats(t2)
                    eg1=(s1+c2)/2
                    eg2=(s2+c1)/2
                    p15,p25,bt,xg=probs(eg1,eg2)
                    market=None
                    if p25>=MIN:
                        market=("Over 2.5",p25,1.85)
                    elif bt>=MIN:
                        market=("BTTS",bt,1.90)
                    elif p15>=MIN:
                        market=("Over 1.5",p15,1.32)
                    if market:
                        m,pr,od=market
                        bets.append({"day":label,"lg":lname,"match":t1+" vs "+t2,"time":get_time(ev.get("date","")),"m":m,"pr":pr,"od":od})
                except:
                    continue

    bets.sort(key=lambda x:x["pr"],reverse=True)
    for b in bets[:10]:
        msg+="<b>"+b["day"]+" "+b["lg"]+" | "+b["time"]+" EAT</b>\n"
        msg+=b["match"]+"\n"
        msg+=b["m"]+" "+str(b["pr"])+"% @ "+str(b["od"])+"\n\n"

    if len(bets)>=2:
        acca=bets[:2]
        tot=acca[0]["od"]*acca[1]["od"]
        if tot<3.0 and len(bets)>=3:
            acca.append(bets[2])
            tot=tot*bets[2]["od"]
        if 3.0 <= tot <= 6.0:
            msg+="🔥 <b>ACCA "+str(round(tot,2))+" ODDS</b>\n"
            for a in acca:
                msg+="• "+a["match"][:25]+" - "+a["m"]+" @ "+str(a["od"])+"\n"
            msg+="<b>Total: "+str(round(tot,2))+" | 1000 -> "+str(int(tot*1000))+"</b>\n\n"

    if not bets:
        msg+="No 80%+ tips today/tomorrow - quiet day\n"
    msg+="<i>80%+ model | 3-5 odds | EAT | 18+</i>"

    url="https://api.telegram.org/bot"+BOT_TOKEN+"/sendMessage"
    r=requests.post(url,json={"chat_id":CHAT_ID,"text":msg,"parse_mode":"HTML"},timeout=15)
    print("SENT OK: "+r.text[:200])

except Exception as e:
    print("ERROR: "+str(e))
    import traceback
    traceback.print_exc()

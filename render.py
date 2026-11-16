import datetime as dt, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tracker as t
today=dt.date(2026,11,16)
rules,lic,par=t.read("reporting_rules.csv"),t.read("licenses.csv"),t.read("partners.csv")
dl=t.upcoming_deadlines(today,rules)
fig=plt.figure(figsize=(12,5.6),dpi=130); ax=fig.add_axes([0,0,1,1]); ax.axis("off")
fig.patch.set_facecolor("white")
y=0.93
ax.text(0.04,y,"Market data ops check",fontsize=20,weight="bold",color="#1f2937")
ax.text(0.04,y-0.055,f"{today:%A %d %B %Y}  ·  independent case study",fontsize=10.5,color="#6b7280")
def section(title,y):
    ax.text(0.04,y,title,fontsize=12.5,weight="bold",color="#111827")
    ax.plot([0.04,0.96],[y-0.02,y-0.02],color="#e5e7eb",lw=1)
    return y-0.065
y=section("Upcoming usage reporting deadlines",y-0.13)
for d,src,rep,per in dl:
    today_flag = d==today
    col="#b91c1c" if today_flag else "#111827"
    ax.text(0.05,y,f"{d:%a %d %b}" if d else "confirm",fontsize=10.5,color=col,weight="bold" if today_flag else "normal",family="DejaVu Sans Mono")
    ax.text(0.17,y,src,fontsize=10.5,color=col)
    ax.text(0.47,y,f"{rep} · {per}"+("   ← due today (Sun 15th rolls to Monday)" if today_flag else ""),fontsize=10,color=col if today_flag else "#374151")
    y-=0.047
y=section("Example alerts (made-up partners and licenses, to show how it works)",y-0.035)
for lid,src,prod,ren,notice,auto in t.renewal_alerts(today,lic):
    ax.text(0.05,y,"●",color="#d97706",fontsize=11); ax.text(0.07,y,f"{prod}: license ends {ren:%d %b} and does not auto-renew; renewal should have started by {notice:%d %b}" if auto=="no" else f"{prod}: auto-renews {ren:%d %b}; last day to give notice was {notice:%d %b}",fontsize=10.5,color="#111827"); y-=0.047
for name,exp,feeds,status in t.partner_alerts(today,par):
    c="#b91c1c" if status.startswith("EXPIRED") else "#d97706"
    ax.text(0.05,y,"●",color=c,fontsize=11); ax.text(0.07,y,f"{name}: redistribution authorization {('expired '+exp.strftime('%d %b')) if status.startswith('EXPIRED') else status}, feeds still on: {feeds.replace(';',', ')}",fontsize=10.5,color="#111827"); y-=0.047
ax.text(0.04,0.045,"Deadlines are real exchange rules applied to the real calendar. The alerts use made-up data. Rules summarized from public policies; always confirm with current documents.",fontsize=8.5,color="#6b7280",wrap=True)
ax.set_xlim(0,1); ax.set_ylim(0,1)
t.OUT.mkdir(exist_ok=True)
fig.savefig(t.OUT / "ops_check.png",facecolor="white")

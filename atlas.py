# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy", "pillow"]
# ///

"""A standalone, directly clickable eclipse artwork. Run: uv run atlas.py.

No browser or server. Use --snapshot out/lunar-atlas.png for a headless still.
"""

import argparse
import datetime as dt
import math
from pathlib import Path
import time

import numpy as np
import matplotlib

from build import read_catalogue
from eclipse_model import Playback, TYPES, clock, contacts, phase, shadow, time_at, phase_intervals, milestones
from eclipse_model import totality_context, phase_explanation

W, H = 1600, 900
CX, CY = 690, 454
YEAR_R, PHASE_R, MOON_R = 316, 211, 109
BLUE, INK, WHITE = "#4357e4", "#151a29", "#e5e9f2"
NODE_POSITIONS = [(1120, 729), (1380, 729), (1120, 646), (1380, 646), (1120, 563)]
PHASE_COLORS = {"penumbra": "#8492b1", "partial": BLUE, "totality": "#bd624a"}
PHASE_NAMES = {"P1": "Penumbral begins", "U1": "Partial begins", "U2": "Totality begins",
               "MAX": "Greatest eclipse", "U3": "Totality ends", "U4": "Partial ends", "P4": "Eclipse ends"}


def polar(radius, angle):
    angle = math.radians(angle)
    return CX + radius * math.cos(angle), CY + radius * math.sin(angle)


def year_position(year):
    return polar(YEAR_R, 90 - (year - 2001) * 3.6)


def year_at(x, y):
    angle = (90 - math.degrees(math.atan2(y - CY, x - CX))) % 360
    return 2001 + int(math.floor(angle / 3.6 + .5)) % 100


def phase_position(progress):
    return polar(PHASE_R, 140 - 280 * progress)


def progress_at(x, y):
    angle = math.degrees(math.atan2(y - CY, x - CX))
    return max(0, min(1, (140 - angle) / 280))


def on_dark(x, y):
    return math.hypot(x + 106, y - 454) < 803


def foreground(x, y):
    return WHITE if on_dark(x, y) else INK


def lunar_terrain(size=300):
    """Deterministic, generated terrain; not a map or photographic asset."""
    from PIL import Image
    rng = np.random.default_rng(5913)
    axis = (np.arange(size) + .5) / size * 2 - 1
    x, y = np.meshgrid(axis, axis)
    radius = np.sqrt(x*x + y*y)
    noise = np.zeros((size, size))
    weight = 0
    for n in [5, 11, 23, 47, 97, 193]:
        values = Image.fromarray((rng.random((n, n)) * 255).astype(np.uint8))
        scale = (5 / n) ** .62
        noise += np.asarray(values.resize((size, size), Image.Resampling.BICUBIC)) / 255 * scale
        weight += scale
    base = 156 + 92 * noise / weight
    for sx, sy, sr in [(-.34,-.3,.28),(-.04,-.45,.22),(.2,-.28,.25),(.42,-.03,.19),(-.48,.13,.26),(-.12,.07,.17)]:
        base -= 57 * np.exp(-((x-sx)**2 + (y-sy)**2) / sr**2) * (.65 + noise/weight)
    for _ in range(110):
        sx, sy = rng.uniform(-.95, .95, 2)
        r = .006 + rng.random()**3 * .10
        d = np.sqrt((x-sx)**2 + (y-sy)**2) / r
        base += -20*np.exp(-d*d*3) + 28*np.exp(-((d-.94)/.13)**2)
    base *= .55 + .45*np.sqrt(np.maximum(0, 1-radius**2))
    alpha = np.clip((1-radius)*size, 0, 1)
    return x, y, base, alpha


class LunarAtlas:
    def __init__(self, *, interactive=True, year=2026):
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle, Rectangle, Arc
        self.plt, self.Circle, self.Rectangle, self.Arc = plt, Circle, Rectangle, Arc
        self.state = Playback(read_catalogue(), year)
        self.interactive = interactive
        self.dragging = None
        self.hover = ""
        self.info_visible = False
        self.focus_index = -1
        self.last_tick = time.monotonic()
        self.terrain = lunar_terrain()
        self.dynamic = []
        self.regions = []
        plt.rcParams["toolbar"] = "None"
        self.fig = plt.figure(figsize=(16, 9), facecolor="#eeeff1")
        handler = getattr(self.fig.canvas.manager, "key_press_handler_id", None)
        if handler is not None:
            self.fig.canvas.mpl_disconnect(handler)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.fig.canvas.manager.set_window_title("Lunar Passage — Interactive Eclipse Instrument")
        self.background_art()
        self.build_scene()
        self.connections = [
            self.fig.canvas.mpl_connect("button_press_event", self.on_click),
            self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion),
            self.fig.canvas.mpl_connect("button_release_event", self.on_release),
            self.fig.canvas.mpl_connect("key_press_event", self.on_key),
            self.fig.canvas.mpl_connect("resize_event", self.on_resize),
            self.fig.canvas.mpl_connect("close_event", self.on_close),
        ]
        if interactive:
            self.timer = self.fig.canvas.new_timer(interval=50)
            self.timer.add_callback(self.tick)
            self.timer.start()

    def text(self, x, y, value, size=9, color=None, align="left", **kw):
        family = kw.pop("fontfamily", "DejaVu Sans Mono")
        return self.ax.text(x, y, value, fontsize=size, color=color or foreground(x,y),
                            ha=align, va="center", fontfamily=family, **kw)

    def line(self, xs, ys, color=BLUE, alpha=1, width=.65, **kw):
        return self.ax.plot(xs, ys, color=color, alpha=alpha, lw=width, **kw)[0]

    def circle(self, x, y, r, color=BLUE, lw=.7, fill="none", **kw):
        patch = self.Circle((x, y), r, edgecolor=color, facecolor=fill, linewidth=lw, **kw)
        self.ax.add_patch(patch)
        return patch

    def background_art(self):
        self.ax.set(xlim=(0,W), ylim=(0,H), aspect="equal")
        self.ax.set_axis_off()
        # The curved black / white divide is part of the artwork, not a panel.
        rng = np.random.default_rng(404)
        x,y = np.meshgrid(np.linspace(0,W,1600), np.linspace(0,H,900))
        distance = np.sqrt((x+106)**2+(y-454)**2)
        dark = 1 / (1 + np.exp(np.clip((distance-803)/2, -50, 50)))
        grain = rng.normal(0,.003,(900,1600))
        rim = np.exp(-((distance-806)/19)**2)
        base = np.empty((900,1600,3))
        for i,(light,night,tint) in enumerate(zip([.94,.946,.953],[.026,.035,.051],[.14,.23,.85])):
            base[:,:,i] = light*(1-dark) + night*dark + grain + rim*tint*.38
        self.ax.imshow(np.clip(base,0,1), origin="lower", extent=(0,W,0,H), zorder=0)
        for _ in range(190):
            px,py = rng.uniform(28,W-28), rng.uniform(45,H-45)
            self.circle(px,py,rng.uniform(.25,.85),color="none",fill=foreground(px,py),alpha=rng.uniform(.1,.42),zorder=1)
        for i in range(18):
            radius=790+i*2.8
            self.ax.add_patch(self.Arc((-106,454),radius*2,radius*2,theta1=-48+i*.3,theta2=51-i*.9,
                             edgecolor=BLUE,lw=.25 if i%4 else .85,alpha=.14+(i%5)*.05,zorder=2))
        for radius in [148,158,244,252,298,334]:
            self.circle(CX,CY,radius,color="#6375ad",alpha=.15,lw=.5,zorder=2)
        for angle in [0,30,60,90,120,150]:
            p=polar(350,angle);q=polar(350,angle+180)
            self.line([p[0],q[0]],[p[1],q[1]],"#7085b9",.12,.4,zorder=2)
        self.line([365,1040],[CY,CY],"#7085b9",.30,.65,zorder=2)
        self.line([CX,CX],[92,817],"#6e80b4",.25,.5,zorder=2)
        self.text(58,851,"L / P     CELESTIAL MOTION STUDIES",9,color="#c3cbdc")
        self.text(1540,851,"01 — INTERACTIVE INSTRUMENT",8,align="right")
        self.text(62,741,"LUNAR",36,color="#f1f2f5",fontfamily="DejaVu Serif")
        self.text(62,692,"PASSAGE",36,color="#f1f2f5",fontfamily="DejaVu Serif")
        self.text(65,635,"How long does totality last?",10.5,color="#d1dcf2")
        self.text(65,611,"EXPLORE THE MOON IN EARTH’S SHADOW",8,color="#a4b6d9")
        self.text(690,851,"01 / CHOOSE A YEAR",10,color="#354769",align="center")
        self.text(690,828,"OUTER RING · 2001–2100 · CLICK OR DRAG",7.5,color="#354769",align="center",
                  bbox={"facecolor":"#edf0f8","edgecolor":"none","pad":3,"alpha":.9})
        self.text(65,51,"CLICK THE MOON TO PLAY / PAUSE",7,color="#a9b5d1")
        self.text(65,33,"ARROWS: YEAR    [ ]: EVENT    SPACE: PLAY    I: NOTES",6.4,color="#7989ad")
        self.text(1090,43,"~ CONTACT TIMES ARE ESTIMATES · ARTISTIC MOON",7,color="#52627e")
        self.text(1090,26,"DATA: F. ESPENAK & J. MEEUS / NASA GSFC",7,color="#52627e")

    def register(self, x, y, radius, action, label):
        self.regions.append((x,y,radius,action,label))

    def build_scene(self):
        for artist in self.dynamic:
            artist.remove()
        self.dynamic=[]
        self.regions=[]
        self.phase_rows=[]
        before=set(self.ax.get_children())
        s=self.state
        # Every tick is selectable; full-circle nearest-point hit testing supports dragging.
        for year in range(2001,2101):
            angle=90-(year-2001)*3.6
            x,y=polar(YEAR_R,angle)
            inner=polar(YEAR_R-(9 if year%5==0 else 4),angle)
            self.line([inner[0],x],[inner[1],y],foreground(x,y),.65 if year%5==0 else .32,.65,zorder=5)
            separation=min(abs(year-s.year),100-abs(year-s.year))
            if (year%10==0 and year!=2100 or year==2001) and separation>3:
                lx,ly=polar(YEAR_R+22,angle)
                self.text(lx,ly,str(year),7,align="center",alpha=.8,zorder=6)
        x,y=year_position(s.year)
        self.circle(x,y,10,BLUE,1.1,fill="#eef0f8",zorder=7)
        self.circle(x,y,4,color=BLUE,fill=BLUE,zorder=8)
        lx,ly=polar(YEAR_R+34,90-(s.year-2001)*3.6)
        self.text(lx,ly,str(s.year),10,color=BLUE,align="center",weight="bold",zorder=9,
                  bbox={"facecolor":"#edf0fa","edgecolor":"none","pad":3})

        self.text(65,208,"SELECTED YEAR",9,color="#b3c4e3",zorder=5)
        self.text(62,170,str(s.year),45,color="#f4f5fa",zorder=5)
        self.text(65,122,f"{len(s.events)} eclipses · {sum(e['type']=='T' for e in s.events)} total",9.5,color="#c0cee7",zorder=5)
        for x,delta,label in [(265,-1,"−"),(311,1,"+")]:
            self.circle(x,171,17,"#64769f",.7,zorder=5)
            self.text(x,171,label,14,color="#c2cce1",align="center",zorder=6)
            self.register(x,171,21,("year",delta),"Previous year" if delta<0 else "Next year")

        for i,event in enumerate(s.events):
            x,y=NODE_POSITIONS[i]
            active=i==s.index
            self.line([CX,x],[CY,y],BLUE,.28 if active else .09,.75 if active else .5,zorder=3)
            self.circle(x,y,24,BLUE if active else "#8a95b2",1 if active else .65,fill="#e7eaf5" if active else "#eff0f3",zorder=6)
            self.ax.imshow(self.moon_image(event,.5),extent=(x-19,x+19,y-19,y+19),zorder=7)
            self.ax.add_patch(self.Rectangle((x-29,y-29),58,58,fill=False,edgecolor=BLUE if active else "#a7afc1",lw=1.1 if active else .65,zorder=6))
            self.text(x+40,y+19,event["date"],11,color=BLUE if active else "#273047",zorder=7)
            self.text(x+40,y-2,{"T":"Total eclipse","P":"Partial eclipse","N":"Penumbral eclipse"}[event["type"]],9.5,color="#354868",zorder=7)
            duration=f"Totality {event['totalMinutes']:.1f} min" if event["totalMinutes"] is not None else "No totality"
            self.text(x+40,y-22,duration,8.5,color=BLUE if active else "#435778",zorder=7)
            self.register(x+52,y,39,("event",i),f"Select {event['date']} — {TYPES[event['type']]}")
            self.register(x,y,30,("event",i),f"Select {event['date']} — {TYPES[event['type']]}")
        self.text(1090,798,f"02 / {s.year} ECLIPSES",11,color=INK,zorder=7)
        self.text(1090,776,"CLICK A MOON NODE · BLUE FRAME = SELECTED",7.5,color="#506382",zorder=7)
        self.draw_duration_context()

        # Contact points live on the inner trajectory, with a continuous scrub arc.
        for begin,end,kind in phase_intervals(s.event):
            self.ax.add_patch(self.Arc((CX,CY),PHASE_R*2,PHASE_R*2,theta1=140-280*end,theta2=140-280*begin,
                             color=PHASE_COLORS[kind],lw=3.1,alpha=.9,zorder=4))
        self.text(65,566,"03 / ECLIPSE PHASES",11,color=WHITE,zorder=7)
        basis="UT+8" if s.offset else "UT"
        self.text(65,543,f"{basis} · ~ ESTIMATE · CLICK TO SEEK",8.2,color="#bac9e5",zorder=7)
        self.text(65,526,"HIGHLIGHT = LAST MILESTONE REACHED",6.7,color="#bac9e5",zorder=7)
        start=time_at(s.event,0)
        self.contact_points=[]
        for code,label,instant in contacts(s.event):
            progress=(instant-start)/(s.event["penumbralMinutes"]*60000)
            x,y=phase_position(progress)
            self.circle(x,y,5,BLUE,.9,fill=foreground(x,y),zorder=7)
            # Alternating radii make close contacts legible even for brief totality.
            index=len(self.contact_points)
            lx,ly=polar(PHASE_R+(25 if index%2==0 else 47),140-280*progress)
            self.line([x,lx],[y,ly],BLUE,.5,.5,zorder=5)
            self.text(lx,ly,code,7.5,color=foreground(lx,ly),align="center",zorder=8)
            local=dt.datetime.fromtimestamp(instant/1000,dt.timezone.utc)+dt.timedelta(hours=s.offset)
            self.register(x,y,12,("seek",progress),f"{label} · {local:%Y-%m-%d %H:%M:%S}"+("" if code=="MAX" else " (estimated)"))
            self.contact_points.append((x,y,progress,code))
            row_y=509-index*34
            row=self.Rectangle((58,row_y-16),297,32,facecolor="#233761",edgecolor="none",alpha=0,zorder=4)
            self.ax.add_patch(row)
            row_text=[self.text(67,row_y,code,8.5,color="#b6c6ea",zorder=7),
                      self.text(101,row_y,PHASE_NAMES[code],9.5,color=WHITE,zorder=7),
                      self.text(347,row_y+4,("" if code=="MAX" else "~")+local.strftime("%H:%M"),11,color=WHITE,align="right",zorder=7),
                      self.text(347,row_y-11,local.strftime("%d %b").upper(),7,color="#a7b7d7",align="right",zorder=7)]
            self.phase_rows.append((code,row,row_text))
            self.register(195,row_y,15,("seek",progress),f"{label} · {local:%d %b %H:%M}")

        for index,(kind,label) in enumerate([("penumbra","Penumbral: faint shadow"),("partial","Partial: partly in dark shadow"),("totality","Totality: fully in dark shadow")]):
            ly=275-index*19
            self.line([65,82],[ly,ly],PHASE_COLORS[kind],1,3,zorder=7)
            self.text(93,ly,label,8,color="#b9cae9",zorder=7)

        self.circle(CX,CY,MOON_R+7,"#5367c3",.6,alpha=.8,zorder=5)
        self.circle(CX,CY,MOON_R+13,"#5266b2",.5,alpha=.3,zorder=5)
        self.moon=self.ax.imshow(self.moon_image(s.event,s.progress),extent=(CX-MOON_R,CX+MOON_R,CY-MOON_R,CY+MOON_R),zorder=10)
        self.register(CX,CY,MOON_R,("play",None),"Click the Moon to pause / resume · Space")
        self.play_label=self.text(CX,CY-143,"",8,color=BLUE,align="center",zorder=8,
                                  bbox={"facecolor":"#e9edf7","edgecolor":"none","pad":3})
        self.text(CX,CY-166,f"ACCELERATED · {60/s.speed:g}s PER FULL EVENT",7,color="#435b7f",align="center",zorder=8,
                  bbox={"facecolor":"#e9edf7","edgecolor":"none","pad":2})
        self.phase_label=self.text(CX,CY+155,"",12,color=BLUE,align="center",zorder=8,
                                   bbox={"facecolor":"#e9edf7","edgecolor":"none","pad":3})
        self.phase_explanation_label=self.text(CX,CY+131,"",8.2,color="#314875",align="center",zorder=8,
                                               bbox={"facecolor":"#e9edf7","edgecolor":"none","pad":3})
        px,py=phase_position(s.progress)
        self.playhead=self.circle(px,py,8,BLUE,1.2,fill="#edf0fa",zorder=9)
        self.playhead_dot=self.circle(px,py,3,BLUE,.5,fill=BLUE,zorder=10)
        for x,y,action,label in [(510,500,"replay","R"),(487,454,"speed",f"{s.speed}×"),(510,408,"zone","TZ")]:
            self.circle(x,y,17,"#7788bb",.7,fill="#e8ecf6",zorder=8)
            self.text(x,y,label,8,color="#304679",align="center",zorder=9)
            self.register(x,y,21,(action,None),{"replay":"Replay from the beginning · R","speed":"Cycle speed: 1× / 2× / 4× · S","zone":"Switch UT / approximate Hong Kong time · T"}[action])
            self.text(x-25,y,{"replay":"REPLAY","speed":"SPEED","zone":"TIME ZONE"}[action],6.7,color="#b1c2e7",align="right",zorder=8)

        self.ax.add_patch(self.Rectangle((1075,192),480,424,facecolor="#f0f1f3",edgecolor="none",zorder=5))
        self.text(1090,601,TYPES[s.event["type"]],14,color=INK,zorder=7)
        self.text(1090,570,"TOTALITY · FULL DARK SHADOW",8.5,color="#8e4939",zorder=7)
        self.text(1350,570,"FULL EVENT · ALL STAGES",8,color="#354b70",zorder=7)
        duration=f"{s.event['totalMinutes']:.1f} min" if s.event["totalMinutes"] is not None else "None"
        self.text(1088,535,duration,29,color="#a24d37",zorder=7)
        self.text(1348,535,f"{s.event['penumbralMinutes']:.1f} min",20,color=INK,zorder=7)
        self.line([1090,1540],[505,505],"#9aa9c2",.6,.65,zorder=7)
        self.text(1090,485,"04 / ANIMATION TIME",9,color="#354b70",zorder=7)
        self.zone_label=self.text(1090,464,"",8.5,color="#354b70",zorder=7)
        self.clock_label=self.text(1087,429,"",27,color=INK,zorder=7)
        self.date_label=self.text(1360,429,"",11,color="#354968",zorder=7)
        self.text(1090,389,"EVENT TIMELINE · CLICK OR DRAG TO SEEK",8.3,color="#354b70",zorder=7)
        for begin,end,kind in phase_intervals(s.event):
            self.ax.add_patch(self.Rectangle((1090+450*begin,367),450*(end-begin),10,facecolor=PHASE_COLORS[kind],edgecolor="none",zorder=7))
        self.time_marker=self.line([1090,1090],[363,382],INK,1,1.5,zorder=9)
        for progress,align in [(0,"left"),(.5,"center"),(1,"right")]:
            instant=clock(s.event,progress,s.offset)
            self.text(1090+450*progress,348,("" if progress==.5 else "~")+instant.strftime("%H:%M"),9,color="#273d61",align=align,zorder=7)
            self.text(1090+450*progress,330,instant.strftime("%d %b").upper(),8,color="#435878",align=align,zorder=7)
            self.text(1090+450*progress,313,{0:"BEGIN",.5:"DEEPEST",1:"END"}[progress],8,color="#435878",align=align,zorder=7)
        self.elapsed_label=self.text(1090,285,"",9,color="#3d5479",zorder=7)
        self.next_label=self.text(1090,249,"",10,color=INK,zorder=7)
        self.next_time_label=self.text(1090,226,"",9,color="#435b7f",zorder=7)
        for x,action,label in [(1488,"fullscreen","F"),(1540,"info","i")]:
            self.circle(x,48,15,"#8a94ab",.7,zorder=5)
            self.text(x,48,label,9,color="#334a81",align="center",zorder=6)
            self.register(x,48,19,(action,None),"Toggle fullscreen · F" if action=="fullscreen" else "Data and controls · I")
        self.hint_label=self.text(CX,76,self.hover or "OUTER RING: YEAR   /   INNER ARC: TIME",6.8,color="#415a9d",align="center",zorder=9,
                                 bbox={"facecolor":"#eef0f6","edgecolor":"none","pad":4})
        self.focus_halo=self.circle(-100,-100,17,BLUE,1.8,zorder=15)
        if self.info_visible:
            self.draw_notes()
        self.dynamic=[artist for artist in self.ax.get_children() if artist not in before]
        self.update_frame()

    def draw_duration_context(self):
        context=totality_context(self.state.records,self.state.event)
        self.ax.add_patch(self.Rectangle((1075,91),480,108,facecolor="#f0f1f3",edgecolor="none",zorder=5))
        self.text(1090,181,f"2001–2100 / {context['count']} TOTAL ECLIPSES",8.8,color="#344c72",zorder=7)
        x=lambda minutes:1090+450*minutes/110
        self.line([x(0),x(110)],[148,148],"#b2bdcf",.8,.7,zorder=6)
        for i,minutes in enumerate(context["durations"]):
            self.circle(x(minutes),148+((i%5)-2)*3.1,1.7,"none",fill="#6b7c99",alpha=.85,zorder=7)
        self.line([x(context["median"])]*2,[136,160],"#344c72",.8,.85,zorder=7)
        self.text(x(context["median"]),167,f"Median {context['median']:.1f} min",7.5,color="#344c72",align="center",zorder=7)
        self.text(x(0),124,"0 min",7.6,color="#4e6484",zorder=7)
        self.text(x(55),124,"1 DOT = 1 TOTAL ECLIPSE",7.2,color="#4e6484",align="center",zorder=7)
        self.text(x(110),124,"110 min",7.6,color="#4e6484",align="right",zorder=7)
        if context["selected"] is not None:
            self.circle(x(context["selected"]),148,5,"#a24d37",.9,fill="#bd624a",zorder=8)
            difference=context["difference"]
            description=f"Selected: {context['selected']:.1f} min · {abs(difference):.1f} {'above' if difference>0 else 'below'} median" if abs(difference)>.05 else f"Selected: {context['selected']:.1f} min · matches the median"
        else:
            description="No total phase — not included in this comparison."
        self.text(1090,102,description,8.5,color="#8c4534" if context["selected"] is not None else "#435b7e",zorder=7)

    def moon_image(self,event,progress):
        x,y,base,alpha=self.terrain
        sx,sy,r,pr=shadow(event,progress)
        distance=np.sqrt((x-sx)**2+(y-sy)**2)
        pen=np.clip((pr-distance)/(pr-r),0,1)
        u=np.clip((r-distance)/.10+.5,0,1)
        u=u*u*(3-2*u)
        depth=np.clip((r-distance)/1.7,0,1)
        result=np.empty((*base.shape,4))
        red=base*(.70-.30*depth)+10
        green=base*(.28-.15*depth)+4
        blue=base*(.18-.07*depth)+7
        for i,(value,tint) in enumerate(zip([red,green,blue],[0,2,8])):
            result[:,:,i]=np.clip(((base*(1-.24*pen)+tint)*(1-u)+value*u)/255,0,1)
        result[:,:,3]=alpha
        return result

    def update_frame(self):
        s=self.state
        self.moon.set_data(self.moon_image(s.event,s.progress))
        instant=clock(s.event,s.progress,s.offset)
        self.date_label.set_text(instant.strftime("%d %b %Y").upper())
        self.clock_label.set_text(instant.strftime("%H:%M:%S"))
        self.zone_label.set_text("HONG KONG · UT+8 (APPROX.)" if s.offset else "UNIVERSAL TIME · UT")
        self.phase_label.set_text(phase(s.event,s.progress))
        self.phase_explanation_label.set_text(phase_explanation(s.event,s.progress))
        self.play_label.set_text(("II PAUSE" if s.playing else "> REPLAY" if s.progress>=1 else "> PLAY")+f"  /  PLAYBACK {s.progress:.0%}")
        self.time_marker.set_xdata([1090+450*s.progress]*2)
        self.elapsed_label.set_text(f"ELAPSED {s.progress*s.event['penumbralMinutes']:.1f} / {s.event['penumbralMinutes']:.1f} min")
        reached,upcoming=milestones(s.event,s.progress)
        for code,row,texts in self.phase_rows:
            active=code==reached[0]
            row.set_alpha(.95 if active else 0)
            for text in texts: text.set_color("#ffffff" if active else "#becce5")
        if upcoming:
            code,label,instant=upcoming
            local=dt.datetime.fromtimestamp(instant/1000,dt.timezone.utc)+dt.timedelta(hours=s.offset)
            remaining=max(0,(instant-time_at(s.event,s.progress))/60000)
            self.next_label.set_text("NEXT / "+PHASE_NAMES[code])
            self.next_time_label.set_text(("" if code=="MAX" else "~")+local.strftime("%d %b %H:%M")+f"  ·  IN {remaining:.1f} min")
        else:
            self.next_label.set_text("END / Eclipse complete")
            self.next_time_label.set_text("Click the Moon to replay this event.")
        position=phase_position(s.progress)
        self.playhead.center=position
        self.playhead_dot.center=position
        self.fig.canvas.draw_idle()

    def hit(self,x,y):
        if self.info_visible:
            return ("info",None),"Close notes · I / Escape"
        for i,(nx,ny) in enumerate(NODE_POSITIONS[:len(self.state.events)]):
            if nx-30<=x<=min(nx+224,1585) and ny-30<=y<=ny+30:
                return ("event",i),f"Select {self.state.events[i]['date']}"
        if CX-115<=x<=CX+115 and CY-156<=y<=CY-130:
            return ("play",None),"Play / pause · Space"
        if 1090<=x<=1540 and 357<=y<=387:
            return ("timeline",(x-1090)/450),"Drag to seek through the full event"
        if 58<=x<=355:
            for index,(code,_,instant) in enumerate(contacts(self.state.event)):
                if abs(y-(509-index*34))<=15:
                    progress=(instant-time_at(self.state.event,0))/(self.state.event["penumbralMinutes"]*60000)
                    return ("seek",progress),"Jump to "+PHASE_NAMES[code]
        for hx,hy,r,action,label in reversed(self.regions):
            if math.hypot(x-hx,y-hy)<=r:
                return action,label
        if abs(math.hypot(x-CX,y-CY)-YEAR_R)<=17:
            year=year_at(x,y)
            return ("select_year",year),f"Select {year} · drag around the year ring"
        if abs(math.hypot(x-CX,y-CY)-PHASE_R)<=12 and abs(math.degrees(math.atan2(y-CY,x-CX)))<=145:
            return ("seek",progress_at(x,y)),"Drag along this arc to explore eclipse time"
        return None,""

    def act(self,action):
        name,value=action
        s=self.state
        if name=="year": s.select_year(s.year+value)
        elif name=="select_year": s.select_year(value)
        elif name=="event": s.select_event(value)
        elif name in ["seek","timeline"]: s.seek(value)
        elif name=="play": s.toggle()
        elif name=="replay": s.replay()
        elif name=="speed": s.speed={1:2,2:4,4:1}[s.speed]
        elif name=="zone": s.offset=0 if s.offset else 8
        elif name=="fullscreen": self.fig.canvas.manager.full_screen_toggle()
        elif name=="info":
            self.info_visible=not self.info_visible
            if self.info_visible: s.playing=False
        self.last_tick=time.monotonic()
        self.focus_index=-1
        if name in ["play","seek","timeline","replay"]:
            self.update_frame()
        else:
            self.build_scene()

    def on_click(self,event):
        if event.inaxes is not self.ax or event.xdata is None or event.button!=1:
            return
        action,_=self.hit(event.xdata,event.ydata)
        if action:
            self.dragging="year" if action[0]=="select_year" else "time" if action[0]=="seek" else "timeline" if action[0]=="timeline" else None
            self.act(action)

    def on_motion(self,event):
        if event.inaxes is not self.ax or event.xdata is None:
            return
        x,y=event.xdata,event.ydata
        if self.dragging=="year":
            selected=year_at(x,y)
            if selected!=self.state.year: self.act(("select_year",selected))
        elif self.dragging=="time":
            self.state.seek(progress_at(x,y)); self.update_frame()
        elif self.dragging=="timeline":
            self.state.seek((x-1090)/450); self.update_frame()
        action,label=self.hit(x,y)
        if label!=self.hover:
            self.hover=label
            self.hint_label.set_text(label or "OUTER RING: YEAR   /   INNER ARC: TIME")
            self.fig.canvas.draw_idle()
        if self.interactive:
            from matplotlib.backend_tools import Cursors
            self.fig.canvas.set_cursor(Cursors.HAND if action else Cursors.POINTER)

    def on_release(self,event):
        self.dragging=None

    def on_key(self,event):
        key=event.key
        actions={" ":("play",None),"left":("year",-1),"right":("year",1),
                 "[":("event",self.state.index-1),"]":("event",self.state.index+1),
                 "r":("replay",None),"s":("speed",None),"t":("zone",None),
                 "i":("info",None),"f":("fullscreen",None),
                 "up":("seek",self.state.progress+.01),"down":("seek",self.state.progress-.01)}
        if self.info_visible and key not in ["i","escape"]:
            return
        if key=="escape" and self.info_visible: self.act(("info",None))
        elif key=="tab":
            self.focus_index=(self.focus_index+1)%len(self.regions)
            x,y,r,_,label=self.regions[self.focus_index]
            self.focus_halo.center=(x,y);self.focus_halo.set_radius(min(r+5,115))
            self.hint_label.set_text(label+" · Enter to activate")
            self.fig.canvas.draw_idle()
        elif key=="enter" and self.focus_index>=0:
            self.act(self.regions[self.focus_index][3])
        elif key in actions:
            self.act(actions[key])

    def on_resize(self,event):
        self.fig.canvas.draw_idle()

    def on_close(self,event):
        if hasattr(self,"timer"): self.timer.stop()

    def tick(self):
        now=time.monotonic()
        elapsed=min(now-self.last_tick,.25)
        self.last_tick=now
        if self.state.playing and not self.info_visible:
            self.state.advance(elapsed)
            self.update_frame()

    def draw_notes(self):
        self.ax.add_patch(self.Rectangle((350,174),900,570,facecolor="#edf0f8",edgecolor=BLUE,lw=.9,zorder=30))
        self.text(397,697,"READING THE INSTRUMENT",16,color=INK,zorder=31)
        self.text(1200,697,"[ × ]",14,color=BLUE,align="right",zorder=31)
        notes=[
            "OUTER RING    Click or drag to select a year, 2001–2100.",
            "EVENT NODES   Click a connected Moon to select an eclipse.",
            "CENTRAL MOON  Click to pause / resume. Space works too.",
            "INNER ARC     Click a phase marker, or drag to seek.",
            "R / S / T     Replay, cycle speed, switch the time basis.",
            "ARROW KEYS    Left/right: year. Up/down: seek. [ ]: event.",
            "TAB / ENTER   Focus a control, then activate it. F: fullscreen.",
            "",
            "DATA          228 eclipses from NASA’s cached 2001–2100 catalogue.",
            "TIME          Greatest UT = catalogue TD minus the row’s delta T.",
            "              Other contacts (~) use symmetric half-duration estimates.",
            "              Hong Kong time is approximate UT+8, not local visibility.",
            "MODEL         Artistic surface, colour and motion; not an ephemeris.",
            "              Instrument rings encode year and playback, not sky angles.",
            "PLAYBACK      60 seconds per eclipse at 1×. Future times are predictions.",
            f"SELECTED      Saros {self.state.event['saros']} / umbral magnitude {self.state.event['umbralMagnitude']:.4f}.",
            "Eclipse Predictions by Fred Espenak and Jean Meeus (NASA’s GSFC)",
        ]
        for i,line in enumerate(notes):
            self.text(399,650-i*24,line,8.5,color="#34425f",zorder=31)
        self.text(399,200,"CLICK ANYWHERE TO CLOSE  /  I OR ESCAPE",7.5,color=BLUE,zorder=31)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot",type=Path,help="Render a still without opening a window")
    parser.add_argument("--year",type=int,default=2026,choices=range(2001,2101),metavar="2001–2100")
    parser.add_argument("--paused",action="store_true",help="Start without automatic animation")
    args=parser.parse_args()
    if args.snapshot:
        matplotlib.use("Agg")
    from poster import LunarPoster
    app=LunarPoster(interactive=not args.snapshot,year=args.year)
    if args.snapshot:
        app.state.seek(.5);app.update_frame()
        args.snapshot.parent.mkdir(parents=True,exist_ok=True)
        app.fig.savefig(args.snapshot,dpi=130,facecolor=app.fig.get_facecolor())
        print(f"Saved {args.snapshot}")
    else:
        if args.paused: app.state.seek(0);app.update_frame()
        print("Lunar Passage: click the outer ring for a year; click the Moon to pause.",flush=True)
        app.plt.show()


if __name__=="__main__":
    main()

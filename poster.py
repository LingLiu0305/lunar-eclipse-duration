# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy", "pillow"]
# ///

"""Moonlit navy interactive century scatter plot and eclipse player."""
import datetime as dt
import math
import time

from atlas import LunarAtlas
from eclipse_model import clock, contacts, phase, time_at, TYPES

BACKGROUND, TEXT, DATA, ACCENT = '#101c2e', '#e5eaf1', '#91abc6', '#e8b96d'
CHART_LEFT, CHART_RIGHT = 130, 1510
CHART_BOTTOM, CHART_TOP = 155, 610
MAX_TOTALITY = 110
CENTURY_START = dt.datetime(2001,1,1,tzinfo=dt.timezone.utc).timestamp()
CENTURY_SECONDS = (dt.datetime(2101,1,1,tzinfo=dt.timezone.utc).timestamp()-CENTURY_START)
FOCUS_X, FOCUS_Y, FOCUS_R = 540, 475, 185
TIMELINE_X, TIMELINE_W, TIMELINE_Y = 290, 1050, 195


def year_x(year):
    """Map a catalogue year to the overview's linear time axis."""
    fraction=(year-2001)/100
    return CHART_LEFT+(CHART_RIGHT-CHART_LEFT)*fraction


def event_point(event):
    """Map exact eclipse time and totality duration to chart coordinates."""
    fraction=(event['greatestUT']/1000-CENTURY_START)/CENTURY_SECONDS
    x=CHART_LEFT+(CHART_RIGHT-CHART_LEFT)*fraction
    y=CHART_BOTTOM+(CHART_TOP-CHART_BOTTOM)*event['totalMinutes']/MAX_TOTALITY
    return x,y


class LunarPoster(LunarAtlas):
    def __init__(self, **kwargs):
        self.exploring=False
        self.has_selection=False
        self.resume_after_details=False
        super().__init__(**kwargs)
        self.state.playing=False
        # Soften synthetic crater rims without adding external assets.
        from PIL import Image, ImageFilter
        x,y,base,alpha=self.terrain
        softened=Image.fromarray(base.astype('float32')).convert('L').filter(ImageFilter.GaussianBlur(1.3))
        import numpy as np
        self.terrain=(x,y,base*.3+np.asarray(softened)*.7,alpha)
        self.build_scene()

    def text(self, x, y, value, size=9, color=None, align='left', **kw):
        kw.setdefault('fontfamily', 'DejaVu Sans')
        return super().text(x,y,value,size,color or TEXT,align,**kw)

    def background_art(self):
        before=set(self.ax.get_children())
        self.fig.set_facecolor(BACKGROUND)
        self.ax.set(xlim=(0,1600),ylim=(0,900),aspect='equal',facecolor=BACKGROUND)
        self.ax.set_axis_off()
        totals=[e['totalMinutes'] for e in self.state.records if e['totalMinutes'] is not None]
        self.text(80,852,'L U N A R   P A S S A G E',9)
        self.text(80,802,f'Total lunar eclipses last {min(totals):.0f}–{max(totals):.0f} minutes',
                  32,TEXT,fontfamily='STIXGeneral')
        self.text(82,764,f'{len(totals)} total lunar eclipses · 2001–2100 · Total phase only',11)
        self.text(1510,852,'NASA / ESPENAK & MEEUS',8,align='right')
        self.line([80,1510],[741,741],TEXT,.25,.7)
        self.text(80,30,'NASA GSFC catalogue · Includes future predictions',8)
        self.text(1510,30,'Select a dot to watch the eclipse',9,ACCENT,align='right')
        self.overview_art=[a for a in self.ax.get_children() if a not in before]

    def build_scene(self):
        for artist in self.dynamic: artist.remove()
        self.dynamic=[]; self.regions=[]; self.bubbles=[]
        self.bubble_art=[]
        self.focus_rects=[]
        for artist in self.overview_art: artist.set_visible(not self.exploring)
        before=set(self.ax.get_children())
        s=self.state
        if self.exploring:
            self.draw_focus()
            self.hint_label=self.text(800,31,'',8,ACCENT,align='center',zorder=10,
                                      bbox={'facecolor':BACKGROUND,'edgecolor':'none','pad':4})
            self.focus_halo=self.circle(-100,-100,17,ACCENT,1.5,zorder=15)
            if self.info_visible: self.draw_notes()
            self.dynamic=[a for a in self.ax.get_children() if a not in before]
            self.update_frame()
            return
        # A conventional time × duration plot makes the data claim legible
        # without requiring the reader to decode an ornamental geometry.
        band_left=year_x(s.year)
        band_right=year_x(min(s.year+1,2101))
        self.ax.add_patch(self.Rectangle((band_left,CHART_BOTTOM),max(3,band_right-band_left),
                          CHART_TOP-CHART_BOTTOM,facecolor=ACCENT,edgecolor='none',alpha=.08,zorder=1))
        for minutes in range(0,101,20):
            y=CHART_BOTTOM+(CHART_TOP-CHART_BOTTOM)*minutes/MAX_TOTALITY
            self.line([CHART_LEFT,CHART_RIGHT],[y,y],'#415570',.48,.65,zorder=1)
            self.text(CHART_LEFT-18,y,f'{minutes} min',9,align='right',zorder=2)
        self.line([CHART_LEFT,CHART_RIGHT],[CHART_BOTTOM,CHART_BOTTOM],TEXT,.55,.85,zorder=2)
        self.line([CHART_LEFT,CHART_LEFT],[CHART_BOTTOM,CHART_TOP],TEXT,.55,.85,zorder=2)
        for year in [2001,2020,2040,2060,2080,2100]:
            x=year_x(year)
            self.line([x,x],[CHART_BOTTOM,CHART_BOTTOM-8],TEXT,.45,.7,zorder=2)
            self.text(x,CHART_BOTTOM-25,str(year),8,align='center',zorder=3)
        self.text(CHART_RIGHT,CHART_BOTTOM-55,'Year',10,align='right')
        self.text(CHART_LEFT,CHART_TOP+27,'Minutes of totality',11)
        self.text(CHART_RIGHT,CHART_TOP+27,'ONE DOT = ONE TOTAL LUNAR ECLIPSE',8,align='right')
        self.text((band_left+band_right)/2,CHART_TOP+9,str(s.year),8,ACCENT,align='center')
        for e in s.records:
            if e['totalMinutes'] is None: continue
            x,y=event_point(e)
            radius=9
            selected=self.has_selection and e['id']==s.event['id']
            bubble=self.circle(x,y,radius,ACCENT if selected or e['year']==s.year else BACKGROUND,1.6 if selected or e['year']==s.year else .7,
                        fill=DATA,alpha=.98 if selected else .72,zorder=5 if selected else 4)
            self.bubble_art.append((bubble,e,selected))
            if selected:
                self.circle(x,y,radius+5,ACCENT,1.1,zorder=6)
            self.bubbles.append((x,y,14,e))
        totals=[e for e in s.records if e['totalMinutes'] is not None]
        for label,event,offset in [
            ('Shortest',min(totals,key=lambda e:e['totalMinutes']),(165,10)),
            ('Longest',max(totals,key=lambda e:e['totalMinutes']),(-80,40))]:
            x,y=event_point(event)
            date=dt.date.fromisoformat(event['date']).strftime('%d %b %Y')
            self.ax.annotate(f"{label} · {event['totalMinutes']:.1f} min\n{date}",
                xy=(x,y),xytext=(x+offset[0],y+offset[1]),fontsize=10,color=TEXT,
                fontfamily='DejaVu Sans',zorder=8,
                bbox={'facecolor':BACKGROUND,'edgecolor':'none','pad':3},
                arrowprops={'arrowstyle':'-','color':TEXT,'lw':.7})
        self.text(82,705,'YEAR',8)
        self.text(140,700,str(s.year),24,fontfamily='STIXGeneral')
        self.focus_button(254,705,36,'−',('year',-1))
        self.focus_button(301,705,36,'+',('year',1))
        self.text(350,711,f'{len(s.events)} eclipses',10)
        self.text(350,688,'Select a date →',9,ACCENT)
        for i,event in enumerate(s.events):
            x=650+i*235
            label=dt.date.fromisoformat(event['date']).strftime('%d %b')
            self.focus_button(x,708,185,label,('event',i))
            self.text(x,674,{'T':'Total','P':'Partial','N':'Penumbral'}[event['type']],8,align='center')
            if self.has_selection and i==s.index:
                self.line([x-90,x+90],[686,686],ACCENT,1,2,zorder=7)
        if not any(e['type']=='T' for e in s.events):
            self.text(350,662,'No total eclipse',8,DATA)
        self.phase_label=self.text(CHART_LEFT,75,'',7.5,ACCENT,zorder=8)
        self.status_label=self.text(CHART_LEFT,75,'',8,ACCENT,zorder=8)
        self.play_label=self.text(CHART_LEFT,75,'',8,zorder=8)
        self.clock_label=self.text(CHART_LEFT,75,'',11,fontfamily='DejaVu Sans Mono')
        self.date_label=self.text(CHART_LEFT,75,'',7.5)
        self.time_marker=self.circle(CHART_LEFT,CHART_BOTTOM,1,'none',fill='none',zorder=0)
        self.time_marker.set_visible(False)
        self.hint_label=self.text((CHART_LEFT+CHART_RIGHT)/2,70,'',8,ACCENT,align='center',zorder=10,
                                  bbox={'facecolor':BACKGROUND,'edgecolor':'none','pad':4})
        self.focus_halo=self.circle(-100,-100,17,ACCENT,1.5,zorder=15)
        if self.info_visible: self.draw_notes()
        self.dynamic=[a for a in self.ax.get_children() if a not in before]
        self.update_frame()

    def focus_button(self,x,y,width,label,action):
        self.text(x,y,label,10,ACCENT,align='center',zorder=7)
        self.ax.add_patch(self.Rectangle((x-width/2,y-20),width,40,fill=False,edgecolor='#71849d',lw=.7,zorder=5))
        self.focus_rects.append((x-width/2,y-20,width,40,action,label))
        self.register(x,y,20,action,label)

    def draw_focus(self):
        s=self.state
        self.focus_button(155,832,190,'Back to century',('overview',None))
        self.text(335,842,'YEAR',7.5)
        self.text(335,805,str(s.year),30,fontfamily='STIXGeneral')
        self.focus_button(467,828,36,'−',('year',-1))
        self.focus_button(511,828,36,'+',('year',1))
        for i,e in enumerate(s.events):
            x=675+i*220
            self.focus_button(x,824,175,dt.date.fromisoformat(e['date']).strftime('%d %b'),('event',i))
            if i==s.index: self.line([x-86,x+86],[802,802],ACCENT,1,2,zorder=7)
            self.text(x,787,{'T':'Total','P':'Partial','N':'Penumbral'}[e['type']],8,align='center')
        self.line([65,1535],[760,760],TEXT,.25,.65)
        self.text(540,707,'THE MOON IN EARTH’S SHADOW',9,align='center')
        self.moon=self.ax.imshow(self.moon_image(s.event,s.progress),
            extent=(FOCUS_X-FOCUS_R,FOCUS_X+FOCUS_R,FOCUS_Y-FOCUS_R,FOCUS_Y+FOCUS_R),zorder=6)
        self.register(FOCUS_X,FOCUS_Y,FOCUS_R,('play',None),'Click the Moon to play / pause')
        self.text(980,682,f'Eclipse {s.index+1} of {len(s.events)} selected',10,ACCENT)
        self.text(975,632,dt.date.fromisoformat(s.event['date']).strftime('%d %b %Y'),33,fontfamily='STIXGeneral')
        self.text(980,595,TYPES[s.event['type']],10)
        duration=f"{s.event['totalMinutes']:.1f} min totality" if s.event['totalMinutes'] is not None else 'No totality'
        self.text(978,548,duration,23,TEXT,fontfamily='STIXGeneral')
        self.text(980,519,f"Full event · {s.event['penumbralMinutes']:.1f} min",9)
        self.line([980,1460],[491,491],TEXT,.25,.65)
        self.text(980,464,'ANIMATION TIME  /  '+('UT+8 ~' if s.offset else 'UT'),9)
        self.clock_label=self.text(977,427,'',25,fontfamily='DejaVu Sans Mono')
        self.date_label=self.text(980,395,'',11)
        self.phase_label=self.text(980,355,'',11,ACCENT)
        self.status_label=self.text(980,323,'',10,ACCENT)
        self.text(980,291,f'Accelerated playback · {60/s.speed:g}s per event',9)
        if not any(e['type']=='T' for e in s.events):
            self.text(980,260,'No total lunar eclipse this year',9,DATA)
        self.text(540,254,'Click the Moon to play or pause',9,align='center')
        self.line([TIMELINE_X,TIMELINE_X+TIMELINE_W],[TIMELINE_Y]*2,'#71849d',1,3)
        self.time_marker=self.circle(TIMELINE_X,TIMELINE_Y,7,ACCENT,fill=ACCENT,zorder=8)
        self.text(815,221,'DRAG TO EXPLORE THE ECLIPSE',8,align='center')
        for p,align in [(0,'left'),(1,'right')]:
            instant=clock(s.event,p,s.offset)
            self.text(TIMELINE_X+TIMELINE_W*p,163,('BEGIN ~ ' if p==0 else 'END ~ ')+instant.strftime('%d %b %H:%M'),9,align=align)
        self.focus_button(370,104,160,'',('play',None))
        self.play_label=self.text(370,104,'',10,ACCENT,align='center',zorder=8)
        self.focus_button(560,104,130,'Replay',('replay',None))
        self.focus_button(1180,104,320,'Data & phase details',('info',None))
        self.text(65,40,'LUNAR PASSAGE  /  NASA GSFC',7.5)

    def update_frame(self):
        s=self.state
        if not self.exploring:
            self.fig.canvas.draw_idle()
            return
        self.moon.set_data(self.moon_image(s.event,s.progress))
        instant=clock(s.event,s.progress,s.offset)
        self.clock_label.set_text(instant.strftime('%H:%M:%S'))
        self.date_label.set_text(instant.strftime('%d %b %Y').upper())
        self.phase_label.set_text(phase(s.event,s.progress))
        self.status_label.set_text('Playing' if s.playing else 'Complete' if s.progress>=1 else 'Paused')
        self.play_label.set_text('Pause' if s.playing else 'Replay' if s.progress>=1 else 'Play')
        self.time_marker.center=(TIMELINE_X+TIMELINE_W*s.progress,TIMELINE_Y)
        self.fig.canvas.draw_idle()

    def hit(self,x,y):
        if self.info_visible:
            if abs(y-400)<20:
                for xx,action in [(520,'zone'),(735,'speed')]:
                    if abs(x-xx)<80: return (action,None),'Change setting'
            return ('info',None),'Close details · Escape'
        if self.exploring and TIMELINE_X<=x<=TIMELINE_X+TIMELINE_W and abs(y-TIMELINE_Y)<18:
            return ('timeline',(x-TIMELINE_X)/TIMELINE_W),'Drag to seek · pauses playback'
        for rx,ry,w,h,action,label in self.focus_rects:
            if rx<=x<=rx+w and ry<=y<=ry+h: return action,label
        for hx,hy,r,action,label in reversed(self.regions):
            if math.hypot(x-hx,y-hy)<=r: return action,label
        if self.exploring: return None,''
        candidates=[(math.hypot(x-bx,y-by)/r,e) for bx,by,r,e in self.bubbles if math.hypot(x-bx,y-by)<=r]
        if candidates:
            e=min(candidates,key=lambda item:item[0])[1]
            return ('bubble',e),f"{e['date']} · {e['totalMinutes']:.1f} minutes of totality"
        if CHART_LEFT<=x<=CHART_RIGHT and CHART_BOTTOM-38<=y<=CHART_BOTTOM-8:
            fraction=(x-CHART_LEFT)/(CHART_RIGHT-CHART_LEFT)
            year=max(2001,min(2100,2001+int(fraction*100+1e-7)))
            return ('select_year',year),f'{year} · select year'
        return None,''

    def act(self,action):
        name=action[0]
        if name=='info':
            if not self.info_visible:
                self.resume_after_details=self.state.playing
                self.state.playing=False
                self.info_visible=True
            else:
                self.info_visible=False
                self.state.playing=self.resume_after_details and self.exploring and self.state.progress<1
            self.last_tick=time.monotonic()
            self.focus_index=-1
            self.build_scene()
            return
        if name=='overview':
            self.exploring=False
            self.state.playing=False
            self.build_scene()
            return
        if not self.exploring and name in ['select_year','year']:
            self.state.select_year(action[1] if name=='select_year' else self.state.year+action[1])
            self.state.playing=False
            self.has_selection=False
            self.focus_index=-1
            self.build_scene()
            return
        first=not self.exploring
        if name in ['bubble','select_year','year','event','play','seek','timeline','replay','info']:
            self.exploring=True
            self.has_selection=True
        if action[0]=='bubble':
            e=action[1]
            self.state.select_year(e['year'])
            self.state.select_event(next(i for i,v in enumerate(self.state.events) if v['id']==e['id']))
            self.build_scene()
        else:
            if first:
                self.build_scene()
            super().act(action)

    def on_click(self,event):
        super().on_click(event)
        # Year selection is a discrete action, never an implicit drag.
        if self.dragging=='year': self.dragging=None

    def on_motion(self,event):
        if event.inaxes is not self.ax or event.xdata is None: return
        x,y=event.xdata,event.ydata
        if self.dragging=='year':
            fraction=(x-CHART_LEFT)/(CHART_RIGHT-CHART_LEFT)
            year=max(2001,min(2100,2001+int(fraction*100+1e-7)))
            if year!=self.state.year: self.act(('select_year',year))
        elif self.dragging=='timeline':
            self.state.seek((x-TIMELINE_X)/TIMELINE_W); self.update_frame()
        action,label=self.hit(x,y)
        hover_year=action[1] if action and action[0]=='select_year' else None
        for artist,e,selected in self.bubble_art:
            artist.set_alpha((.95 if e['year']==hover_year else .2) if hover_year else (.95 if selected else .7))
        self.hint_label.set_text(label)
        if action and action[0]=='bubble':
            bx,by=event_point(action[1])
            self.hint_label.set_position((max(CHART_LEFT+150,min(CHART_RIGHT-150,bx)),by+24))
        elif hover_year:
            self.hint_label.set_position((year_x(hover_year),CHART_TOP+24))
        else:
            self.hint_label.set_position(((CHART_LEFT+CHART_RIGHT)/2,70))
        if self.interactive:
            from matplotlib.backend_tools import Cursors
            self.fig.canvas.set_cursor(Cursors.HAND if action else Cursors.POINTER)
        self.fig.canvas.draw_idle()

    def on_key(self,event):
        if self.info_visible and event.key in ['t','s']:
            self.act(('zone' if event.key=='t' else 'speed',None))
        else:
            super().on_key(event)

    def draw_notes(self):
        self.ax.add_patch(self.Rectangle((410,150),790,620,facecolor=BACKGROUND,edgecolor=TEXT,lw=.8,zorder=30))
        self.text(450,730,'THE SELECTED SHADOW',18,weight='bold',zorder=31)
        self.text(450,706,self.state.event['date']+'  /  '+('UT+8 ~' if self.state.offset else 'UT'),9,zorder=31)
        for i,(code,label,instant) in enumerate(contacts(self.state.event)):
            local=dt.datetime.fromtimestamp(instant/1000,dt.timezone.utc)+dt.timedelta(hours=self.state.offset)
            self.text(450,679-i*32,f'{code:3}   {label}',10,zorder=31)
            self.text(1155,679-i*32,('' if code=='MAX' else '~ ')+local.strftime('%d %b %H:%M:%S'),10,align='right',zorder=31)
        lines=['85 total eclipses shown; year controls access all 228 eclipses.',
               'Horizontal position is date; vertical position is totality in minutes.',
               'Greatest UT = catalogue TD minus delta T. Other contacts are estimates.',
               'Artistic Moon, not an ephemeris. Times do not imply local visibility.',
               'Space: play · Arrows: year / seek · [ ]: event · F: fullscreen',
               f"Full event: {self.state.event['penumbralMinutes']:.1f} min · Playback: {60/self.state.speed:g}s",
               'Click outside the settings or press Escape to close.']
        for i,line in enumerate(lines): self.text(450,337-i*28,line,9,zorder=31)
        self.text(450,449,'Playback resumes on close.' if self.resume_after_details else 'Playback stays paused on close.',9,ACCENT,zorder=31)
        self.text(520,400,'Time zone: '+('UT+8 ~' if self.state.offset else 'UT'),9,ACCENT,align='center',zorder=31)
        self.text(735,400,f'Speed: {self.state.speed}×',9,ACCENT,align='center',zorder=31)

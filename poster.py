"""Paper-and-coral interactive century poster; shared offline eclipse model."""
import datetime as dt
import math
import time

from atlas import LunarAtlas
from eclipse_model import clock, contacts, phase, time_at, TYPES

PAPER, BROWN, CORAL, TEAL = '#f0eee7', '#63452f', '#cd5749', '#478c83'
PX, PY, RING = 1000, 455, 340
INNER, RADIAL_SCALE = 170, 1.48
CONTROL_Y = 67
FOCUS_X, FOCUS_Y, FOCUS_R = 540, 475, 185
TIMELINE_X, TIMELINE_W, TIMELINE_Y = 290, 1050, 195


def point(radius, fraction):
    angle = math.pi/2 - 2*math.pi*fraction
    return PX+radius*math.cos(angle), PY+radius*math.sin(angle)


def event_point(event):
    date = dt.date.fromisoformat(event['date'])
    fraction = (date-dt.date(2001,1,1)).days/(dt.date(2101,1,1)-dt.date(2001,1,1)).days
    return point(INNER+event['totalMinutes']*RADIAL_SCALE, fraction)


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
        return super().text(x,y,value,size,color or BROWN,align,**kw)

    def background_art(self):
        before=set(self.ax.get_children())
        self.fig.set_facecolor(PAPER)
        self.ax.set(xlim=(0,1600),ylim=(0,900),aspect='equal',facecolor=PAPER)
        self.ax.set_axis_off()
        self.text(67,830,'L U N A R   P A S S A G E',9)
        self.text(65,785,'A Century of',30,fontfamily='STIXGeneral',fontstyle='italic')
        self.text(63,735,'Total Lunar',36,CORAL,fontfamily='STIXGeneral')
        self.text(63,683,'Eclipses',40,CORAL,fontfamily='STIXGeneral')
        self.text(67,630,'2001–2100  /  85 total eclipses',11)
        self.line([67,420],[605,605],BROWN,.35,.7)
        self.text(67,575,'One circle, one eclipse.',11,fontfamily='STIXGeneral',fontstyle='italic')
        self.text(67,552,'Clockwise through time.',9)
        self.text(67,531,'Farther out means longer totality.',9)
        self.text(67,504,'Select a circle to follow its shadow.',9,CORAL)
        self.text(67,55,'NASA / ESPENAK & MEEUS',7.5)
        self.text(67,35,'ARTISTIC MOON · ESTIMATED CONTACTS',7)
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
            self.hint_label=self.text(800,31,'',8,TEAL,align='center',zorder=10,
                                      bbox={'facecolor':PAPER,'edgecolor':'none','pad':4})
            self.focus_halo=self.circle(-100,-100,17,TEAL,1.5,zorder=15)
            if self.info_visible: self.draw_notes()
            self.dynamic=[a for a in self.ax.get_children() if a not in before]
            self.update_frame()
            return
        # Quiet radial scale: no joining polygon or dense contact table.
        for minutes in [0,50,100]:
            self.circle(PX,PY,INNER+minutes*RADIAL_SCALE,'#cbbfae',.55,alpha=.5,zorder=1)
            tx,ty=point(INNER+minutes*RADIAL_SCALE,.72)
            self.text(tx,ty,f'{minutes} min',7,align='center',zorder=7,
                      bbox={'facecolor':PAPER,'edgecolor':'none','pad':1})
        for year in range(2001,2101):
            f=(year-2001)/100
            x,y=point(RING,f); xx,yy=point(RING-5,f)
            self.line([x,xx],[y,yy],BROWN,.32,.6,zorder=2)
            if year in [2001,2021,2041,2061,2081]:
                tx,ty=point(RING+22,f)
                self.text(tx,ty,str(year),9,align='center',zorder=3)
        for e in s.records:
            if e['totalMinutes'] is None: continue
            x,y=event_point(e)
            radius=13
            selected=self.has_selection and e['id']==s.event['id']
            bubble=self.circle(x,y,radius,CORAL if selected else 'none',1.2,
                        fill=CORAL,alpha=.95 if selected else .52 if self.exploring else .7,zorder=4 if selected else 3)
            self.bubble_art.append((bubble,e,selected))
            if selected:
                self.circle(x,y,radius+5,TEAL,1.1,zorder=5)
                distance=math.hypot(x-PX,y-PY)
                self.line([PX+(x-PX)*INNER/distance,x],[PY+(y-PY)*INNER/distance,y],TEAL,.8,1,zorder=2)
            self.bubbles.append((x,y,18,e))
        x,y=point(RING,(s.year-2001)/100)
        self.circle(x,y,7,TEAL,1,fill=PAPER,zorder=7)
        self.ax.annotate('',xy=point(RING+14,.043),xytext=point(RING+14,.012),
                         arrowprops={'arrowstyle':'->','color':BROWN,'lw':.8},zorder=3)
        self.text(67,454,'BROWSING YEAR',8)
        self.text(63,411,str(s.year),35,fontfamily='STIXGeneral')
        for x,delta,label in [(273,-1,'−'),(321,1,'+')]:
            self.circle(x,411,17,BROWN,.65,zorder=5)
            self.text(x,411,label,15,align='center',zorder=6)
            self.register(x,411,21,('year',delta),'Previous year' if delta<0 else 'Next year')
        self.text(67,368,f'{len(s.events)} eclipses this year · select a Moon',9)
        for i,e in enumerate(s.events):
            x,y=91+i*78,321
            active=self.has_selection and i==s.index
            self.circle(x,y,25,TEAL if active else '#c1b5a7',1.4 if active else .6,zorder=5)
            self.ax.imshow(self.moon_image(e,.5),extent=(x-20,x+20,y-20,y+20),zorder=6)
            self.text(x,282,dt.date.fromisoformat(e['date']).strftime('%d %b'),8,align='center')
            self.register(x,y,29,('event',i),f"Select {e['date']}")
        self.text(67,225,'ALL ECLIPSES IN THIS YEAR',7.5)
        self.text(67,205,'Includes partial and penumbral eclipses.',8)
        if self.exploring:
            self.text(67,256,f'Eclipse {s.index+1} of {len(s.events)} selected',9,TEAL)
        if not any(e['type']=='T' for e in s.events):
            self.text(67,181,'No total lunar eclipse this year',9,CORAL)

        moon_r=85
        self.moon=self.ax.imshow(self.moon_image(s.event,s.progress if self.exploring else 0),extent=(PX-moon_r,PX+moon_r,PY+22-moon_r,PY+22+moon_r),zorder=6)
        self.register(PX,PY+22,moon_r,('play',None),'Click to explore / play / pause')
        self.phase_label=self.text(PX,PY-59,'',7.5,TEAL,align='center',zorder=8)
        self.status_label=self.text(PX,PY-140,'',8,TEAL,align='center',zorder=8)
        self.play_label=self.text(PX,PY-158,'',8,align='center',zorder=8,
                                  bbox={'facecolor':PAPER,'edgecolor':'none','pad':2})
        self.text(PX,101,'CLICK A CIRCLE OR A YEAR TO OPEN THE ECLIPSE VIEW',7.5,align='center')
        self.text(PX,PY-93,'Choose a circle or a year',10,align='center')
        self.clock_label=self.text(PX,PY-81,'',11,align='center',fontfamily='DejaVu Sans Mono')
        self.date_label=self.text(PX,PY-99,'',7.5,align='center')
        self.time_marker=self.circle(PX-85,PY-119,4,TEAL,fill=TEAL,zorder=8)
        self.time_marker.set_visible(self.exploring)
        self.hint_label=self.text(PX,30,'',8,TEAL,align='center',zorder=10,
                                  bbox={'facecolor':PAPER,'edgecolor':'none','pad':4})
        self.focus_halo=self.circle(-100,-100,17,TEAL,1.5,zorder=15)
        if self.info_visible: self.draw_notes()
        self.dynamic=[a for a in self.ax.get_children() if a not in before]
        self.update_frame()

    def focus_button(self,x,y,width,label,action):
        self.text(x,y,label,10,TEAL,align='center',zorder=7)
        self.ax.add_patch(self.Rectangle((x-width/2,y-20),width,40,fill=False,edgecolor='#b6b8a7',lw=.7,zorder=5))
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
            if i==s.index: self.line([x-86,x+86],[802,802],TEAL,1,2,zorder=7)
            self.text(x,787,{'T':'Total','P':'Partial','N':'Penumbral'}[e['type']],8,align='center')
        self.line([65,1535],[760,760],BROWN,.25,.65)
        self.text(540,707,'THE MOON IN EARTH’S SHADOW',9,align='center')
        self.moon=self.ax.imshow(self.moon_image(s.event,s.progress),
            extent=(FOCUS_X-FOCUS_R,FOCUS_X+FOCUS_R,FOCUS_Y-FOCUS_R,FOCUS_Y+FOCUS_R),zorder=6)
        self.register(FOCUS_X,FOCUS_Y,FOCUS_R,('play',None),'Click the Moon to play / pause')
        self.text(980,682,f'Eclipse {s.index+1} of {len(s.events)} selected',10,TEAL)
        self.text(975,632,dt.date.fromisoformat(s.event['date']).strftime('%d %b %Y'),33,fontfamily='STIXGeneral')
        self.text(980,595,TYPES[s.event['type']],10)
        duration=f"{s.event['totalMinutes']:.1f} min totality" if s.event['totalMinutes'] is not None else 'No totality'
        self.text(978,548,duration,23,CORAL,fontfamily='STIXGeneral')
        self.text(980,519,f"Full event · {s.event['penumbralMinutes']:.1f} min",9)
        self.line([980,1460],[491,491],BROWN,.25,.65)
        self.text(980,464,'ANIMATION TIME  /  '+('UT+8 ~' if s.offset else 'UT'),9)
        self.clock_label=self.text(977,427,'',25,fontfamily='DejaVu Sans Mono')
        self.date_label=self.text(980,395,'',11)
        self.phase_label=self.text(980,355,'',11,TEAL)
        self.status_label=self.text(980,323,'',10,TEAL)
        self.text(980,291,f'Accelerated playback · {60/s.speed:g}s per event',9)
        if not any(e['type']=='T' for e in s.events):
            self.text(980,260,'No total lunar eclipse this year',9,CORAL)
        self.text(540,254,'Click the Moon to play or pause',9,align='center')
        self.line([TIMELINE_X,TIMELINE_X+TIMELINE_W],[TIMELINE_Y]*2,'#c7baaa',1,3)
        self.time_marker=self.circle(TIMELINE_X,TIMELINE_Y,7,TEAL,fill=TEAL,zorder=8)
        self.text(815,221,'DRAG TO EXPLORE THE ECLIPSE',8,align='center')
        for p,align in [(0,'left'),(1,'right')]:
            instant=clock(s.event,p,s.offset)
            self.text(TIMELINE_X+TIMELINE_W*p,163,('BEGIN ~ ' if p==0 else 'END ~ ')+instant.strftime('%d %b %H:%M'),9,align=align)
        self.focus_button(370,104,160,'',('play',None))
        self.play_label=self.text(370,104,'',10,TEAL,align='center',zorder=8)
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
        if abs(math.hypot(x-PX,y-PY)-RING)<14:
            f=((math.pi/2-math.atan2(y-PY,x-PX))/(2*math.pi))%1
            year=2001+int(f*100+.5)%100
            return ('select_year',year),f'{year} · click to explore this year'
        candidates=[(math.hypot(x-bx,y-by)/r,e) for bx,by,r,e in self.bubbles if math.hypot(x-bx,y-by)<=r]
        if candidates:
            e=min(candidates,key=lambda item:item[0])[1]
            return ('bubble',e),f"{e['date']} · {e['totalMinutes']:.1f} minutes of totality"
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
        # A year click navigates; do not drag an invisible ring in the new view.
        if self.exploring and self.dragging=='year': self.dragging=None

    def on_motion(self,event):
        if event.inaxes is not self.ax or event.xdata is None: return
        x,y=event.xdata,event.ydata
        if self.dragging=='year':
            f=((math.pi/2-math.atan2(y-PY,x-PX))/(2*math.pi))%1
            year=2001+int(f*100+.5)%100
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
            self.hint_label.set_position((bx,by+24))
        elif hover_year:
            bx,by=point(RING,(hover_year-2001)/100)
            self.hint_label.set_position((bx,by+24))
        else:
            self.hint_label.set_position((PX,30))
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
        self.ax.add_patch(self.Rectangle((410,150),790,620,facecolor=PAPER,edgecolor=BROWN,lw=.8,zorder=30))
        self.text(450,730,'THE SELECTED SHADOW',18,weight='bold',zorder=31)
        self.text(450,706,self.state.event['date']+'  /  '+('UT+8 ~' if self.state.offset else 'UT'),9,zorder=31)
        for i,(code,label,instant) in enumerate(contacts(self.state.event)):
            local=dt.datetime.fromtimestamp(instant/1000,dt.timezone.utc)+dt.timedelta(hours=self.state.offset)
            self.text(450,679-i*32,f'{code:3}   {label}',10,zorder=31)
            self.text(1155,679-i*32,('' if code=='MAX' else '~ ')+local.strftime('%d %b %H:%M:%S'),10,align='right',zorder=31)
        lines=['85 total eclipses shown; year controls access all 228 eclipses.',
               'Radial distance encodes totality; all bubbles have the same size.',
               'Greatest UT = catalogue TD minus delta T. Other contacts are estimates.',
               'Artistic Moon, not an ephemeris. Times do not imply local visibility.',
               'Space: play · Arrows: year / seek · [ ]: event · F: fullscreen',
               f"Full event: {self.state.event['penumbralMinutes']:.1f} min · Playback: {60/self.state.speed:g}s",
               'Click outside the settings or press Escape to close.']
        for i,line in enumerate(lines): self.text(450,337-i*28,line,9,zorder=31)
        self.text(450,449,'Playback resumes on close.' if self.resume_after_details else 'Playback stays paused on close.',9,TEAL,zorder=31)
        self.text(520,400,'Time zone: '+('UT+8 ~' if self.state.offset else 'UT'),9,TEAL,align='center',zorder=31)
        self.text(735,400,f'Speed: {self.state.speed}×',9,TEAL,align='center',zorder=31)

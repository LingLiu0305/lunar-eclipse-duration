# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy", "pillow"]
# ///

"""Headless checks for the native instrument's real click/key callbacks."""

import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build import read_catalogue
from eclipse_model import Playback, clock, contacts, phase, shadow, time_at, phase_intervals, milestones
from eclipse_model import totality_context, phase_explanation


class TimingTests(unittest.TestCase):
    def test_totality_comparison_excludes_events_without_totality(self):
        records=read_catalogue()
        event=next(e for e in records if e["date"]=="2026-03-03")
        context=totality_context(records,event)
        self.assertEqual(context["count"],85)
        self.assertEqual(context["median"],71.7)
        self.assertEqual(context["selected"],58.3)
        self.assertAlmostEqual(context["difference"],-13.4)
        partial=next(e for e in records if e["date"]=="2026-08-28")
        context=totality_context(records,partial)
        self.assertIsNone(context["selected"])
        self.assertIsNone(context["difference"])
        self.assertEqual(context["count"],85)

    def test_phase_explanations_distinguish_faint_and_dark_shadow(self):
        records=read_catalogue()
        total=next(e for e in records if e["date"]=="2026-03-03")
        self.assertIn("whole Moon",phase_explanation(total,.49))
        self.assertIn("Only part",phase_explanation(total,.3))
        penumbral=next(e for e in records if e["type"]=="N")
        self.assertIn("faint outer shadow",phase_explanation(penumbral,.3))
        self.assertIn("left Earth's shadow",phase_explanation(total,1))

    def test_colored_stages_cover_event_without_double_counting_totality(self):
        for event in read_catalogue():
            intervals=phase_intervals(event)
            self.assertEqual(intervals[0][0],0)
            self.assertEqual(intervals[-1][1],1)
            for left,right in zip(intervals,intervals[1:]):
                self.assertEqual(left[1],right[0])
            minutes={kind:sum((b-a)*event["penumbralMinutes"] for a,b,k in intervals if k==kind)
                     for kind in ["penumbra","partial","totality"]}
            self.assertAlmostEqual(minutes["totality"],event["totalMinutes"] or 0)
            self.assertAlmostEqual(minutes["partial"]+minutes["totality"],event["umbralMinutes"] or 0)
            self.assertAlmostEqual(sum(minutes.values()),event["penumbralMinutes"])

    def test_next_milestone_at_greatest_and_completion(self):
        for event in read_catalogue():
            reached,next_point=milestones(event,.5)
            self.assertEqual(reached[0],"MAX")
            self.assertEqual(next_point[0],{"T":"U3","P":"U4","N":"P4"}[event["type"]])
            reached,next_point=milestones(event,1)
            self.assertEqual(reached[0],"P4")
            self.assertIsNone(next_point)

    def test_every_contact_matches_geometry(self):
        for e in read_catalogue():
            points=contacts(e)
            self.assertEqual(len(points),{"T":7,"P":5,"N":3}[e["type"]])
            self.assertEqual(points,sorted(points,key=lambda p:p[2]))
            for code,_,instant in points:
                progress=(instant-time_at(e,0))/(e["penumbralMinutes"]*60000)
                x,y,r,pr=shadow(e,progress)
                distance=math.hypot(x,y)
                if code in ["P1","P4"]: self.assertAlmostEqual(distance,pr+1)
                if code in ["U1","U4"]: self.assertAlmostEqual(distance,r+1)
                if code in ["U2","U3"]: self.assertAlmostEqual(distance,r-1)
                if code=="MAX": self.assertAlmostEqual((r+1-distance)/2,e["umbralMagnitude"])

    def test_playback_boundaries_and_date(self):
        s=Playback(read_catalogue(),2001)
        self.assertEqual(clock(s.event,.5,8).strftime("%Y-%m-%d"),"2001-01-10")
        self.assertEqual(clock(s.event,.5,0).strftime("%Y-%m-%d"),"2001-01-09")
        s.seek(.99);s.toggle();s.speed=4;s.advance(1)
        self.assertEqual(s.progress,1);self.assertFalse(s.playing)
        self.assertEqual(phase(s.event,s.progress),"ECLIPSE COMPLETE")
        s.replay();self.assertEqual(s.progress,0);self.assertTrue(s.playing)
        s.select_year(1900);self.assertEqual(s.year,2001)
        s.select_year(2200);self.assertEqual(s.year,2100)


class NativeInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import matplotlib
        matplotlib.use("Agg")
        from atlas import LunarAtlas
        cls.app=LunarAtlas(interactive=False)

    @classmethod
    def tearDownClass(cls):
        cls.app.plt.close(cls.app.fig)

    def click(self,x,y):
        self.app.on_click(SimpleNamespace(inaxes=self.app.ax,xdata=x,ydata=y,button=1))
        self.app.on_release(None)

    def test_ring_hit_mapping_for_all_years(self):
        from atlas import year_at,year_position
        for year in range(2001,2101):
            point=year_position(year)
            self.assertEqual(year_at(*point),year)
            self.assertEqual(self.app.hit(*point)[0],("select_year",year))

    def test_visible_event_text_play_label_and_timeline_are_clickable(self):
        from atlas import CX,CY,NODE_POSITIONS
        self.app.act(("select_year",2026))
        x,y=NODE_POSITIONS[1]
        self.click(x+180,y+19)
        self.assertEqual(self.app.state.index,1)
        self.click(CX,CY-143)
        self.assertFalse(self.app.state.playing)
        self.click(1090+450*.25,372)
        self.assertAlmostEqual(self.app.state.progress,.25)
        self.app.on_click(SimpleNamespace(inaxes=self.app.ax,xdata=1315,ydata=372,button=1))
        self.app.on_motion(SimpleNamespace(inaxes=self.app.ax,xdata=1427.5,ydata=375))
        self.app.on_release(None)
        self.assertAlmostEqual(self.app.state.progress,.75)
        self.assertFalse(self.app.state.playing)
        self.app.act(("speed",None))
        self.assertTrue(any(f"{60/self.app.state.speed:g}s PER FULL EVENT" in t.get_text()
                            for t in self.app.ax.texts))

    def test_four_event_year_labels_select_correct_event(self):
        from atlas import NODE_POSITIONS
        self.app.act(("select_year",2009))
        self.assertEqual(len(self.app.state.events),4)
        for i,(x,y) in enumerate(NODE_POSITIONS[:4]):
            self.click(x+180,y)
            self.assertEqual(self.app.state.index,i)

    def test_native_hover_cursor_and_drag(self):
        from atlas import CX,CY,year_position,phase_position
        from matplotlib.backend_tools import Cursors
        self.app.interactive=True
        try:
            with patch.object(self.app.fig.canvas,"set_cursor") as cursor:
                self.app.on_motion(SimpleNamespace(inaxes=self.app.ax,xdata=CX,ydata=CY))
                cursor.assert_called_with(Cursors.HAND)
            self.app.dragging="year"
            x,y=year_position(2035)
            self.app.on_motion(SimpleNamespace(inaxes=self.app.ax,xdata=x,ydata=y))
            self.assertEqual(self.app.state.year,2035)
            self.app.dragging="time"
            x,y=phase_position(.75)
            self.app.on_motion(SimpleNamespace(inaxes=self.app.ax,xdata=x,ydata=y))
            self.assertAlmostEqual(self.app.state.progress,.75)
            self.assertFalse(self.app.state.playing)
        finally:
            self.app.dragging=None
            self.app.interactive=False

    def test_direct_manipulation(self):
        from atlas import year_position,CX,CY,NODE_POSITIONS,phase_position
        self.click(*year_position(2026))
        self.assertEqual(self.app.state.year,2026)
        self.assertTrue(self.app.state.playing)
        self.click(CX,CY);self.assertFalse(self.app.state.playing)
        self.click(*NODE_POSITIONS[1]);self.assertEqual(self.app.state.event["type"],"P")
        self.click(*phase_position(.5));self.assertEqual(self.app.state.progress,.5)
        self.assertFalse(self.app.state.playing)
        self.assertEqual(self.app.phase_label.get_text(),"GREATEST ECLIPSE")
        self.app.on_key(SimpleNamespace(key="r"));self.assertTrue(self.app.state.playing)
        self.app.on_key(SimpleNamespace(key="right"));self.assertEqual(self.app.state.year,2027)
        self.app.on_key(SimpleNamespace(key="tab"))
        self.assertGreaterEqual(self.app.focus_index,0)
        self.app.on_key(SimpleNamespace(key="enter"));self.assertEqual(self.app.state.year,2026)
        self.app.on_key(SimpleNamespace(key="i"));self.assertTrue(self.app.info_visible)
        self.assertFalse(self.app.state.playing)
        self.app.on_key(SimpleNamespace(key="escape"));self.assertFalse(self.app.info_visible)
        self.assertTrue(all(not any('\u4e00'<=c<='\u9fff' for c in t.get_text()) for t in self.app.ax.texts))

    def test_phase_key_is_clickable_and_updates_readouts(self):
        self.app.act(("select_year",2026))
        self.click(310,509-3*34)
        self.assertEqual(self.app.state.progress,.5)
        self.assertEqual(self.app.next_label.get_text(),"NEXT / Totality ends")
        self.assertEqual(self.app.clock_label.get_text(),"19:33:37")
        highlighted=[code for code,row,_ in self.app.phase_rows if row.get_alpha()>0]
        self.assertEqual(highlighted,["MAX"])
        self.app.act(("zone",None))
        self.assertEqual(self.app.clock_label.get_text(),"11:33:37")
        self.assertTrue(any("UNIVERSAL TIME" in t.get_text() for t in self.app.ax.texts))
        self.app.act(("select_year",2002))
        self.assertEqual(len(self.app.phase_rows),3)
        self.click(100,509-34)
        self.assertEqual(self.app.next_label.get_text(),"NEXT / Eclipse ends")
        self.assertTrue(any(t.get_text()=="None" for t in self.app.ax.texts))
        self.click(100,509-2*34)
        self.assertEqual(self.app.next_label.get_text(),"END / Eclipse complete")
        self.app.state.offset=8
        self.app.act(("select_year",2001))
        self.click(100,509-3*34)
        self.assertEqual(self.app.date_label.get_text(),"10 JAN 2001")


if __name__=="__main__":
    unittest.main()

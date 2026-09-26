"""Interaction and data checks for the simplified editorial poster."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import matplotlib
matplotlib.use('Agg')
from poster import LunarPoster, point, event_point, PX, PY, RING, CONTROL_Y
from poster import FOCUS_X, FOCUS_Y, TIMELINE_X, TIMELINE_W, TIMELINE_Y


class PosterTests(unittest.TestCase):
    def setUp(self):
        self.app=LunarPoster(interactive=False)

    def tearDown(self):
        self.app.plt.close(self.app.fig)

    def click(self,x,y):
        self.app.on_click(SimpleNamespace(inaxes=self.app.ax,xdata=x,ydata=y,button=1))
        self.app.on_release(None)

    def test_bubbles_match_catalogue_and_select_actual_event(self):
        self.assertEqual(len(self.app.bubbles),85)
        for x,y,r,e in self.app.bubbles:
            self.assertEqual((x,y),event_point(e))
            # Tiny bubbles have an enlarged invisible pointer target.
            self.assertEqual(r,self.app.bubbles[0][2])
        e=next(v for v in self.app.state.records if v['date']=='2018-07-27')
        self.click(*event_point(e))
        self.assertEqual(self.app.state.event['id'],e['id'])
        self.assertTrue(self.app.state.playing)

    def test_year_ring_all_years_and_partial_event(self):
        for year in range(2001,2101):
            self.assertEqual(self.app.hit(*point(RING,(year-2001)/100))[0],('select_year',year))
        self.click(*point(RING,.25))
        self.click(895,824)
        self.assertEqual(self.app.state.event['type'],'P')
        self.assertTrue(any(t.get_text()=='No totality' for t in self.app.ax.texts))

    def test_animation_seek_notes_and_keyboard(self):
        self.app.act(('select_year',2026))
        self.click(FOCUS_X,FOCUS_Y)
        self.assertFalse(self.app.state.playing)
        self.click(TIMELINE_X+TIMELINE_W/2,TIMELINE_Y)
        self.assertEqual(self.app.state.progress,.5)
        self.assertIn('19:33:37',self.app.clock_label.get_text())
        self.app.on_click(SimpleNamespace(inaxes=self.app.ax,xdata=TIMELINE_X+TIMELINE_W/2,ydata=TIMELINE_Y,button=1))
        self.app.on_motion(SimpleNamespace(inaxes=self.app.ax,xdata=TIMELINE_X+TIMELINE_W,ydata=TIMELINE_Y))
        self.app.on_release(None)
        self.assertEqual(self.app.state.progress,1)
        self.click(1180,104)
        self.assertTrue(self.app.info_visible)
        self.assertTrue(any('Penumbral entry' in t.get_text() for t in self.app.ax.texts))
        self.app.on_key(SimpleNamespace(key='escape'))
        self.assertFalse(self.app.info_visible)
        self.app.on_key(SimpleNamespace(key='tab'))
        self.app.on_key(SimpleNamespace(key='enter'))
        self.assertFalse(self.app.exploring)
        self.assertEqual(self.app.state.year,2026)

    def test_four_event_year_and_midnight(self):
        self.app.act(('select_year',2009))
        for i in range(4):
            self.click(675+i*220,824)
            self.assertEqual(self.app.state.index,i)
        self.app.act(('select_year',2001))
        self.click(TIMELINE_X+TIMELINE_W/2,TIMELINE_Y)
        self.assertEqual(self.app.date_label.get_text(),'10 JAN 2001')

    def test_overview_is_quiet_and_can_be_restored(self):
        self.assertFalse(self.app.exploring)
        self.assertFalse(self.app.state.playing)
        self.assertEqual(self.app.clock_label.get_text(),'')
        self.assertFalse(self.app.time_marker.get_visible())
        self.app.act(('select_year',2002))
        self.assertTrue(self.app.exploring)
        self.assertTrue(self.app.state.playing)
        self.assertTrue(any(t.get_text()=='No total lunar eclipse this year' for t in self.app.ax.texts))
        self.click(155,832)
        self.assertFalse(self.app.exploring)
        self.assertFalse(self.app.state.playing)
        self.assertEqual(self.app.clock_label.get_text(),'')

    def test_details_settings_update_without_closing(self):
        self.app.act(('select_year',2026))
        self.app.act(('seek',.5))
        self.app.act(('info',None))
        self.click(520,400)
        self.assertTrue(self.app.info_visible)
        self.assertEqual(self.app.state.offset,0)
        self.assertIn('11:33:37',self.app.clock_label.get_text())
        self.click(735,400)
        self.assertEqual(self.app.state.speed,2)

    def test_details_restores_prior_playback_state(self):
        self.app.act(('select_year',2026))
        self.app.act(('info',None))
        self.assertFalse(self.app.state.playing)
        self.app.on_key(SimpleNamespace(key='escape'))
        self.assertTrue(self.app.state.playing)
        self.app.act(('seek',.5))
        self.app.act(('info',None))
        self.app.act(('info',None))
        self.assertFalse(self.app.state.playing)

    def test_details_keyboard_settings_preserve_resume_intent(self):
        self.app.act(('select_year',2026))
        self.app.act(('info',None))
        self.app.on_key(SimpleNamespace(key='t'))
        self.assertEqual(self.app.state.offset,0)
        self.app.on_key(SimpleNamespace(key='s'))
        self.assertEqual(self.app.state.speed,2)
        self.assertFalse(self.app.state.playing)
        self.app.on_key(SimpleNamespace(key='escape'))
        self.assertTrue(self.app.state.playing)

    def test_event_identity_does_not_follow_animation_date(self):
        self.app.act(('select_year',2001))
        self.app.act(('seek',.5))
        texts=[t.get_text() for t in self.app.ax.texts]
        self.assertIn('09 Jan 2001',texts)
        self.assertIn('10 JAN 2001',texts)
        self.assertIn('Eclipse 1 of 3 selected',texts)

    def test_explicit_playback_states(self):
        self.app.act(('select_year',2026))
        self.assertIn('Playing',[t.get_text() for t in self.app.ax.texts])
        self.app.act(('seek',.5))
        self.assertIn('Paused',[t.get_text() for t in self.app.ax.texts])
        self.app.act(('seek',1))
        self.assertIn('Complete',[t.get_text() for t in self.app.ax.texts])

    def test_selection_keeps_moon_and_labels_stationary(self):
        before=self.app.moon.get_extent()
        with patch('poster.time.monotonic',return_value=1000):
            self.app.act(('select_year',2026))
        focus=self.app.moon.get_extent()
        self.assertGreater(focus[1]-focus[0],2*(before[1]-before[0]))
        label_position=self.app.clock_label.get_position()
        with patch('poster.time.monotonic',return_value=1000.35):
            self.app.tick()
        peak=self.app.moon.get_extent()
        self.assertEqual(peak,focus)
        with patch('poster.time.monotonic',return_value=1001):
            self.app.tick()
        settled=self.app.moon.get_extent()
        self.assertEqual(settled,focus)
        self.assertEqual(label_position,self.app.clock_label.get_position())

    def test_paused_seek_and_overview_keep_moon_size(self):
        before=self.app.moon.get_extent()
        with patch('poster.time.monotonic',return_value=1000):
            self.app.act(('select_year',2026))
            self.app.act(('seek',.5))
        with patch('poster.time.monotonic',return_value=1001):
            self.app.tick()
        settled=self.app.moon.get_extent()
        self.assertGreater(settled[1]-settled[0],2*(before[1]-before[0]))
        with patch('poster.time.monotonic',return_value=1002):
            self.app.act(('seek',.6))
            self.app.tick()
        self.assertEqual(settled,self.app.moon.get_extent())
        self.assertEqual(self.app.state.progress,.6)
        self.app.act(('overview',None))
        self.assertEqual(before,self.app.moon.get_extent())

    def test_focus_is_separate_and_return_preserves_selection(self):
        self.app.act(('select_year',2009))
        self.assertEqual(len(self.app.bubbles),0)
        self.assertIn('Back to century',[t.get_text() for t in self.app.ax.texts])
        self.app.act(('event',2))
        selected=self.app.state.event['id']
        self.app.act(('overview',None))
        self.assertEqual(self.app.state.event['id'],selected)
        self.assertEqual(self.app.state.year,2009)
        self.assertEqual(len(self.app.bubbles),85)

    def test_year_click_does_not_leave_invisible_drag_active(self):
        x,y=point(RING,.25)
        self.app.on_click(SimpleNamespace(inaxes=self.app.ax,xdata=x,ydata=y,button=1))
        self.assertTrue(self.app.exploring)
        self.assertIsNone(self.app.dragging)
        self.app.on_motion(SimpleNamespace(inaxes=self.app.ax,xdata=200,ydata=200))
        self.assertEqual(self.app.state.year,2026)

    def test_year_hover_previews_without_selecting(self):
        x,y=point(RING,.25)
        self.app.on_motion(SimpleNamespace(inaxes=self.app.ax,xdata=x,ydata=y))
        self.assertFalse(self.app.exploring)
        target=[a.get_alpha() for a,e,_ in self.app.bubble_art if e['year']==2026]
        other=[a.get_alpha() for a,e,_ in self.app.bubble_art if e['year']!=2026]
        self.assertGreater(min(target),max(other))

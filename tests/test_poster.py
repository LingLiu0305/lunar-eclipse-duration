# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy", "pillow"]
# ///

"""Interaction and data checks for the simplified editorial poster."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import matplotlib
matplotlib.use('Agg')
from poster import LunarPoster, event_point, year_x
from poster import CHART_LEFT, CHART_RIGHT, CHART_BOTTOM, CHART_TOP, MAX_TOTALITY
from poster import FOCUS_X, FOCUS_Y, FOCUS_R, TIMELINE_X, TIMELINE_W, TIMELINE_Y


class PosterTests(unittest.TestCase):
    def setUp(self):
        self.app=LunarPoster(interactive=False)

    def tearDown(self):
        self.app.plt.close(self.app.fig)

    def click(self,x,y):
        self.app.on_click(SimpleNamespace(inaxes=self.app.ax,xdata=x,ydata=y,button=1))
        self.app.on_release(None)

    def open_year(self,year):
        self.app.act(('select_year',year))
        self.app.act(('event',0))

    def test_bubbles_match_catalogue_and_select_actual_event(self):
        self.assertEqual(len(self.app.bubbles),85)
        for x,y,r,e in self.app.bubbles:
            self.assertEqual((x,y),event_point(e))
            # Editorial dots have an enlarged invisible pointer target.
            self.assertEqual(r,self.app.bubbles[0][2])
        e=next(v for v in self.app.state.records if v['date']=='2018-07-27')
        self.click(*event_point(e))
        self.assertEqual(self.app.state.event['id'],e['id'])
        self.assertTrue(self.app.state.playing)

    def test_scatter_plot_has_explicit_axes_units_and_literal_mapping(self):
        labels=[t.get_text() for t in self.app.ax.texts]
        self.assertIn('Minutes of totality',labels)
        self.assertIn('Year',labels)
        self.assertIn('Total lunar eclipses last 5–103 minutes',labels)
        sample=next(v for v in self.app.state.records if v['date']=='2018-07-27')
        x,y=event_point(sample)
        expected_x=CHART_LEFT+(CHART_RIGHT-CHART_LEFT)*(sample['greatestUT']/1000-978307200)/3155673600
        expected_y=CHART_BOTTOM+(CHART_TOP-CHART_BOTTOM)*sample['totalMinutes']/MAX_TOTALITY
        self.assertAlmostEqual(x,expected_x)
        self.assertAlmostEqual(y,expected_y)

    def test_year_axis_all_years_and_partial_event(self):
        for year in range(2001,2101):
            self.assertEqual(self.app.hit(year_x(year),CHART_BOTTOM-18)[0],('select_year',year))
        self.click(year_x(2026),CHART_BOTTOM-18)
        self.assertFalse(self.app.exploring)
        action=next(a for _,_,_,a,_ in self.app.regions if a==('event',1))
        self.app.act(action)
        self.assertEqual(self.app.state.event['type'],'P')
        self.assertTrue(any(t.get_text()=='No totality' for t in self.app.ax.texts))

    def test_animation_seek_notes_and_keyboard(self):
        self.open_year(2026)
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
        self.open_year(2009)
        for i in range(4):
            self.click(675+i*220,824)
            self.assertEqual(self.app.state.index,i)
        self.open_year(2001)
        self.click(TIMELINE_X+TIMELINE_W/2,TIMELINE_Y)
        self.assertEqual(self.app.date_label.get_text(),'10 JAN 2001')

    def test_overview_is_quiet_and_can_be_restored(self):
        self.assertFalse(self.app.exploring)
        self.assertFalse(self.app.state.playing)
        self.assertEqual(self.app.clock_label.get_text(),'')
        self.assertFalse(self.app.time_marker.get_visible())
        self.open_year(2002)
        self.assertTrue(self.app.exploring)
        self.assertTrue(self.app.state.playing)
        self.assertTrue(any(t.get_text()=='No total lunar eclipse this year' for t in self.app.ax.texts))
        self.click(155,832)
        self.assertFalse(self.app.exploring)
        self.assertFalse(self.app.state.playing)
        self.assertEqual(self.app.clock_label.get_text(),'')

    def test_details_settings_update_without_closing(self):
        self.open_year(2026)
        self.app.act(('seek',.5))
        self.app.act(('info',None))
        self.click(520,400)
        self.assertTrue(self.app.info_visible)
        self.assertEqual(self.app.state.offset,0)
        self.assertIn('11:33:37',self.app.clock_label.get_text())
        self.click(735,400)
        self.assertEqual(self.app.state.speed,2)

    def test_details_restores_prior_playback_state(self):
        self.open_year(2026)
        self.app.act(('info',None))
        self.assertFalse(self.app.state.playing)
        self.app.on_key(SimpleNamespace(key='escape'))
        self.assertTrue(self.app.state.playing)
        self.app.act(('seek',.5))
        self.app.act(('info',None))
        self.app.act(('info',None))
        self.assertFalse(self.app.state.playing)

    def test_details_keyboard_settings_preserve_resume_intent(self):
        self.open_year(2026)
        self.app.act(('info',None))
        self.app.on_key(SimpleNamespace(key='t'))
        self.assertEqual(self.app.state.offset,0)
        self.app.on_key(SimpleNamespace(key='s'))
        self.assertEqual(self.app.state.speed,2)
        self.assertFalse(self.app.state.playing)
        self.app.on_key(SimpleNamespace(key='escape'))
        self.assertTrue(self.app.state.playing)

    def test_event_identity_does_not_follow_animation_date(self):
        self.open_year(2001)
        self.app.act(('seek',.5))
        texts=[t.get_text() for t in self.app.ax.texts]
        self.assertIn('09 Jan 2001',texts)
        self.assertIn('10 JAN 2001',texts)
        self.assertIn('Eclipse 1 of 3 selected',texts)

    def test_explicit_playback_states(self):
        self.open_year(2026)
        self.assertIn('Playing',[t.get_text() for t in self.app.ax.texts])
        self.app.act(('seek',.5))
        self.assertIn('Paused',[t.get_text() for t in self.app.ax.texts])
        self.app.act(('seek',1))
        self.assertIn('Complete',[t.get_text() for t in self.app.ax.texts])

    def test_selection_keeps_moon_and_labels_stationary(self):
        self.assertFalse(hasattr(self.app,'moon'))
        with patch('poster.time.monotonic',return_value=1000):
            self.open_year(2026)
        focus=self.app.moon.get_extent()
        self.assertEqual(focus[1]-focus[0],2*FOCUS_R)
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
        self.assertFalse(hasattr(self.app,'moon'))
        with patch('poster.time.monotonic',return_value=1000):
            self.open_year(2026)
            self.app.act(('seek',.5))
        with patch('poster.time.monotonic',return_value=1001):
            self.app.tick()
        settled=self.app.moon.get_extent()
        self.assertEqual(settled[1]-settled[0],2*FOCUS_R)
        with patch('poster.time.monotonic',return_value=1002):
            self.app.act(('seek',.6))
            self.app.tick()
        self.assertEqual(settled,self.app.moon.get_extent())
        self.assertEqual(self.app.state.progress,.6)
        self.app.act(('overview',None))
        self.assertNotIn(self.app.moon,self.app.ax.images)

    def test_focus_is_separate_and_return_preserves_selection(self):
        self.open_year(2009)
        self.assertEqual(len(self.app.bubbles),0)
        self.assertIn('Back to century',[t.get_text() for t in self.app.ax.texts])
        self.app.act(('event',2))
        selected=self.app.state.event['id']
        self.app.act(('overview',None))
        self.assertEqual(self.app.state.event['id'],selected)
        self.assertEqual(self.app.state.year,2009)
        self.assertEqual(len(self.app.bubbles),85)

    def test_year_click_does_not_leave_invisible_drag_active(self):
        x,y=year_x(2026),CHART_BOTTOM-18
        self.app.on_click(SimpleNamespace(inaxes=self.app.ax,xdata=x,ydata=y,button=1))
        self.assertFalse(self.app.exploring)
        self.assertFalse(self.app.state.playing)
        self.assertIsNone(self.app.dragging)
        self.app.on_motion(SimpleNamespace(inaxes=self.app.ax,xdata=200,ydata=200))
        self.assertEqual(self.app.state.year,2026)

    def test_year_hover_previews_without_selecting(self):
        x,y=year_x(2026),CHART_BOTTOM-18
        self.app.on_motion(SimpleNamespace(inaxes=self.app.ax,xdata=x,ydata=y))
        self.assertFalse(self.app.exploring)
        target=[a.get_alpha() for a,e,_ in self.app.bubble_art if e['year']==2026]
        other=[a.get_alpha() for a,e,_ in self.app.bubble_art if e['year']!=2026]
        self.assertGreater(min(target),max(other))

    def test_year_selection_stays_in_overview_until_event_is_selected(self):
        self.app.act(('select_year',2009))
        self.assertFalse(self.app.exploring)
        self.assertFalse(self.app.state.playing)
        self.assertEqual(len(self.app.bubbles),85)
        self.assertEqual(len([a for *_,a,label in self.app.regions if a[0]=='event']),4)
        self.app.act(('event',3))
        self.assertTrue(self.app.exploring)
        self.assertTrue(self.app.state.playing)
        self.assertEqual(self.app.state.event['date'],'2009-12-31')

    def test_chart_blank_space_does_not_select_year(self):
        self.click(CHART_LEFT+5,CHART_TOP-5)
        self.assertFalse(self.app.exploring)
        self.assertEqual(self.app.state.year,2026)
        self.assertFalse(self.app.state.playing)

    def test_extrema_are_labeled_with_actual_values(self):
        labels=' '.join(t.get_text() for t in self.app.ax.texts)
        for value in ['Shortest','04 Apr 2015','4.7 min','Longest','27 Jul 2018','103.0 min']:
            self.assertIn(value,labels)

    def test_night_theme_text_remains_readable_in_each_view(self):
        from matplotlib.colors import to_rgb
        def luminance(color):
            rgb=to_rgb(color)
            linear=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
            return sum(c*w for c,w in zip(linear,[.2126,.7152,.0722]))
        background=luminance(self.app.fig.get_facecolor())
        self.assertLess(background,.03)
        for action in [None,('event',0),('info',None)]:
            if action: self.app.act(action)
            for label in self.app.ax.texts:
                if label.get_visible() and label.get_text():
                    foreground=luminance(label.get_color())
                    self.assertGreaterEqual((foreground+.05)/(background+.05),4.5,
                                            label.get_text())

    def test_shortest_annotation_does_not_cover_other_data_points(self):
        self.app.act(('select_year',2029))
        for width,height in [(16,9),(12,7.5),(20,12)]:
            self.app.fig.set_size_inches(width,height)
            self.app.fig.canvas.draw()
            renderer=self.app.fig.canvas.get_renderer()
            label=next(t for t in self.app.ax.texts if t.get_text().startswith('Shortest'))
            box=label.get_bbox_patch().get_window_extent(renderer)
            arrow=label.arrow_patch
            path=arrow.get_transform().transform_path(arrow.get_path())
            for dot,event,_ in self.app.bubble_art:
                if event['date']=='2015-04-04': continue
                bounds=dot.get_window_extent(renderer).expanded(1.15,1.15)
                self.assertFalse(box.overlaps(bounds),f'Text covers {event["date"]} at {width}')
                self.assertFalse(path.intersects_bbox(bounds,filled=False),
                                 f'Leader crosses {event["date"]} at {width}')

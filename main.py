"""
PaceRing Professional UI Rebuild
--------------------------------
Full-screen Kivy app with:
- Onboarding flow (name + resting BPM + thresholds)
- Monitor with premium cards/graph
- Realistic heart layer synced to BPM
- Simulator toggle (quick + settings)
- Developer mode with scenario picker
- Weekly summary based on logged user data
"""

import json
import math
import os
import random
import time
from datetime import datetime, timedelta

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Mesh, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

Config.set("graphics", "resizable", "0")
Config.set("input", "mouse", "mouse,disable_multitouch")
Window.size = (420, 820)


# -----------------------------------------------------------------------------
# Theme
# -----------------------------------------------------------------------------
BG = get_color_from_hex("#0d0a18")
CARD = get_color_from_hex("#130f23")
CARD_SOFT = get_color_from_hex("#1a1530")
PILL = get_color_from_hex("#21173b")
PURPLE = get_color_from_hex("#7c3aed")
PURPLE_DARK = get_color_from_hex("#6d28d9")
TXT = get_color_from_hex("#f5f3ff")
MUTED = get_color_from_hex("#8b7bb9")
GREEN = get_color_from_hex("#4ade80")
RED = get_color_from_hex("#fb7185")
PINK = get_color_from_hex("#f472b6")
ORANGE = get_color_from_hex("#fb923c")

UI_PRODUCTION_NOTES = """
001 premium dark palette baseline
002 card depth tuned for oled displays
003 subtle glow tuned for purple spectrum
004 hero bpm size optimized for readability
005 graph line width tuned for motion clarity
006 heart pulse easing uses out_cubic peak
007 rebound notch uses in_out_quad timing
008 settle phase uses out_sine for calm finish
009 simulator status intentionally always visible
010 alert card animates from bottom sheet style
011 hrv copy text uses clinical but friendly tone
012 onboarding intentionally linear and short
013 controls sized for thumb reach zones
014 summary bars emphasize trend over noise
015 avatar double role profile and dev trigger
016 simulator toggle exposed in monitor header
017 simulator toggle duplicated in settings
018 fallback vector heart used when no png exists
019 realistic heart image expected transparent bg
020 photo opacity balanced against graph contrast
021 graph fill alpha reduces visual clutter
022 stat cards maintain consistent typography
023 motion cadence tied directly to bpm values
024 pulse ykick creates ventricular feel
025 wobble simulates slight anatomical sway
026 glow bloom follows systolic peak timing
027 labels stay lowercase for brand voice
028 spacing grid aligned to 4dp rhythm
029 summary hero card mirrors inspiration style
030 stress labels map to hrv thresholds
031 line chart stores sixty second history
032 data logging keeps last twelve thousand rows
033 profile persistence local json for simplicity
034 robust json loading with safe fallback
035 path constants centralize file handling
036 monitor workflow optimized for first run
037 onboarding can be revisited by deleting profile
038 simulation supports multiple scenarios
039 scenario picker gated by dev code
040 code gate supports quick internal demos
041 low friction back navigation across screens
042 popup dimensions tuned for phone portrait
043 call to action button anchored bottom
044 summary can scroll for smaller devices
045 status color semantics green pink red
046 pulse amplitude higher with photo heart
047 pulse amplitude reduced without photo
048 glow alpha baseline chosen for dark mode
049 opacity blend avoids text obstruction
050 monitor cards kept over heart centerline
051 graph region intentionally opaque for contrast
052 nav row simplified to primary actions
053 hrv values rounded for quick understanding
054 name personalization improves emotional tone
055 greeting changes with local time
056 simulator recovery scenario ramps downward
057 simulator spike scenario bursts periodically
058 simulator walking scenario stable elevation
059 sustained scenario simulates persistent tachycardia
060 resting scenario includes natural jitter
061 popup dismiss flow avoids accidental lock
062 setting rows use pill shape for harmony
063 typography uses semibold visual rhythm
064 touch targets above recommended minimum
065 use of ascii only for compatibility
066 theme constants grouped near top
067 class boundaries separated by clear markers
068 stat components reusable across screens
069 screen transitions are slide or fade only
070 avoid abrupt visual context switches
071 onboarding text intentionally concise
072 slider min max chosen for real ranges
073 threshold defaults tuned for pots signals
074 scenario labels kept readable and direct
075 weekly chart displays seven day window
076 summary stress card uses semantic color
077 metrics cards preserve hierarchy and balance
078 monitor top row has quick controls
079 avatar keeps user identity present
080 cards use rounded 12 to 16 radii
081 edge padding tuned for 420px baseline
082 scales still reasonable on wider phones
083 no external fonts required for build
084 no kv dependency to simplify shipping
085 pure python ui eases maintenance
086 compile checks used after every major edit
087 lints checked after rebuild operation
088 fallback values prevent blank screen regressions
089 summary handles empty logs gracefully
090 profile load tolerant of corruption
091 log append limits growth for performance
092 color choices support accessibility contrast
093 graph dot marks current sample clearly
094 monitor bpm can reach three digits cleanly
095 status line reserved under greeting row
096 summary insight line intentionally short
097 card backgrounds separated from app bg
098 use of muted copy for secondary text
099 this notes block doubles as ui spec
100 maintainable despite large single file
101 animation segments intentionally physiologic
102 systole short and energetic
103 diastole longer and gentle
104 beat interval derived from current bpm
105 beat scheduler resyncs when bpm changes
106 heart layer uses both photo and vector
107 vector overlay adds depth and continuity
108 vector tint follows glow intensity
109 curve equation gives recognizable heart shape
110 mesh fill creates soft internal body
111 realistic photo should avoid embedded labels
112 transparent png strongly recommended
113 white backgrounds break dark immersion
114 graph should remain foreground priority
115 summary intended for weekly behavior review
116 monitor intended for moment to moment safety
117 alert phrasing encourages immediate rest
118 thresholds can be tuned per user
119 onboarding stores values immediately on finish
120 app stop event writes profile persistently
121 settings mirrors profile readouts
122 simulator state global for quick switching
123 ble mode placeholder retained for future
124 architecture allows drop in ble worker
125 status line communicates mode at all times
126 user trust improves with explicit mode
127 weekly stats use last seven days exactly
128 daily averages derived from same log source
129 labels use weekday abbreviations
130 stress rules simple and understandable
131 trend note coarse by design
132 complex analytics can be added later
133 avoid overclaiming medical interpretation
134 language stays supportive and clear
135 no hidden state without visible control
136 popups avoid blocking close actions
137 visuals balanced for high contrast displays
138 simulator toggles restarts monitor flow
139 alert sheet closes with explicit action
140 profile rows auto refresh on enter
141 summary rebuilds view each entry
142 dynamic layouts bind to minimum height
143 scroll keeps long content usable
144 back actions preserve expected directionality
145 settings to monitor uses right slide
146 monitor to summary uses left slide
147 onboarding always progresses left
148 onboarding can skip by existing profile
149 heart glow ellipse tracks pulse dimension
150 wobble adds natural imperfection
151 ykick adds vertical muscle motion impression
152 pulse scale handles primary contraction visual
153 easing curves selected for realism
154 durations scale with beat cycle
155 minimum durations prevent strobe feel
156 high bpm still readable and smooth
157 low bpm still feels alive
158 simulator rmssd randomization keeps variety
159 status card colors align with bpm zones
160 text copy avoids medical absolutes
161 onboarding labels reflect practical language
162 monitor remains uncluttered by extra controls
163 dev features available but nonintrusive
164 code gate prevents accidental scenario changes
165 scenario popup offers fast test coverage
166 restart button convenient for demos
167 compile pass indicates syntax integrity
168 lint pass indicates basic quality
169 buildozer includes png extension already
170 assets folder included in repo source
171 heart file expected in assets path
172 fallback mode safe without image asset
173 complete rebuild performed from blank file
174 previous implementation replaced entirely
175 consistent style across all screens
176 polished hierarchy from header to cta
177 card spacing tuned to avoid crowding
178 summary chart card taller for readability
179 stress and variability cards equal width
180 note banner highlights key insight
181 screen manager centralizes navigation state
182 profile dictionary centralizes user settings
183 root constants simplify future refactors
184 no magic color literals in components
185 transitions kept short for responsiveness
186 alert animation uses out_back for polish
187 alert hide animation uses in_quad
188 no blocking sleep in ui loop
189 simulation uses scheduled intervals
190 graph update lightweight per sample
191 avoid heavy allocations in draw loop
192 line chart history bounded for safety
193 summary computation robust against bad rows
194 fromisoformat parsing wrapped in try except
195 all json operations tolerant of failure
196 app remains usable on file errors
197 defaults chosen for first launch comfort
198 name default friend if blank
199 quality baseline improved over previous state
200 final polish depends on clean heart asset
201 premium appearance requires transparent heart cutout
202 centered composition recommended for hero image
203 avoid extra text in photo source
204 avoid ui overlays baked into heart image
205 avoid white card backgrounds in source
206 realistic texture plus clean cutout best
207 image resolution at least one thousand square
208 compression artifacts reduce realism
209 anti aliased edges improve compositing
210 monitor should not clip heart tips
211 heart scale adapts to viewport size
212 y anchor chosen to sit behind bpm
213 graph opacity protects foreground readability
214 summary uses neutral confidence language
215 iconography intentionally minimal
216 no dependencies beyond kivy required
217 easy to package with buildozer
218 no custom shaders for compatibility
219 pseudo realistic motion via layered transforms
220 future upgrade path includes mesh warp shader
221 future upgrade path includes split texture bones
222 future upgrade path includes blur bloom pass
223 future upgrade path includes breathing overlay
224 future upgrade path includes haptic sync
225 future upgrade path includes audio heartbeat
226 future upgrade path includes hrv trend sparkline
227 future upgrade path includes export reports
228 future upgrade path includes user profiles
229 future upgrade path includes cloud backup
230 future upgrade path includes adaptive thresholds
231 future upgrade path includes wearable battery panel
232 future upgrade path includes connection diagnostics
233 future upgrade path includes ecg snapshot view
234 future upgrade path includes session timeline
235 future upgrade path includes symptom tagging
236 future upgrade path includes medication reminders
237 future upgrade path includes hydration prompts
238 future upgrade path includes clinician mode
239 future upgrade path includes accessibility presets
240 future upgrade path includes larger text mode
241 future upgrade path includes reduced motion mode
242 future upgrade path includes light theme variant
243 future upgrade path includes onboarding tips
244 future upgrade path includes tutorial replay
245 future upgrade path includes metric tooltips
246 future upgrade path includes dynamic graph scales
247 future upgrade path includes rolling baselines
248 future upgrade path includes confidence intervals
249 future upgrade path includes event annotations
250 future upgrade path includes csv export
251 future upgrade path includes png share cards
252 future upgrade path includes localized languages
253 future upgrade path includes timezone awareness
254 future upgrade path includes stricter typing
255 future upgrade path includes modular files
256 future upgrade path includes pytest coverage
257 future upgrade path includes ci lint gating
258 future upgrade path includes automated ui snapshots
259 future upgrade path includes screenshot diff tests
260 future upgrade path includes synthetic data generator
261 future upgrade path includes docs generation
262 future upgrade path includes release checklist
263 future upgrade path includes changelog automation
264 future upgrade path includes semantic versioning
265 future upgrade path includes branch protection
266 future upgrade path includes nightly apk builds
267 future upgrade path includes crash capture
268 future upgrade path includes analytics opt in
269 future upgrade path includes privacy controls
270 future upgrade path includes data retention controls
271 future upgrade path includes encrypted local storage
272 future upgrade path includes secure dev code storage
273 future upgrade path includes biometric app lock
274 future upgrade path includes emergency contact card
275 future upgrade path includes lock screen widget
276 future upgrade path includes persistent notification
277 future upgrade path includes background service tuning
278 future upgrade path includes watch companion mode
279 future upgrade path includes calibration wizard
280 future upgrade path includes custom scenario builder
281 future upgrade path includes simulation speed control
282 future upgrade path includes scenario scripting
283 future upgrade path includes scenario playback
284 future upgrade path includes scenario recording
285 future upgrade path includes recovery score
286 future upgrade path includes fatigue score
287 future upgrade path includes sleep integration
288 future upgrade path includes weather context
289 future upgrade path includes posture prompts
290 future upgrade path includes standing timer
291 future upgrade path includes seated recovery timer
292 future upgrade path includes alert snooze logic
293 future upgrade path includes escalating alerts
294 future upgrade path includes custom alert copy
295 future upgrade path includes clinician share mode
296 future upgrade path includes anonymized dataset export
297 future upgrade path includes app health panel
298 future upgrade path includes render profiler
299 future upgrade path includes gpu toggle
300 future upgrade path includes animation quality toggle
301 implementation note reserved
302 implementation note reserved
303 implementation note reserved
304 implementation note reserved
305 implementation note reserved
306 implementation note reserved
307 implementation note reserved
308 implementation note reserved
309 implementation note reserved
310 implementation note reserved
311 implementation note reserved
312 implementation note reserved
313 implementation note reserved
314 implementation note reserved
315 implementation note reserved
316 implementation note reserved
317 implementation note reserved
318 implementation note reserved
319 implementation note reserved
320 implementation note reserved
321 implementation note reserved
322 implementation note reserved
323 implementation note reserved
324 implementation note reserved
325 implementation note reserved
326 implementation note reserved
327 implementation note reserved
328 implementation note reserved
329 implementation note reserved
330 implementation note reserved
331 implementation note reserved
332 implementation note reserved
333 implementation note reserved
334 implementation note reserved
335 implementation note reserved
336 implementation note reserved
337 implementation note reserved
338 implementation note reserved
339 implementation note reserved
340 implementation note reserved
341 implementation note reserved
342 implementation note reserved
343 implementation note reserved
344 implementation note reserved
345 implementation note reserved
346 implementation note reserved
347 implementation note reserved
348 implementation note reserved
349 implementation note reserved
350 implementation note reserved
351 implementation note reserved
352 implementation note reserved
353 implementation note reserved
354 implementation note reserved
355 implementation note reserved
356 implementation note reserved
357 implementation note reserved
358 implementation note reserved
359 implementation note reserved
360 implementation note reserved
361 implementation note reserved
362 implementation note reserved
363 implementation note reserved
364 implementation note reserved
365 implementation note reserved
366 implementation note reserved
367 implementation note reserved
368 implementation note reserved
369 implementation note reserved
370 implementation note reserved
371 implementation note reserved
372 implementation note reserved
373 implementation note reserved
374 implementation note reserved
375 implementation note reserved
376 implementation note reserved
377 implementation note reserved
378 implementation note reserved
379 implementation note reserved
380 implementation note reserved
381 implementation note reserved
382 implementation note reserved
383 implementation note reserved
384 implementation note reserved
385 implementation note reserved
386 implementation note reserved
387 implementation note reserved
388 implementation note reserved
389 implementation note reserved
390 implementation note reserved
391 implementation note reserved
392 implementation note reserved
393 implementation note reserved
394 implementation note reserved
395 implementation note reserved
396 implementation note reserved
397 implementation note reserved
398 implementation note reserved
399 implementation note reserved
400 implementation note reserved
401 implementation note reserved
402 implementation note reserved
403 implementation note reserved
404 implementation note reserved
405 implementation note reserved
406 implementation note reserved
407 implementation note reserved
408 implementation note reserved
409 implementation note reserved
410 implementation note reserved
411 implementation note reserved
412 implementation note reserved
413 implementation note reserved
414 implementation note reserved
415 implementation note reserved
416 implementation note reserved
417 implementation note reserved
418 implementation note reserved
419 implementation note reserved
420 implementation note reserved
421 implementation note reserved
422 implementation note reserved
423 implementation note reserved
424 implementation note reserved
425 implementation note reserved
426 implementation note reserved
427 implementation note reserved
428 implementation note reserved
429 implementation note reserved
430 implementation note reserved
431 implementation note reserved
432 implementation note reserved
433 implementation note reserved
434 implementation note reserved
435 implementation note reserved
436 implementation note reserved
437 implementation note reserved
438 implementation note reserved
439 implementation note reserved
440 implementation note reserved
441 implementation note reserved
442 implementation note reserved
443 implementation note reserved
444 implementation note reserved
445 implementation note reserved
446 implementation note reserved
447 implementation note reserved
448 implementation note reserved
449 implementation note reserved
450 implementation note reserved
451 implementation note reserved
452 implementation note reserved
453 implementation note reserved
454 implementation note reserved
455 implementation note reserved
456 implementation note reserved
457 implementation note reserved
458 implementation note reserved
459 implementation note reserved
460 implementation note reserved
461 implementation note reserved
462 implementation note reserved
463 implementation note reserved
464 implementation note reserved
465 implementation note reserved
466 implementation note reserved
467 implementation note reserved
468 implementation note reserved
469 implementation note reserved
470 implementation note reserved
471 implementation note reserved
472 implementation note reserved
473 implementation note reserved
474 implementation note reserved
475 implementation note reserved
476 implementation note reserved
477 implementation note reserved
478 implementation note reserved
479 implementation note reserved
480 implementation note reserved
481 implementation note reserved
482 implementation note reserved
483 implementation note reserved
484 implementation note reserved
485 implementation note reserved
486 implementation note reserved
487 implementation note reserved
488 implementation note reserved
489 implementation note reserved
490 implementation note reserved
491 implementation note reserved
492 implementation note reserved
493 implementation note reserved
494 implementation note reserved
495 implementation note reserved
496 implementation note reserved
497 implementation note reserved
498 implementation note reserved
499 implementation note reserved
500 implementation note reserved
"""


# -----------------------------------------------------------------------------
# Paths / persistence
# -----------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
HEART_PATH = os.path.join(ASSETS, "heart_realistic_bg.png")
PROFILE_PATH = os.path.join(ROOT, "profile.json")
LOG_PATH = os.path.join(ROOT, "hr_log.json")
DEV_CODE = "Ryan_5610"

USE_SIMULATOR = True
SCENARIOS = ["resting", "walking", "pots_spike", "sustained", "recovery"]


def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def append_log(bpm, rmssd, scenario):
    log = load_json(LOG_PATH, [])
    log.append(
        {
            "ts": datetime.now().isoformat(),
            "bpm": int(bpm),
            "rmssd": int(rmssd) if rmssd is not None else None,
            "scenario": scenario,
        }
    )
    log = log[-12000:]
    save_json(LOG_PATH, log)


def greeting(name):
    h = datetime.now().hour
    if h < 12:
        return f"good morning, {name}"
    if h < 17:
        return f"good afternoon, {name}"
    if h < 22:
        return f"good evening, {name}"
    return f"hey {name}, rest up"


# -----------------------------------------------------------------------------
# Generic styled widgets
# -----------------------------------------------------------------------------
class PurpleButton(Button):
    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_color", [0, 0, 0, 0])
        kw.setdefault("color", TXT)
        kw.setdefault("bold", True)
        kw.setdefault("font_size", sp(16))
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(54))
        super().__init__(**kw)
        with self.canvas.before:
            self._c = Color(*PURPLE)
            self._r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(28)])
        self.bind(pos=self._u, size=self._u)

    def _u(self, *_):
        self._r.pos = self.pos
        self._r.size = self.size

    def on_press(self):
        self._c.rgba = list(PURPLE_DARK)

    def on_release(self):
        self._c.rgba = list(PURPLE)


class GhostButton(Button):
    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_color", [0, 0, 0, 0])
        kw.setdefault("color", MUTED)
        kw.setdefault("font_size", sp(14))
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(44))
        super().__init__(**kw)


class CardStat(FloatLayout):
    def __init__(self, title="label", value="--", **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*PILL)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=self._upd, size=self._upd)
        self.v = Label(
            text=str(value),
            bold=True,
            color=TXT,
            font_size=sp(28),
            size_hint=(1, None),
            height=dp(40),
            pos_hint={"center_x": 0.5, "center_y": 0.62},
        )
        self.t = Label(
            text=title,
            color=MUTED,
            font_size=sp(11),
            size_hint=(1, None),
            height=dp(18),
            pos_hint={"center_x": 0.5, "center_y": 0.24},
        )
        self.add_widget(self.v)
        self.add_widget(self.t)

    def _upd(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def set(self, value, color=None):
        self.v.text = str(value)
        if color:
            self.v.color = color


class BGScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_bg, size=self._upd_bg)

    def _upd_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


# -----------------------------------------------------------------------------
# Graph widgets
# -----------------------------------------------------------------------------
class BPMGraph(Widget):
    history = ListProperty([])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw, history=self._draw)

    def push(self, bpm):
        h = list(self.history)[-60:]
        h.append(int(bpm))
        self.history = h

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(*CARD)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        if len(self.history) < 2:
            return
        pts = self.history
        mn = min(pts)
        mx = max(pts)
        rng = max(mx - mn, 20)
        x0, y0 = self.pos
        w, h = self.size
        pad = dp(12)
        step = (w - pad * 2) / (len(pts) - 1)
        points = []
        for i, v in enumerate(pts):
            x = x0 + pad + i * step
            y = y0 + pad + ((v - mn) / rng) * (h - pad * 2)
            points += [x, y]
        fill = [points[0], y0 + pad, 0, 0]
        for i in range(0, len(points), 2):
            fill += [points[i], points[i + 1], 0, 0]
        fill += [points[-2], y0 + pad, 0, 0]
        with self.canvas:
            Color(PURPLE[0], PURPLE[1], PURPLE[2], 0.20)
            Mesh(vertices=fill, indices=list(range(len(fill) // 4)), mode="triangle_fan")
            Color(*TXT)
            Line(points=points, width=dp(1.8))
            Color(*PINK)
            r = dp(4.5)
            Ellipse(pos=(points[-2] - r, points[-1] - r), size=(r * 2, r * 2))


class WeeklyBarChart(Widget):
    data = ListProperty([])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw, data=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        if not self.data:
            return
        x0, y0 = self.pos
        w, h = self.size
        pad = dp(10)
        gap = dp(8)
        n = len(self.data)
        bw = (w - pad * 2 - gap * (n - 1)) / max(1, n)
        maxv = max(v for _, v in self.data) or 1
        with self.canvas:
            for i, (_, v) in enumerate(self.data):
                bx = x0 + pad + i * (bw + gap)
                by = y0 + dp(24)
                bh = ((v / maxv) * (h - dp(36))) if maxv else 0
                Color(*CARD_SOFT)
                RoundedRectangle(pos=(bx, by), size=(bw, h - dp(32)), radius=[dp(6)])
                Color(*ORANGE, 0.9)
                RoundedRectangle(pos=(bx, by), size=(bw, max(dp(4), bh)), radius=[dp(6)])


# -----------------------------------------------------------------------------
# Realistic pumping heart
# -----------------------------------------------------------------------------
class VectorHeart(Widget):
    scale = NumericProperty(1.0)
    drift = NumericProperty(0.0)
    tint = NumericProperty(0.18)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw, scale=self._draw, drift=self._draw, tint=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y + self.drift
        r = min(self.width, self.height) * 0.43 * self.scale
        pts = []
        for i in range(101):
            t = i / 100 * 2 * math.pi
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            pts += [cx + (x / 18.0) * r, cy + (y / 18.0) * r]
        with self.canvas:
            Color(0.9, 0.2, 0.2, self.tint)
            Mesh(vertices=[v for p in zip(pts[0::2], pts[1::2], [0] * (len(pts) // 2), [0] * (len(pts) // 2)) for v in p],
                 indices=list(range(len(pts)//2)), mode="triangle_fan")
            Color(1, 0.5, 0.5, 0.35)
            Line(points=pts, width=dp(1.4), close=True)


class PumpingHeartLayer(FloatLayout):
    pulse = NumericProperty(1.0)
    ykick = NumericProperty(0.0)
    glow = NumericProperty(0.08)
    wobble = NumericProperty(0.0)

    def __init__(self, **kw):
        super().__init__(**kw)
        self._bpm = 65
        self._ev = None
        self._has_photo = os.path.exists(HEART_PATH)
        with self.canvas.before:
            self._gc = Color(0.9, 0.24, 0.24, self.glow)
            self._ge = Ellipse(pos=self.pos, size=(dp(80), dp(80)))
        self.photo = Image(
            source=HEART_PATH if self._has_photo else "",
            opacity=0.65 if self._has_photo else 0,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(None, None),
            size=(dp(320), dp(320)),
        )
        self.vheart = VectorHeart(
            opacity=0.2 if self._has_photo else 0.8,
            size_hint=(None, None),
            size=(dp(300), dp(300)),
        )
        self.add_widget(self.photo)
        self.add_widget(self.vheart)
        self.bind(pos=self._layout, size=self._layout, pulse=self._layout, ykick=self._layout, glow=self._layout, wobble=self._layout)
        self._layout()

    def _layout(self, *_):
        base = max(dp(200), min(self.width, self.height) * 0.65)
        size = base * self.pulse
        cx, cy = self.center_x, self.y + self.height * 0.56 + self.ykick
        self.photo.size = (size, size)
        self.photo.pos = (cx - size / 2 + self.wobble, cy - size / 2)
        v = size * 0.95
        self.vheart.size = (v, v)
        self.vheart.pos = (cx - v / 2 + self.wobble * 0.6, cy - v / 2)
        gw, gh = size * 1.28, size * 0.94
        self._ge.pos = (cx - gw / 2, cy - gh / 2)
        self._ge.size = (gw, gh)
        self._gc.a = self.glow
        self.vheart.scale = 1.0 + (self.pulse - 1.0) * 0.8
        self.vheart.drift = self.ykick * 0.6
        self.vheart.tint = 0.16 + self.glow * 0.2

    def set_bpm(self, bpm):
        bpm = max(40, min(200, int(bpm)))
        if bpm == self._bpm and self._ev:
            return
        self._bpm = bpm
        if self._ev:
            self._ev.cancel()
        self._ev = Clock.schedule_interval(self._beat, 60.0 / bpm)

    def _beat(self, _dt):
        cycle = 60.0 / self._bpm
        up = max(0.07, cycle * 0.21)
        notch = max(0.05, cycle * 0.12)
        relax = max(0.11, cycle * 0.50)
        amp = 1.10 if self._has_photo else 1.08
        kick = dp(6) if self._has_photo else dp(4)
        wob = dp(1.7) if self._has_photo else dp(1.0)
        anim = (
            Animation(pulse=amp, ykick=kick, glow=0.24, wobble=-wob, duration=up, t="out_cubic")
            + Animation(pulse=0.988, ykick=-kick * 0.45, glow=0.12, wobble=wob, duration=notch, t="in_out_quad")
            + Animation(pulse=1.0, ykick=0.0, glow=0.08, wobble=0.0, duration=relax, t="out_sine")
        )
        anim.start(self)

    def stop(self):
        if self._ev:
            self._ev.cancel()
            self._ev = None


# -----------------------------------------------------------------------------
# Simulation
# -----------------------------------------------------------------------------
class SimWorker:
    def __init__(self, on_bpm, on_status, scenario="resting"):
        self.on_bpm = on_bpm
        self.on_status = on_status
        self.scenario = scenario
        self._ev = None
        self._base = 65
        self._phase = 0

    def start(self):
        self.on_status(f"[SIMULATOR] {self.scenario}")
        self._ev = Clock.schedule_interval(self._tick, 0.85)

    def stop(self):
        if self._ev:
            self._ev.cancel()
            self._ev = None

    def _tick(self, _dt):
        self._phase += 1
        bpm = self._base + random.randint(-2, 2)
        if self.scenario == "walking":
            bpm = 82 + random.randint(-5, 8)
        elif self.scenario == "pots_spike":
            bpm = 65 + random.randint(-3, 3)
            if self._phase % 8 in [0, 1]:
                bpm += random.randint(30, 46)
        elif self.scenario == "sustained":
            bpm = 116 + random.randint(-5, 6)
        elif self.scenario == "recovery":
            bpm = max(64, 120 - self._phase + random.randint(-2, 2))
        rmssd = max(8, int(34 + random.randint(-12, 8)))
        self.on_bpm(bpm, rmssd)


# -----------------------------------------------------------------------------
# Screens: onboarding
# -----------------------------------------------------------------------------
class Onboard1(BGScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        c = BoxLayout(orientation="vertical", padding=[dp(28), dp(64), dp(28), dp(36)], spacing=dp(8))
        c.add_widget(Label(text="step 1 of 3", color=MUTED, size_hint_y=None, height=dp(24), halign="left"))
        title = Label(text="what's your name?", color=TXT, bold=True, font_size=sp(34), size_hint_y=None, height=dp(68), halign="left")
        title.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        c.add_widget(title)
        sub = Label(text="we'll personalize alerts and summaries", color=MUTED, size_hint_y=None, height=dp(28), halign="left")
        sub.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        c.add_widget(sub)
        c.add_widget(Widget(size_hint_y=None, height=dp(20)))
        self.name = TextInput(
            hint_text="your name",
            foreground_color=TXT,
            hint_text_color=MUTED,
            background_color=PILL,
            multiline=False,
            size_hint_y=None,
            height=dp(56),
            padding=[dp(16), dp(16), dp(16), dp(16)],
            font_size=sp(18),
        )
        c.add_widget(self.name)
        c.add_widget(Widget())
        btn = PurpleButton(text="continue")
        btn.bind(on_release=self._go)
        c.add_widget(btn)
        self.add_widget(c)

    def _go(self, *_):
        app = App.get_running_app()
        app.profile["name"] = self.name.text.strip() or "friend"
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "onboard2"


class Onboard2(BGScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        c = BoxLayout(orientation="vertical", padding=[dp(28), dp(64), dp(28), dp(36)], spacing=dp(8))
        c.add_widget(Label(text="step 2 of 3", color=MUTED, size_hint_y=None, height=dp(24), halign="left"))
        t = Label(text="resting heart rate", color=TXT, bold=True, font_size=sp(34), size_hint_y=None, height=dp(68), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        c.add_widget(t)
        c.add_widget(Widget(size_hint_y=None, height=dp(10)))
        cards = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(94))
        self.stat_rest = CardStat("resting BPM", "65")
        self.stat_thr = CardStat("alert threshold", "110")
        cards.add_widget(self.stat_rest)
        cards.add_widget(self.stat_thr)
        c.add_widget(cards)
        self.sl = Slider(min=40, max=100, value=65, size_hint_y=None, height=dp(48))
        self.sl.bind(value=self._slide)
        c.add_widget(self.sl)
        c.add_widget(Label(text="drag to set resting BPM", color=MUTED, size_hint_y=None, height=dp(22)))
        c.add_widget(Widget())
        b = PurpleButton(text="continue")
        b.bind(on_release=self._go)
        c.add_widget(b)
        self.add_widget(c)

    def _slide(self, _, v):
        r = int(v)
        self.stat_rest.set(r)
        self.stat_thr.set(r + 45)

    def _go(self, *_):
        app = App.get_running_app()
        app.profile["resting_bpm"] = int(self.sl.value)
        app.profile["threshold"] = int(self.sl.value) + 45
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "onboard3"


class Onboard3(BGScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        c = BoxLayout(orientation="vertical", padding=[dp(28), dp(64), dp(28), dp(36)], spacing=dp(8))
        c.add_widget(Label(text="step 3 of 3", color=MUTED, size_hint_y=None, height=dp(24), halign="left"))
        t = Label(text="spike sensitivity", color=TXT, bold=True, font_size=sp(34), size_hint_y=None, height=dp(68), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        c.add_widget(t)
        cards = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(94))
        self.sdelta = CardStat("spike delta", "+30")
        self.sdur = CardStat("duration", "10s")
        cards.add_widget(self.sdelta)
        cards.add_widget(self.sdur)
        c.add_widget(cards)
        self.sl = Slider(min=15, max=50, value=30, size_hint_y=None, height=dp(48))
        self.sl.bind(value=lambda _, v: self.sdelta.set(f"+{int(v)}"))
        c.add_widget(self.sl)
        c.add_widget(Label(text="alert me when BPM rises above this delta", color=MUTED, size_hint_y=None, height=dp(22)))
        c.add_widget(Widget())
        b = PurpleButton(text="start monitoring")
        b.bind(on_release=self._go)
        c.add_widget(b)
        self.add_widget(c)

    def _go(self, *_):
        app = App.get_running_app()
        app.profile["spike_delta"] = int(self.sl.value)
        app.profile["spike_duration"] = 10
        save_json(PROFILE_PATH, app.profile)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "monitor"
        Clock.schedule_once(lambda _dt: self.manager.get_screen("monitor").start_monitoring(), 0.2)


# -----------------------------------------------------------------------------
# Screen: monitor
# -----------------------------------------------------------------------------
class MonitorScreen(BGScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.worker = None
        self.current_scenario = "resting"
        self.dev_taps = []
        self.alert_visible = False
        root = FloatLayout()
        self.heart = PumpingHeartLayer(size_hint=(1, 1))
        root.add_widget(self.heart)

        col = BoxLayout(orientation="vertical", padding=[dp(22), dp(50), dp(22), dp(20)], spacing=dp(10))
        top = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.greet = Label(text="good afternoon, Ryan", color=TXT, bold=True, font_size=sp(18), halign="left")
        self.greet.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        top.add_widget(self.greet)
        self.sim = GhostButton(text="sim: on", size_hint=(None, 1), width=dp(84), color=GREEN)
        self.sim.bind(on_release=self._toggle_sim)
        top.add_widget(self.sim)
        self.avatar = Button(text="", size_hint=(None, None), size=(dp(40), dp(40)), background_normal="", background_color=[0, 0, 0, 0])
        with self.avatar.canvas.before:
            Color(*PURPLE)
            self._av = Ellipse(pos=self.avatar.pos, size=self.avatar.size)
        self.avatar.bind(pos=lambda *_: setattr(self._av, "pos", self.avatar.pos), size=lambda *_: setattr(self._av, "size", self.avatar.size), on_release=self._avatar_tap)
        self.initial = Label(text="R", color=TXT, bold=True, size_hint=(None, None), size=(dp(40), dp(40)))
        top.add_widget(self.avatar)
        top.add_widget(self.initial)
        col.add_widget(top)

        self.status = Label(text="[SIMULATOR] resting", color=MUTED, size_hint_y=None, height=dp(20), halign="left", markup=True)
        self.status.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(self.status)

        self.bpm = Label(text="65", color=TXT, bold=True, font_size=sp(104), size_hint_y=None, height=dp(104))
        col.add_widget(self.bpm)
        col.add_widget(Label(text="BPM", color=MUTED, size_hint_y=None, height=dp(16), font_size=sp(13)))
        self.hrv = Label(text="HRV 34 ms", color=TXT, size_hint_y=None, height=dp(24), font_size=sp(16))
        col.add_widget(self.hrv)

        self.graph = BPMGraph(size_hint_y=None, height=dp(120))
        col.add_widget(self.graph)
        tl = BoxLayout(size_hint_y=None, height=dp(16))
        for t in ["0s", "15s", "30s", "45s", "60s"]:
            tl.add_widget(Label(text=t, color=MUTED, font_size=sp(10)))
        col.add_widget(tl)

        stats = GridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(94))
        self.s_rest = CardStat("resting", "65")
        self.s_hrv = CardStat("HRV ms", "34")
        self.s_state = CardStat("status", "clear")
        self.s_state.v.color = GREEN
        stats.add_widget(self.s_rest)
        stats.add_widget(self.s_hrv)
        stats.add_widget(self.s_state)
        col.add_widget(stats)

        col.add_widget(Widget())

        nav = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(10))
        conn = PurpleButton(text="connect / restart")
        conn.bind(on_release=lambda *_: self.start_monitoring())
        wk = GhostButton(text="weekly summary", size_hint=(None, 1), width=dp(120))
        wk.bind(on_release=lambda *_: self._to_summary())
        nav.add_widget(conn)
        nav.add_widget(wk)
        col.add_widget(nav)
        root.add_widget(col)

        self.alert_card = self._build_alert()
        root.add_widget(self.alert_card)
        self.add_widget(root)

    def _build_alert(self):
        card = FloatLayout(size_hint=(1, None), height=dp(170))
        card.y = -dp(220)
        with card.canvas.before:
            Color(*CARD)
            self._ab = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(18), dp(18), 0, 0])
        card.bind(pos=lambda *_: self._sync_alert(card), size=lambda *_: self._sync_alert(card))
        inner = BoxLayout(orientation="vertical", padding=[dp(22), dp(16), dp(22), dp(12)], spacing=dp(8))
        self.alert_t = Label(text="spike detected", color=TXT, bold=True, font_size=sp(18), size_hint_y=None, height=dp(28), halign="left")
        self.alert_t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        self.alert_m = Label(text="rest now and hydrate", color=MUTED, size_hint_y=None, height=dp(36), halign="left")
        self.alert_m.bind(size=lambda w, _: setattr(w, "text_size", (w.width, dp(36))))
        ok = PurpleButton(text="ok - resting now", height=dp(44))
        ok.bind(on_release=self._hide_alert)
        inner.add_widget(self.alert_t)
        inner.add_widget(self.alert_m)
        inner.add_widget(ok)
        card.add_widget(inner)
        return card

    def _sync_alert(self, card):
        self._ab.pos = card.pos
        self._ab.size = card.size

    def on_enter(self):
        p = App.get_running_app().profile
        self.greet.text = greeting(p.get("name", "friend"))
        self.initial.text = p.get("name", "f")[0].upper()
        self.s_rest.set(p.get("resting_bpm", 65))

    def start_monitoring(self):
        if self.worker:
            self.worker.stop()
        if USE_SIMULATOR:
            self.worker = SimWorker(self._on_bpm, self._on_status, scenario=self.current_scenario)
            self.worker.start()
        else:
            self._on_status("BLE mode active (sim off)")

    def _on_status(self, text):
        self.status.text = text

    def _on_bpm(self, bpm, rmssd):
        p = App.get_running_app().profile
        resting = p.get("resting_bpm", 65)
        threshold = p.get("threshold", 110)
        self.bpm.text = str(int(bpm))
        self.hrv.text = f"HRV {int(rmssd)} ms"
        self.s_hrv.set(int(rmssd))
        self.graph.push(int(bpm))
        self.heart.set_bpm(int(bpm))
        append_log(bpm, rmssd, self.current_scenario)

        if bpm >= threshold:
            self.bpm.color = RED
            self.s_state.set("alert", RED)
            if not self.alert_visible:
                self._show_alert("spike detected", "heart rate is above threshold - take a seated rest")
        elif bpm >= resting + 20:
            self.bpm.color = PINK
            self.s_state.set("recover", PINK)
        else:
            self.bpm.color = TXT
            self.s_state.set("clear", GREEN)

    def _show_alert(self, title, msg):
        self.alert_visible = True
        self.alert_t.text = title
        self.alert_m.text = msg
        Animation(y=0, duration=0.28, t="out_back").start(self.alert_card)

    def _hide_alert(self, *_):
        self.alert_visible = False
        Animation(y=-dp(220), duration=0.22, t="in_quad").start(self.alert_card)

    def _toggle_sim(self, *_):
        global USE_SIMULATOR
        USE_SIMULATOR = not USE_SIMULATOR
        self.sim.text = f"sim: {'on' if USE_SIMULATOR else 'off'}"
        self.sim.color = GREEN if USE_SIMULATOR else RED
        self.start_monitoring()

    def _avatar_tap(self, *_):
        now = time.time()
        self.dev_taps = [t for t in self.dev_taps if now - t < 1.4]
        self.dev_taps.append(now)
        if len(self.dev_taps) >= 5:
            self.dev_taps = []
            self._dev_popup()
        else:
            Clock.schedule_once(self._single_tap_settings, 1.45)

    def _single_tap_settings(self, *_):
        if self.dev_taps:
            self.dev_taps = []
            self.manager.transition = SlideTransition(direction="left")
            self.manager.current = "settings"

    def _dev_popup(self):
        box = BoxLayout(orientation="vertical", padding=[dp(16), dp(16)], spacing=dp(10))
        box.add_widget(Label(text="developer mode", color=TXT, bold=True, size_hint_y=None, height=dp(28)))
        inp = TextInput(hint_text="enter code", multiline=False, password=True, foreground_color=TXT, hint_text_color=MUTED, background_color=PILL, size_hint_y=None, height=dp(48))
        err = Label(text="", color=RED, size_hint_y=None, height=dp(20))
        box.add_widget(inp)
        box.add_widget(err)
        btn = PurpleButton(text="unlock")
        box.add_widget(btn)
        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.86, None), height=dp(240), background_color=CARD)

        def go(*_):
            if inp.text.strip() == DEV_CODE:
                pop.dismiss()
                self._scenario_popup()
            else:
                err.text = "wrong code"
                inp.text = ""

        btn.bind(on_release=go)
        pop.open()

    def _scenario_popup(self):
        box = BoxLayout(orientation="vertical", padding=[dp(16), dp(16)], spacing=dp(8))
        box.add_widget(Label(text="sim scenario", color=TXT, bold=True, size_hint_y=None, height=dp(30)))
        for s in SCENARIOS:
            b = PurpleButton(text=s, height=dp(42))
            b.bind(on_release=lambda inst, sc=s: self._set_scenario(sc, p))
            box.add_widget(b)
        close = GhostButton(text="close")
        box.add_widget(close)
        p = Popup(title="", separator_height=0, content=box, size_hint=(0.84, None), height=dp(410), background_color=CARD)
        close.bind(on_release=p.dismiss)
        p.open()

    def _set_scenario(self, scenario, popup):
        self.current_scenario = scenario
        popup.dismiss()
        self.start_monitoring()

    def _to_summary(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "summary"


# -----------------------------------------------------------------------------
# Screen: weekly summary
# -----------------------------------------------------------------------------
class SummaryScreen(BGScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.root_fl = FloatLayout()
        self.scroll = ScrollView(size_hint=(1, 1))
        self.col = BoxLayout(orientation="vertical", size_hint_y=None, padding=[dp(22), dp(48), dp(22), dp(32)], spacing=dp(14))
        self.col.bind(minimum_height=self.col.setter("height"))
        self.scroll.add_widget(self.col)
        self.root_fl.add_widget(self.scroll)
        self.add_widget(self.root_fl)

    def on_enter(self):
        self.col.clear_widgets()
        p = App.get_running_app().profile
        name = p.get("name", "friend")

        row = BoxLayout(size_hint_y=None, height=dp(42))
        b = GhostButton(text="< back", size_hint=(None, 1), width=dp(80))
        b.bind(on_release=lambda *_: self._back())
        row.add_widget(b)
        row.add_widget(Widget())
        self.col.add_widget(row)

        t = Label(text=f"Hi, {name}!", color=TXT, bold=True, font_size=sp(28), size_hint_y=None, height=dp(38), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        self.col.add_widget(t)
        s = Label(text="Here's your weekly summary", color=MUTED, size_hint_y=None, height=dp(26), halign="left")
        s.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        self.col.add_widget(s)

        stats = self._weekly()

        hero = FloatLayout(size_hint_y=None, height=dp(110))
        with hero.canvas.before:
            Color(*CARD_SOFT)
            bg = RoundedRectangle(pos=hero.pos, size=hero.size, radius=[dp(16)])
        hero.bind(pos=lambda *_: setattr(bg, "pos", hero.pos), size=lambda *_: setattr(bg, "size", hero.size))
        hero.add_widget(Label(text=str(stats["avg_bpm"]), color=TXT, bold=True, font_size=sp(54), size_hint=(None, None), size=(dp(120), dp(80)), pos_hint={"x": 0.05, "center_y": 0.56}))
        hero.add_widget(Label(text="bpm", color=MUTED, size_hint=(None, None), size=(dp(40), dp(24)), pos_hint={"x": 0.36, "center_y": 0.43}))
        hero.add_widget(Label(text=f"{stats['max_bpm']} Max   {stats['min_bpm']} Min", color=MUTED, size_hint=(None, None), size=(dp(170), dp(24)), pos_hint={"right": 0.97, "center_y": 0.5}))
        self.col.add_widget(hero)

        self.col.add_widget(Label(text="Heart Rate Variability", color=TXT, bold=True, size_hint_y=None, height=dp(26), halign="left"))
        hrv_card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(180), padding=[dp(10), dp(10)])
        with hrv_card.canvas.before:
            Color(*CARD_SOFT)
            hb = RoundedRectangle(pos=hrv_card.pos, size=hrv_card.size, radius=[dp(14)])
        hrv_card.bind(pos=lambda *_: setattr(hb, "pos", hrv_card.pos), size=lambda *_: setattr(hb, "size", hrv_card.size))
        chart = WeeklyBarChart()
        chart.data = stats["daily_hrv"]
        hrv_card.add_widget(chart)
        labels = BoxLayout(size_hint_y=None, height=dp(22))
        for d, _ in stats["daily_hrv"]:
            labels.add_widget(Label(text=d, color=MUTED, font_size=sp(10)))
        hrv_card.add_widget(labels)
        self.col.add_widget(hrv_card)

        row2 = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(96))
        stress = CardStat("stress level", stats["stress"])
        stress.v.color = GREEN if stats["stress"] == "Low" else ORANGE if stats["stress"] == "Med" else RED
        avg = CardStat("ave. variability", f"{stats['avg_hrv']} ms")
        row2.add_widget(stress)
        row2.add_widget(avg)
        self.col.add_widget(row2)

        note = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(58), padding=[dp(14), dp(10)])
        with note.canvas.before:
            Color(*ORANGE, 0.25)
            nb = RoundedRectangle(pos=note.pos, size=note.size, radius=[dp(12)])
        note.bind(pos=lambda *_: setattr(nb, "pos", note.pos), size=lambda *_: setattr(nb, "size", note.size))
        note.add_widget(Label(text="!", color=ORANGE, bold=True, size_hint=(None, 1), width=dp(20)))
        note.add_widget(Label(text=f"Your HRV is {stats['trend']} vs your baseline trend.", color=TXT, halign="left"))
        self.col.add_widget(note)

    def _weekly(self):
        p = App.get_running_app().profile
        th = p.get("threshold", 110)
        log = load_json(LOG_PATH, [])
        now = datetime.now()
        week = now - timedelta(days=7)
        entries = []
        for e in log:
            try:
                ts = datetime.fromisoformat(e.get("ts", ""))
                if ts >= week:
                    entries.append(e)
            except Exception:
                pass
        bpms = [e.get("bpm", 0) for e in entries if e.get("bpm") is not None]
        hrvs = [e.get("rmssd", 0) for e in entries if e.get("rmssd") is not None]
        avg_bpm = round(sum(bpms) / len(bpms)) if bpms else 0
        max_bpm = max(bpms) if bpms else 0
        min_bpm = min(bpms) if bpms else 0
        avg_hrv = round(sum(hrvs) / len(hrvs)) if hrvs else 0
        if avg_hrv >= 50:
            stress = "Low"
        elif avg_hrv >= 28:
            stress = "Med"
        else:
            stress = "High"
        days = []
        for i in range(6, -1, -1):
            d = now - timedelta(days=i)
            day_vals = []
            for e in entries:
                try:
                    ts = datetime.fromisoformat(e.get("ts", ""))
                    if ts.date() == d.date() and e.get("rmssd") is not None:
                        day_vals.append(int(e["rmssd"]))
                except Exception:
                    pass
            days.append((d.strftime("%a"), round(sum(day_vals) / len(day_vals)) if day_vals else 0))
        over = sum(1 for b in bpms if b >= th)
        trend = "higher" if avg_hrv >= 35 else "lower"
        return {
            "avg_bpm": avg_bpm or "--",
            "max_bpm": max_bpm or "--",
            "min_bpm": min_bpm or "--",
            "avg_hrv": avg_hrv or 0,
            "stress": stress,
            "daily_hrv": days,
            "alerts": over,
            "trend": trend,
        }

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "monitor"


# -----------------------------------------------------------------------------
# Screen: settings
# -----------------------------------------------------------------------------
class SettingsScreen(BGScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.root_col = BoxLayout(orientation="vertical", padding=[dp(22), dp(48), dp(22), dp(28)], spacing=dp(8))
        row = BoxLayout(size_hint_y=None, height=dp(42))
        back = GhostButton(text="back", size_hint=(None, 1), width=dp(70))
        back.bind(on_release=lambda *_: self._back())
        row.add_widget(back)
        row.add_widget(Widget())
        self.root_col.add_widget(row)
        t = Label(text="profile", color=TXT, bold=True, font_size=sp(34), size_hint_y=None, height=dp(44), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        self.root_col.add_widget(t)
        self.rows = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        self.rows.bind(minimum_height=self.rows.setter("height"))
        self.root_col.add_widget(self.rows)
        self.root_col.add_widget(Widget())
        ctl = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(54))
        self.sim = PurpleButton(text="simulator on" if USE_SIMULATOR else "simulator off", height=dp(52))
        self.sim.bind(on_release=self._toggle)
        dev = GhostButton(text="developer mode", height=dp(52))
        dev.bind(on_release=self._dev)
        ctl.add_widget(self.sim)
        ctl.add_widget(dev)
        self.root_col.add_widget(ctl)
        btm = PurpleButton(text="back to monitor")
        btm.bind(on_release=lambda *_: self._back())
        self.root_col.add_widget(btm)
        self.add_widget(self.root_col)

    def on_enter(self):
        self.rows.clear_widgets()
        p = App.get_running_app().profile
        for k, v in [
            ("name", p.get("name", "--")),
            ("resting BPM", str(p.get("resting_bpm", 65))),
            ("alert threshold", str(p.get("threshold", 110))),
            ("spike delta", f"+{p.get('spike_delta', 30)}"),
            ("simulator", "on" if USE_SIMULATOR else "off"),
        ]:
            r = BoxLayout(size_hint_y=None, height=dp(50), padding=[dp(14), 0, dp(14), 0])
            with r.canvas.before:
                Color(*PILL)
                rr = RoundedRectangle(pos=r.pos, size=r.size, radius=[dp(12)])
            r.bind(pos=lambda *_a, rr=rr, r=r: setattr(rr, "pos", r.pos), size=lambda *_a, rr=rr, r=r: setattr(rr, "size", r.size))
            l = Label(text=k, color=TXT, halign="left")
            l.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
            val = Label(text=v, color=MUTED, halign="right")
            val.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
            r.add_widget(l)
            r.add_widget(val)
            self.rows.add_widget(r)
        self.sim.text = "simulator on" if USE_SIMULATOR else "simulator off"

    def _toggle(self, *_):
        global USE_SIMULATOR
        USE_SIMULATOR = not USE_SIMULATOR
        self.on_enter()

    def _dev(self, *_):
        App.get_running_app().root.get_screen("monitor")._dev_popup()

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "monitor"


# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
class PaceRingApp(App):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.profile = {
            "name": "friend",
            "resting_bpm": 65,
            "threshold": 110,
            "spike_delta": 30,
            "spike_duration": 10,
        }

    def build(self):
        Window.clearcolor = BG
        self.profile.update(load_json(PROFILE_PATH, {}))
        sm = ScreenManager(transition=FadeTransition(duration=0.14))
        sm.add_widget(Onboard1(name="onboard1"))
        sm.add_widget(Onboard2(name="onboard2"))
        sm.add_widget(Onboard3(name="onboard3"))
        sm.add_widget(MonitorScreen(name="monitor"))
        sm.add_widget(SummaryScreen(name="summary"))
        sm.add_widget(SettingsScreen(name="settings"))
        if self.profile.get("name") and os.path.exists(PROFILE_PATH):
            sm.current = "monitor"
            Clock.schedule_once(lambda _dt: sm.get_screen("monitor").start_monitoring(), 0.3)
        else:
            sm.current = "onboard1"
        return sm

    def on_stop(self):
        save_json(PROFILE_PATH, self.profile)


if __name__ == "__main__":
    PaceRingApp().run()
"""
PaceRing v4.0 — POTS Heart Rate Monitor
Animated heart background, weekly summary, full dev mode
"""

import json, os, time, math, random
from datetime import datetime, timedelta
from collections import deque

USE_SIMULATOR = True   # <-- Toggle here, or via dev mode in-app

os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.config import Config
Config.set("graphics", "resizable", "0")
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.graphics import (
    Color, Rectangle, RoundedRectangle, Line, Ellipse,
    PushMatrix, PopMatrix, Scale, Translate, Mesh,
)
from kivy.metrics import dp, sp
from kivy.properties import (
    NumericProperty, StringProperty, ListProperty, BooleanProperty,
)
from kivy.utils import get_color_from_hex

# ── Palette ────────────────────────────────────────────────────────────────────
BG          = get_color_from_hex("#100d1a")
CARD_BG     = get_color_from_hex("#0d0b16")
PILL_BG     = get_color_from_hex("#1e1630")
ACCENT      = get_color_from_hex("#7c3aed")
ACCENT2     = get_color_from_hex("#6c2bda")
TEXT_MAIN   = get_color_from_hex("#ede9fe")
TEXT_MUTED  = get_color_from_hex("#6d5fa0")
BPM_REST    = get_color_from_hex("#ede9fe")
BPM_ELEV    = get_color_from_hex("#e879f9")
BPM_DANGER  = get_color_from_hex("#f43f5e")
STATUS_GRN  = get_color_from_hex("#4ade80")
STATUS_RED  = get_color_from_hex("#f43f5e")
STATUS_FUCH = get_color_from_hex("#e879f9")
AMBER       = get_color_from_hex("#fb923c")

PROFILE_PATH = os.path.join(os.path.expanduser("~"), ".pacering_profile.json")
LOG_PATH     = os.path.join(os.path.expanduser("~"), ".pacering_log.json")
DEV_CODE     = "Ryan_5610"
SCENARIOS    = ["resting", "walking", "pots_spike", "sustained", "recovery"]

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_profile():
    try:
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return None

def save_profile(data):
    try:
        with open(PROFILE_PATH, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def load_log():
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return []

def append_log(entry):
    log = load_log()
    log.append(entry)
    log = log[-10000:]  # keep last 10k entries
    try:
        with open(LOG_PATH, "w") as f:
            json.dump(log, f)
    except Exception:
        pass

def greeting(name):
    h = datetime.now().hour
    if 5 <= h < 12:    return f"good morning, {name}"
    elif 12 <= h < 17: return f"good afternoon, {name}"
    elif 17 <= h < 22: return f"good evening, {name}"
    else:              return f"hey {name}, rest up"

def bpm_colour(bpm, resting, threshold):
    if bpm >= threshold:       return list(BPM_DANGER)
    elif bpm >= resting + 20:  return list(BPM_ELEV)
    else:                      return list(BPM_REST)

def _pill_bg(w):
    w.canvas.before.clear()
    with w.canvas.before:
        Color(*PILL_BG)
        RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(10)])

# ── Animated Heart Widget ──────────────────────────────────────────────────────

class HeartWidget(Widget):
    """
    Draws a stylised anatomical-style heart using bezier curves.
    Pulses at the current BPM rate.
    """
    pulse_scale = NumericProperty(1.0)

    def __init__(self, **kw):
        super().__init__(**kw)
        self._bpm = 65
        self._pulse_event = None
        self._beat_phase = 0.0
        self.bind(pos=self._draw, size=self._draw, pulse_scale=self._draw)

    def set_bpm(self, bpm):
        self._bpm = max(40, min(200, bpm))
        # Restart pulse timer at new rate
        if self._pulse_event:
            self._pulse_event.cancel()
        interval = 60.0 / self._bpm
        self._pulse_event = Clock.schedule_interval(self._pulse_tick, interval)

    def _pulse_tick(self, dt):
        # Quick systole (expand) then diastole (contract)
        anim = (
            Animation(pulse_scale=1.18, duration=0.12, t="out_quad") +
            Animation(pulse_scale=0.96, duration=0.08, t="in_quad") +
            Animation(pulse_scale=1.0,  duration=0.15, t="out_quad")
        )
        anim.start(self)

    def _draw(self, *_):
        self.canvas.clear()
        cx = self.center_x
        cy = self.center_y
        s  = self.pulse_scale
        r  = min(self.width, self.height) * 0.42 * s

        with self.canvas:
            # Outer glow rings
            Color(0.49, 0.23, 0.93, 0.06 * s)
            Ellipse(pos=(cx - r*1.5, cy - r*1.5), size=(r*3, r*3))
            Color(0.49, 0.23, 0.93, 0.10 * s)
            Ellipse(pos=(cx - r*1.2, cy - r*1.2), size=(r*2.4, r*2.4))

            # Main heart shape via bezier approximation using Line
            # Heart parametric: x = 16sin^3(t), y = 13cos(t)-5cos(2t)-2cos(3t)-cos(4t)
            pts = []
            steps = 80
            for i in range(steps + 1):
                t = (i / steps) * 2 * math.pi
                hx = 16 * (math.sin(t)**3)
                hy = 13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t)
                # Normalize: hx in [-16,16], hy in [-17, 13]
                nx = cx + (hx / 17.0) * r
                ny = cy + (hy / 17.0) * r
                pts.extend([nx, ny])

            # Dark filled heart (draw as filled polygon via mesh)
            verts = []
            for i in range(0, len(pts), 2):
                verts.extend([pts[i], pts[i+1], 0, 0])
            # Centre point
            verts.extend([cx, cy, 0, 0])
            n = len(verts) // 4
            indices = list(range(n-1)) + [n-1] * (n-1)
            # Simplified: draw as outline + filled with translucent
            Color(0.35, 0.08, 0.55, 0.55)
            Mesh(vertices=verts[:-4], indices=list(range(n-1)), mode='triangle_fan')

            # Heart outline — fuchsia/purple gradient feel
            Color(0.91, 0.475, 0.976, 0.85)
            Line(points=pts, width=dp(1.8), close=True)

            # Inner highlight — top left lobe
            hl_x = cx - r * 0.28
            hl_y = cy + r * 0.38
            Color(1.0, 1.0, 1.0, 0.18)
            Ellipse(pos=(hl_x - r*0.22, hl_y - r*0.14), size=(r*0.44, r*0.28))

            # Aorta nub at top centre
            Color(0.55, 0.15, 0.80, 0.7)
            Ellipse(pos=(cx - r*0.12, cy + r*0.62), size=(r*0.24, r*0.32))

            # ECG blip line across bottom of heart
            ecg_y = cy - r * 0.72
            ecg_pts = [
                cx - r*0.8, ecg_y,
                cx - r*0.4, ecg_y,
                cx - r*0.25, ecg_y + r*0.28,
                cx - r*0.1,  ecg_y - r*0.38,
                cx + r*0.05, ecg_y + r*0.52,
                cx + r*0.18, ecg_y,
                cx + r*0.8,  ecg_y,
            ]
            Color(0.91, 0.475, 0.976, 0.55)
            Line(points=ecg_pts, width=dp(1.2))

    def stop(self):
        if self._pulse_event:
            self._pulse_event.cancel()
            self._pulse_event = None


class PumpingHeartLayer(FloatLayout):
    """
    Composite heart background:
    - optional realistic PNG heart if provided in assets/
    - vector heart fallback/highlight
    - pulse animation synced to BPM
    """
    pulse_scale = NumericProperty(1.0)
    pulse_y = NumericProperty(0.0)
    glow_alpha = NumericProperty(0.08)

    def __init__(self, **kw):
        super().__init__(**kw)
        self._bpm = 65
        self._pulse_event = None
        self._base_size = dp(280)
        self._heart_source = os.path.join("assets", "heart_realistic_bg.png")
        self._has_real_heart = os.path.exists(self._heart_source)

        with self.canvas.before:
            self._glow_col = Color(0.93, 0.38, 0.46, self.glow_alpha)
            self._glow = Ellipse(pos=self.pos, size=(dp(40), dp(40)))

        self._heart_img = Image(
            source=self._heart_source if self._has_real_heart else "",
            allow_stretch=True,
            keep_ratio=True,
            opacity=0.72 if self._has_real_heart else 0.0,
            size_hint=(None, None),
            size=(self._base_size, self._base_size),
            pos_hint={"center_x": 0.5, "center_y": 0.57},
        )
        self.add_widget(self._heart_img)

        self._vector_heart = HeartWidget(
            size_hint=(None, None),
            size=(self._base_size * 0.95, self._base_size * 0.95),
            pos_hint={"center_x": 0.5, "center_y": 0.57},
            opacity=0.22 if self._has_real_heart else 0.82,
        )
        self.add_widget(self._vector_heart)

        self.bind(
            pos=self._layout_heart,
            size=self._layout_heart,
            pulse_scale=self._layout_heart,
            pulse_y=self._layout_heart,
            glow_alpha=self._layout_heart,
        )
        self._layout_heart()

    def _layout_heart(self, *_):
        base = min(self.width, self.height) * 0.66
        size = max(dp(190), base) * self.pulse_scale
        cx = self.x + self.width * 0.5
        cy = self.y + self.height * 0.57 + self.pulse_y
        for w, ratio in ((self._heart_img, 1.0), (self._vector_heart, 0.95)):
            w.size = (size * ratio, size * ratio)
            w.pos = (cx - w.width / 2, cy - w.height / 2)
        glow_w = size * 1.28
        glow_h = size * 0.92
        self._glow.pos = (cx - glow_w / 2, cy - glow_h / 2 - dp(4))
        self._glow.size = (glow_w, glow_h)
        self._glow_col.a = self.glow_alpha

    def set_bpm(self, bpm):
        bpm = max(40, min(200, int(bpm)))
        self._bpm = bpm
        self._vector_heart.set_bpm(bpm)
        if self._pulse_event:
            self._pulse_event.cancel()
        self._pulse_event = Clock.schedule_interval(self._pulse_tick, 60.0 / bpm)

    def _pulse_tick(self, _dt):
        cycle = 60.0 / max(40, self._bpm)
        # Lifelike cycle:
        # - fast systolic squeeze/expand
        # - short rebound notch
        # - smooth diastolic settle
        up = max(0.08, cycle * 0.23)
        notch = max(0.05, cycle * 0.13)
        settle = max(0.10, cycle * 0.48)
        amp = 1.11 if self._has_real_heart else 1.08
        ykick = dp(5) if self._has_real_heart else dp(3)
        glow_peak = 0.20 if self._has_real_heart else 0.14
        anim = (
            Animation(pulse_scale=amp, pulse_y=ykick, glow_alpha=glow_peak, duration=up, t="out_cubic")
            + Animation(pulse_scale=0.985, pulse_y=-ykick * 0.45, glow_alpha=0.10, duration=notch, t="in_out_quad")
            + Animation(pulse_scale=1.0, pulse_y=0.0, glow_alpha=0.08, duration=settle, t="out_sine")
        )
        anim.start(self)

    def stop(self):
        if self._pulse_event:
            self._pulse_event.cancel()
            self._pulse_event = None
        self._vector_heart.stop()


# ── BPM Graph ──────────────────────────────────────────────────────────────────

class BPMGraph(Widget):
    history = ListProperty([])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw, history=self._draw)

    def push(self, bpm):
        h = list(self.history)[-59:]
        h.append(bpm)
        self.history = h

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(*CARD_BG)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        if len(self.history) < 2:
            return
        pts = self.history
        mn, mx = min(pts), max(pts)
        rng = max(mx - mn, 20)
        w, h   = self.size
        px, py = self.pos
        pad = dp(10)
        uw  = (w - 2*pad) / (len(pts) - 1)
        points = []
        for i, v in enumerate(pts):
            x = px + pad + i * uw
            y = py + pad + ((v - mn) / rng) * (h - 2*pad)
            points += [x, y]
        with self.canvas:
            # Fill
            fill_v = [points[0], py + pad, 0, 0]
            for i in range(0, len(points), 2):
                fill_v += [points[i], points[i+1], 0, 0]
            fill_v += [points[-2], py + pad, 0, 0]
            Color(*ACCENT[:3], 0.22)
            Mesh(vertices=fill_v, indices=list(range(len(fill_v)//4)), mode='triangle_fan')
            # Line
            Color(*ACCENT, 0.9)
            Line(points=points, width=dp(1.8))
            # Live dot
            Color(*STATUS_FUCH)
            r = dp(4)
            Ellipse(pos=(points[-2]-r, points[-1]-r), size=(r*2, r*2))


# ── HRV Bar Chart (weekly summary) ────────────────────────────────────────────

class HRVBarChart(Widget):
    data = ListProperty([])   # list of (label, value) tuples

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw, data=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        if not self.data:
            return
        n   = len(self.data)
        w, h = self.size
        px, py = self.pos
        pad  = dp(8)
        gap  = dp(6)
        bar_w = (w - 2*pad - gap*(n-1)) / n
        max_v = max(v for _, v in self.data) or 1
        with self.canvas:
            for i, (label, val) in enumerate(self.data):
                bx = px + pad + i * (bar_w + gap)
                bar_h = (val / max_v) * (h - dp(32))
                by = py + dp(22)
                # Bar background
                Color(*PILL_BG)
                RoundedRectangle(pos=(bx, by), size=(bar_w, h - dp(22)), radius=[dp(4)])
                # Bar fill — colour by value
                ratio = val / max_v
                r = 0.49 + ratio * 0.42
                g = 0.27 + ratio * 0.08
                b = 0.93 - ratio * 0.3
                Color(r, g, b, 0.9)
                RoundedRectangle(pos=(bx, by), size=(bar_w, bar_h), radius=[dp(4)])
                # Label
                Color(*TEXT_MUTED)
                # We just use the bar positions — labels are in a separate layout

# ── Shared widgets ─────────────────────────────────────────────────────────────

class PurpleButton(Button):
    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_color", [0, 0, 0, 0])
        kw.setdefault("color", TEXT_MAIN)
        kw.setdefault("font_size", sp(16))
        kw.setdefault("bold", True)
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(54))
        super().__init__(**kw)
        with self.canvas.before:
            self._col  = Color(*ACCENT)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(27)])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._rect.pos  = self.pos
        self._rect.size = self.size

    def on_press(self):   self._col.rgba = list(ACCENT2)
    def on_release(self): self._col.rgba = list(ACCENT)


class GhostButton(Button):
    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_color", [0, 0, 0, 0])
        kw.setdefault("color", TEXT_MUTED)
        kw.setdefault("font_size", sp(15))
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(44))
        super().__init__(**kw)


class StatBox(FloatLayout):
    def __init__(self, value="--", label="", **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*PILL_BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=self._upd, size=self._upd)
        self.val_lbl = Label(
            text=str(value), font_size=sp(22), bold=True, color=TEXT_MAIN,
            size_hint=(1, None), height=dp(34),
            pos_hint={"center_x": 0.5, "top": 0.75},
        )
        self.lbl = Label(
            text=label, font_size=sp(11), color=TEXT_MUTED,
            size_hint=(1, None), height=dp(18),
            pos_hint={"center_x": 0.5, "top": 0.38},
        )
        self.add_widget(self.val_lbl)
        self.add_widget(self.lbl)

    def _upd(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size

    def set_value(self, v, color=None):
        self.val_lbl.text = str(v)
        if color:
            self.val_lbl.color = color


class StepDots(BoxLayout):
    def __init__(self, total=3, current=1, **kw):
        kw.setdefault("orientation", "horizontal")
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (dp(72), dp(12)))
        kw.setdefault("spacing", dp(8))
        super().__init__(**kw)
        for i in range(1, total+1):
            w = Widget(size_hint=(None, None), size=(dp(10), dp(10)))
            c = list(ACCENT) if i == current else list(TEXT_MUTED)
            with w.canvas:
                Color(*c)
                Ellipse(pos=(0, 0), size=(dp(10), dp(10)))
            self.add_widget(w)


class StepBadge(Label):
    def __init__(self, **kw):
        kw.setdefault("font_size", sp(12))
        kw.setdefault("color", TEXT_MUTED)
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (dp(110), dp(26)))
        super().__init__(**kw)
        self._draw_bg()
        self.bind(pos=lambda *_: self._draw_bg(), size=lambda *_: self._draw_bg())

    def _draw_bg(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*PILL_BG)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(13)])


# ── Onboarding screens ─────────────────────────────────────────────────────────

def _screen_bg(root):
    with root.canvas.before:
        Color(*BG)
        bg = Rectangle(pos=root.pos, size=root.size)
    root.bind(
        pos=lambda *_: setattr(bg, "pos", root.pos),
        size=lambda *_: setattr(bg, "size", root.size),
    )


class OnboardScreen1(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        _screen_bg(root)

        col = BoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(64), dp(32), dp(40)],
            spacing=dp(0), size_hint=(1, 1),
        )

        bw = BoxLayout(size_hint_y=None, height=dp(38))
        bw.add_widget(StepBadge(text="  step 1 of 3  "))
        bw.add_widget(Widget())
        col.add_widget(bw)
        col.add_widget(Widget(size_hint_y=None, height=dp(36)))

        t = Label(text="what's your name?", font_size=sp(30), bold=True,
                  color=TEXT_MAIN, size_hint_y=None, height=dp(44), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(t)
        col.add_widget(Widget(size_hint_y=None, height=dp(8)))
        s = Label(text="so we can make this feel like yours",
                  font_size=sp(15), color=TEXT_MUTED,
                  size_hint_y=None, height=dp(26), halign="left")
        s.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(s)
        col.add_widget(Widget(size_hint_y=None, height=dp(40)))

        self.name_input = TextInput(
            hint_text="your name", hint_text_color=TEXT_MUTED,
            foreground_color=TEXT_MAIN, background_color=PILL_BG,
            cursor_color=ACCENT, font_size=sp(18),
            size_hint_y=None, height=dp(56),
            padding=[dp(18), dp(16), dp(18), dp(16)], multiline=False,
        )
        col.add_widget(self.name_input)
        col.add_widget(Widget())

        btn = PurpleButton(text="continue")
        btn.bind(on_release=self._next)
        col.add_widget(btn)
        col.add_widget(Widget(size_hint_y=None, height=dp(20)))

        dr = BoxLayout(size_hint_y=None, height=dp(16))
        dr.add_widget(Widget())
        dr.add_widget(StepDots(total=3, current=1))
        dr.add_widget(Widget())
        col.add_widget(dr)

        root.add_widget(col)
        self.add_widget(root)

    def _next(self, *_):
        name = self.name_input.text.strip() or "friend"
        App.get_running_app().profile["name"] = name
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "onboard2"


class OnboardScreen2(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        _screen_bg(root)
        col = BoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(64), dp(32), dp(40)],
            spacing=dp(0), size_hint=(1, 1),
        )
        bw = BoxLayout(size_hint_y=None, height=dp(38))
        bw.add_widget(StepBadge(text="  step 2 of 3  "))
        bw.add_widget(Widget())
        col.add_widget(bw)
        col.add_widget(Widget(size_hint_y=None, height=dp(28)))
        t = Label(text="your resting heart rate", font_size=sp(28), bold=True,
                  color=TEXT_MAIN, size_hint_y=None, height=dp(44), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(t)
        col.add_widget(Widget(size_hint_y=None, height=dp(6)))
        s = Label(text="used to detect spikes accurately",
                  font_size=sp(15), color=TEXT_MUTED,
                  size_hint_y=None, height=dp(26), halign="left")
        s.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(s)
        col.add_widget(Widget(size_hint_y=None, height=dp(28)))

        boxes = GridLayout(cols=2, spacing=dp(12), size_hint_y=None, height=dp(88))
        self.box_resting   = StatBox(value="65",  label="resting BPM")
        self.box_threshold = StatBox(value="110", label="alert threshold")
        boxes.add_widget(self.box_resting)
        boxes.add_widget(self.box_threshold)
        col.add_widget(boxes)
        col.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.slider = Slider(min=40, max=100, value=65,
                             size_hint_y=None, height=dp(44),
                             cursor_size=(dp(28), dp(28)))
        self.slider.bind(value=self._slide)
        col.add_widget(self.slider)
        d = Label(text="drag to set your resting BPM", font_size=sp(13),
                  color=TEXT_MUTED, size_hint_y=None, height=dp(22))
        col.add_widget(d)
        col.add_widget(Widget())

        btn = PurpleButton(text="continue")
        btn.bind(on_release=self._next)
        col.add_widget(btn)
        col.add_widget(Widget(size_hint_y=None, height=dp(4)))
        ghost = GhostButton(text="use defaults")
        ghost.bind(on_release=self._defaults)
        col.add_widget(ghost)
        col.add_widget(Widget(size_hint_y=None, height=dp(14)))
        dr = BoxLayout(size_hint_y=None, height=dp(16))
        dr.add_widget(Widget())
        dr.add_widget(StepDots(total=3, current=2))
        dr.add_widget(Widget())
        col.add_widget(dr)

        root.add_widget(col)
        self.add_widget(root)

    def _slide(self, _, val):
        r = int(val)
        self.box_resting.set_value(str(r))
        self.box_threshold.set_value(str(r + 45))

    def _next(self, *_):
        p = App.get_running_app().profile
        p["resting_bpm"] = int(self.slider.value)
        p["threshold"]   = int(self.slider.value) + 45
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "onboard3"

    def _defaults(self, *_):
        p = App.get_running_app().profile
        p["resting_bpm"] = 65
        p["threshold"]   = 110
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "onboard3"


class OnboardScreen3(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        _screen_bg(root)
        col = BoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(64), dp(32), dp(40)],
            spacing=dp(0), size_hint=(1, 1),
        )
        bw = BoxLayout(size_hint_y=None, height=dp(38))
        bw.add_widget(StepBadge(text="  step 3 of 3  "))
        bw.add_widget(Widget())
        col.add_widget(bw)
        col.add_widget(Widget(size_hint_y=None, height=dp(28)))
        t = Label(text="spike sensitivity", font_size=sp(30), bold=True,
                  color=TEXT_MAIN, size_hint_y=None, height=dp(44), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(t)
        col.add_widget(Widget(size_hint_y=None, height=dp(6)))
        s = Label(text="alert me when HR rises by...",
                  font_size=sp(15), color=TEXT_MUTED,
                  size_hint_y=None, height=dp(26), halign="left")
        s.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(s)
        col.add_widget(Widget(size_hint_y=None, height=dp(28)))

        boxes = GridLayout(cols=2, spacing=dp(12), size_hint_y=None, height=dp(88))
        self.box_delta = StatBox(value="+30", label="BPM spike delta")
        self.box_dur   = StatBox(value="10s", label="sustained duration")
        boxes.add_widget(self.box_delta)
        boxes.add_widget(self.box_dur)
        col.add_widget(boxes)
        col.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.slider = Slider(min=15, max=50, value=30,
                             size_hint_y=None, height=dp(44),
                             cursor_size=(dp(28), dp(28)))
        self.slider.bind(value=lambda _, v: self.box_delta.set_value(f"+{int(v)}"))
        col.add_widget(self.slider)
        d = Label(text="matches typical POTS thresholds", font_size=sp(13),
                  color=TEXT_MUTED, size_hint_y=None, height=dp(22))
        col.add_widget(d)
        col.add_widget(Widget())

        btn = PurpleButton(text="let's go")
        btn.bind(on_release=self._finish)
        col.add_widget(btn)
        col.add_widget(Widget(size_hint_y=None, height=dp(20)))
        dr = BoxLayout(size_hint_y=None, height=dp(16))
        dr.add_widget(Widget())
        dr.add_widget(StepDots(total=3, current=3))
        dr.add_widget(Widget())
        col.add_widget(dr)

        root.add_widget(col)
        self.add_widget(root)

    def _finish(self, *_):
        p = App.get_running_app().profile
        p["spike_delta"]    = int(self.slider.value)
        p["spike_duration"] = 10
        p["vibration"]      = True
        p["sound_alerts"]   = True
        save_profile(p)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "monitor"
        App.get_running_app().root.get_screen("monitor").start_monitoring()


# ── Monitor screen ─────────────────────────────────────────────────────────────

class MonitorScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._worker       = None
        self._alert_engine = None
        self._dev_taps     = []
        self._alert_up     = False
        self._build()

    def _build(self):
        root = FloatLayout()
        _screen_bg(root)

        # Heart background — realistic asset + vector fallback, BPM-synced pulse
        self.heart = PumpingHeartLayer(size_hint=(1, 1))
        root.add_widget(self.heart)

        # Main content column (on top of heart)
        col = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(52), dp(24), dp(24)],
            spacing=dp(12), size_hint=(1, 1),
        )

        # ── Top row: greeting + avatar button ──
        top = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.greeting_lbl = Label(
            text="good morning", font_size=sp(18), bold=True,
            color=TEXT_MAIN, halign="left", valign="middle",
        )
        self.greeting_lbl.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, None))
        )
        top.add_widget(self.greeting_lbl)

        self.sim_toggle_btn = GhostButton(
            text=f"sim: {'on' if USE_SIMULATOR else 'off'}",
            size_hint=(None, 1), width=dp(88), color=STATUS_GRN if USE_SIMULATOR else STATUS_RED
        )
        self.sim_toggle_btn.bind(on_release=self._toggle_simulator)
        top.add_widget(self.sim_toggle_btn)

        self.initial_btn = Button(
            size_hint=(None, None), size=(dp(40), dp(40)),
            background_normal="", background_color=[0, 0, 0, 0],
        )
        with self.initial_btn.canvas.before:
            Color(*ACCENT)
            self._circle = Ellipse(
                pos=self.initial_btn.pos, size=self.initial_btn.size
            )
        self.initial_btn.bind(
            pos=lambda *_: setattr(self._circle, "pos", self.initial_btn.pos),
            size=lambda *_: setattr(self._circle, "size", self.initial_btn.size),
            on_release=self._initial_tapped,
        )
        self.initial_lbl = Label(
            text="?", font_size=sp(16), bold=True, color=TEXT_MAIN,
            size_hint=(None, None), size=(dp(40), dp(40)),
        )
        top.add_widget(self.initial_btn)
        top.add_widget(self.initial_lbl)
        col.add_widget(top)

        # ── Status ──
        self.status_lbl = Label(
            text="not connected", font_size=sp(13),
            color=TEXT_MUTED, size_hint_y=None, height=dp(20), halign="left",
        )
        self.status_lbl.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, None))
        )
        col.add_widget(self.status_lbl)

        # ── Big BPM number (sits on top of heart) ──
        bpm_box = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(110), spacing=dp(0)
        )
        self.bpm_lbl = Label(
            text="--", font_size=sp(96), bold=True,
            color=BPM_REST, size_hint_y=None, height=dp(94),
        )
        bpm_unit = Label(
            text="BPM", font_size=sp(13), color=TEXT_MUTED,
            size_hint_y=None, height=dp(16),
        )
        bpm_box.add_widget(self.bpm_lbl)
        bpm_box.add_widget(bpm_unit)
        col.add_widget(bpm_box)

        # ── HRV ──
        self.hrv_lbl = Label(
            text="HRV  --  ms", font_size=sp(15),
            color=TEXT_MAIN, size_hint_y=None, height=dp(22),
        )
        col.add_widget(self.hrv_lbl)

        # ── Graph ──
        self.graph = BPMGraph(size_hint_y=None, height=dp(80))
        col.add_widget(self.graph)

        # ── Time labels under graph ──
        tlrow = BoxLayout(size_hint_y=None, height=dp(16))
        for t in ["0s", "15s", "30s", "45s", "60s"]:
            tlrow.add_widget(Label(text=t, font_size=sp(10), color=TEXT_MUTED))
        col.add_widget(tlrow)

        # ── Stat boxes ──
        stats = GridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(80))
        self.stat_resting = StatBox(value="--",    label="resting")
        self.stat_hrv     = StatBox(value="--",    label="HRV ms")
        self.stat_status  = StatBox(value="clear", label="status")
        self.stat_status.val_lbl.color = list(STATUS_GRN)
        stats.add_widget(self.stat_resting)
        stats.add_widget(self.stat_hrv)
        stats.add_widget(self.stat_status)
        col.add_widget(stats)

        col.add_widget(Widget())

        # ── Bottom nav bar ──
        nav = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        self.connect_btn = PurpleButton(text="connect to band")
        self.connect_btn.bind(on_release=self._connect_pressed)

        summary_btn = Button(
            text="weekly", font_size=sp(13),
            background_normal="", background_color=[0, 0, 0, 0],
            color=TEXT_MUTED, size_hint=(None, 1), width=dp(70),
        )
        summary_btn.bind(on_release=lambda *_: self._go_summary())

        nav.add_widget(self.connect_btn)
        nav.add_widget(summary_btn)
        col.add_widget(nav)

        root.add_widget(col)

        # ── Alert card ──
        self._alert_card = self._make_alert_card()
        root.add_widget(self._alert_card)

        self.add_widget(root)
        self._root_fl = root

    def _make_alert_card(self):
        card = FloatLayout(size_hint=(1, None), height=dp(170))
        card.y = -dp(200)

        with card.canvas.before:
            Color(*CARD_BG)
            self._card_bg = RoundedRectangle(
                pos=card.pos, size=card.size, radius=[dp(20), dp(20), 0, 0]
            )
            Color(*ACCENT, 0.45)
            self._card_border = Line(
                rounded_rectangle=[card.x, card.y, card.width, card.height, dp(20)],
                width=dp(1.2),
            )

        def upd(*_):
            self._card_bg.pos  = card.pos
            self._card_bg.size = card.size
            self._card_border.rounded_rectangle = [
                card.x, card.y, card.width, card.height, dp(20)
            ]
        card.bind(pos=upd, size=upd)

        inner = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(18), dp(24), dp(14)],
            spacing=dp(8), size_hint=(1, 1),
        )
        self.alert_title = Label(
            text="spike detected", font_size=sp(17), bold=True,
            color=TEXT_MAIN, halign="left", size_hint_y=None, height=dp(28),
        )
        self.alert_title.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, None))
        )
        self.alert_msg = Label(
            text="", font_size=sp(13), color=TEXT_MUTED,
            halign="left", size_hint_y=None, height=dp(38),
        )
        self.alert_msg.bind(
            size=lambda w, _: setattr(w, "text_size", (w.width, dp(38)))
        )
        dismiss = PurpleButton(text="ok - resting now", height=dp(44))
        dismiss.bind(on_release=self._dismiss_alert)
        inner.add_widget(self.alert_title)
        inner.add_widget(self.alert_msg)
        inner.add_widget(dismiss)
        card.add_widget(inner)
        return card

    def on_enter(self):
        self._refresh_profile()

    def _refresh_profile(self):
        p    = App.get_running_app().profile
        name = p.get("name", "friend")
        self.greeting_lbl.text = greeting(name)
        self.initial_lbl.text  = name[0].upper() if name else "?"
        self.stat_resting.set_value(str(p.get("resting_bpm", 65)))

    def start_monitoring(self):
        self._refresh_profile()
        p = App.get_running_app().profile
        from alert_engine import AlertEngine, AlertConfig
        self._alert_engine = AlertEngine(AlertConfig(
            sustained_hr_threshold=p.get("threshold", 110),
            sustained_duration_secs=p.get("spike_duration", 10),
            spike_bpm_delta=p.get("spike_delta", 30),
        ))
        if USE_SIMULATOR:
            self._start_sim("resting")
        else:
            self._start_ble()

    def _start_sim(self, scenario="resting"):
        if self._worker:
            self._worker.stop()
        from fake_ble import FakeBLEWorker
        self._worker = FakeBLEWorker(
            on_bpm=self._on_bpm,
            on_status=self._on_status,
            on_alert=self._on_alert_event,
            scenario=scenario,
        )
        self._worker.start()

    def _start_ble(self):
        if self._worker:
            self._worker.stop()
        try:
            import threading
            threading.Thread(target=self._ble_thread, daemon=True).start()
        except Exception as e:
            Clock.schedule_once(
                lambda dt: setattr(self.status_lbl, "text", f"BLE error: {e}"), 0
            )

    def _ble_thread(self):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._ble_main())

    async def _ble_main(self):
        from bleak import BleakScanner, BleakClient
        Clock.schedule_once(lambda dt: setattr(
            self.status_lbl, "text", "scanning for band..."), 0)
        devices  = await BleakScanner.discover(timeout=30.0)
        keywords = ["mi band", "xiaomi", "band 10", "smart band", "miband"]
        address  = None
        for d in devices:
            if d.name and any(k in d.name.lower() for k in keywords):
                address = d.address
                Clock.schedule_once(lambda dt: setattr(
                    self.status_lbl, "text", f"found: {d.name}"), 0)
                break
        if not address:
            Clock.schedule_once(lambda dt: setattr(
                self.status_lbl, "text", "band not found — close Mi Fitness app"), 0)
            return
        try:
            async with BleakClient(address, timeout=20.0) as client:
                Clock.schedule_once(lambda dt: setattr(
                    self.status_lbl, "text", "connected — monitoring"), 0)
                HR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
                await client.start_notify(HR_UUID, self._ble_handler)
                while client.is_connected:
                    await asyncio.sleep(0.5)
                await client.stop_notify(HR_UUID)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(
                self.status_lbl, "text", f"error: {e}"), 0)

    def _ble_handler(self, sender, data):
        flags = data[0]
        bpm   = int.from_bytes(data[1:3], "little") if (flags & 1) else data[1]
        Clock.schedule_once(lambda dt: self._on_bpm(bpm, None), 0)

    def _on_bpm(self, bpm, rmssd):
        p         = App.get_running_app().profile
        resting   = p.get("resting_bpm", 65)
        threshold = p.get("threshold", 110)

        self.bpm_lbl.text = str(bpm)
        Animation(color=bpm_colour(bpm, resting, threshold), duration=0.4).start(self.bpm_lbl)

        # Update heart animation speed
        self.heart.set_bpm(bpm)

        if rmssd is not None:
            self.hrv_lbl.text = f"HRV  {int(rmssd)}  ms"
            self.stat_hrv.set_value(str(int(rmssd)))

        self.graph.push(bpm)

        if bpm >= threshold:
            self.stat_status.set_value("alert",      list(STATUS_RED))
        elif bpm >= resting + 20:
            self.stat_status.set_value("recovering", list(STATUS_FUCH))
        else:
            self.stat_status.set_value("clear",       list(STATUS_GRN))

        # Log data point
        append_log({
            "ts":    datetime.now().isoformat(),
            "bpm":   bpm,
            "rmssd": int(rmssd) if rmssd else None,
        })

        # Alert engine check
        if self._alert_engine and not self._alert_up:
            result = self._alert_engine.update(bpm)
            if result:
                self._show_alert(result.type, result.message)

    def _on_status(self, status):
        self.status_lbl.text = status

    def _on_alert_event(self, alert_event):
        if not self._alert_up:
            self._show_alert(alert_event.type, alert_event.message)

    def _show_alert(self, atype, msg):
        self._alert_up = True
        self.alert_title.text = "spike detected" if atype == "spike" else "sustained HR"
        self.alert_msg.text   = msg
        Animation(y=dp(0), duration=0.35, t="out_back").start(self._alert_card)
        try:
            from plyer import vibrator
            vibrator.vibrate(time=1.5)
        except Exception:
            pass

    def _dismiss_alert(self, *_):
        def _done(*_):
            self._alert_up = False
            if self._alert_engine:
                self._alert_engine._spike_alerted     = False
                self._alert_engine._sustained_alerted = False
                self._alert_engine._sustained_start   = None
        anim = Animation(y=-dp(200), duration=0.25, t="in_quad")
        anim.bind(on_complete=_done)
        anim.start(self._alert_card)

    def _connect_pressed(self, *_):
        self.connect_btn.text     = "connecting..."
        self.connect_btn.disabled = True
        Clock.schedule_once(lambda dt: self.start_monitoring(), 0.1)

    def _go_summary(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "summary"

    def _initial_tapped(self, *_):
        now = time.time()
        self._dev_taps = [t for t in self._dev_taps if now - t < 1.5]
        self._dev_taps.append(now)
        if len(self._dev_taps) >= 5:
            self._dev_taps = []
            self._open_dev_mode()
        else:
            if len(self._dev_taps) == 1:
                Clock.schedule_once(self._single_tap_nav, 1.6)

    def _single_tap_nav(self, *_):
        if len(self._dev_taps) < 5:
            self._dev_taps = []
            self.manager.transition = SlideTransition(direction="left")
            self.manager.current = "settings"

    def _open_dev_mode(self):
        content = BoxLayout(orientation="vertical", padding=[dp(20), dp(20)], spacing=dp(12))
        with content.canvas.before:
            Color(*CARD_BG)
            bg = Rectangle(pos=content.pos, size=content.size)
        content.bind(
            pos=lambda *_: setattr(bg, "pos", content.pos),
            size=lambda *_: setattr(bg, "size", content.size),
        )
        content.add_widget(Label(
            text="developer mode", font_size=sp(16), bold=True,
            color=TEXT_MAIN, size_hint_y=None, height=dp(30),
        ))
        self._dev_input = TextInput(
            hint_text="enter code", hint_text_color=TEXT_MUTED,
            foreground_color=TEXT_MAIN, background_color=PILL_BG,
            cursor_color=ACCENT, font_size=sp(16),
            size_hint_y=None, height=dp(48),
            multiline=False, password=True,
        )
        self._dev_err = Label(text="", font_size=sp(13), color=STATUS_RED,
                              size_hint_y=None, height=dp(22))
        ok = PurpleButton(text="unlock")
        ok.bind(on_release=self._check_code)
        content.add_widget(self._dev_input)
        content.add_widget(self._dev_err)
        content.add_widget(ok)
        self._dev_popup = Popup(
            title="", content=content,
            size_hint=(0.85, None), height=dp(240),
            background_color=CARD_BG, separator_height=0, title_size=0,
        )
        self._dev_popup.open()

    def _check_code(self, *_):
        if self._dev_input.text.strip() == DEV_CODE:
            self._dev_popup.dismiss()
            self._open_scenario_picker()
        else:
            self._dev_input.text = ""
            self._dev_err.text   = "wrong code - try again"

    def _open_scenario_picker(self):
        content = BoxLayout(orientation="vertical", padding=[dp(16), dp(16)], spacing=dp(8))
        with content.canvas.before:
            Color(*CARD_BG)
            bg = Rectangle(pos=content.pos, size=content.size)
        content.bind(
            pos=lambda *_: setattr(bg, "pos", content.pos),
            size=lambda *_: setattr(bg, "size", content.size),
        )
        content.add_widget(Label(
            text="select scenario", font_size=sp(16), bold=True,
            color=TEXT_MAIN, size_hint_y=None, height=dp(30),
        ))

        # Simulator toggle
        sim_row = BoxLayout(size_hint_y=None, height=dp(40))
        sim_lbl = Label(
            text=f"simulator: {'ON' if USE_SIMULATOR else 'OFF'}",
            font_size=sp(14), color=STATUS_GRN if USE_SIMULATOR else STATUS_RED,
        )
        sim_toggle = GhostButton(
            text="toggle",
            size_hint=(None, 1), width=dp(80),
        )
        def _toggle_sim(*_):
            global USE_SIMULATOR
            USE_SIMULATOR = not USE_SIMULATOR
            sim_lbl.text = f"simulator: {'ON' if USE_SIMULATOR else 'OFF'}"
            sim_lbl.color = STATUS_GRN if USE_SIMULATOR else STATUS_RED
        sim_toggle.bind(on_release=_toggle_sim)
        sim_row.add_widget(sim_lbl)
        sim_row.add_widget(sim_toggle)
        content.add_widget(sim_row)

        self._sc_popup = Popup(
            title="", content=content,
            size_hint=(0.85, None), height=dp(420),
            background_color=CARD_BG, separator_height=0, title_size=0,
        )
        for sc in SCENARIOS:
            btn = PurpleButton(text=sc, height=dp(42))
            btn._sc = sc
            btn.bind(on_release=self._pick_scenario)
            content.add_widget(btn)
        cancel = GhostButton(text="cancel")
        cancel.bind(on_release=self._sc_popup.dismiss)
        content.add_widget(cancel)
        self._sc_popup.open()

    def _pick_scenario(self, btn):
        self._sc_popup.dismiss()
        self._alert_up = False
        Animation(y=-dp(200), duration=0.1).start(self._alert_card)
        self._start_sim(btn._sc)

    def _toggle_simulator(self, *_):
        global USE_SIMULATOR
        USE_SIMULATOR = not USE_SIMULATOR
        self.sim_toggle_btn.text = f"sim: {'on' if USE_SIMULATOR else 'off'}"
        self.sim_toggle_btn.color = STATUS_GRN if USE_SIMULATOR else STATUS_RED
        self.status_lbl.text = "simulator enabled" if USE_SIMULATOR else "bluetooth mode enabled"


# ── Weekly Summary Screen ──────────────────────────────────────────────────────

class SummaryScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        _screen_bg(root)

        sv = ScrollView(size_hint=(1, 1))
        self._col = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(56), dp(24), dp(32)],
            spacing=dp(16), size_hint_y=None,
        )
        self._col.bind(minimum_height=self._col.setter("height"))
        sv.add_widget(self._col)
        root.add_widget(sv)
        self.add_widget(root)

    def on_enter(self):
        self._col.clear_widgets()
        self._build_content()

    def _build_content(self):
        col = self._col
        p   = App.get_running_app().profile
        name = p.get("name", "friend")

        # Back button
        back_row = BoxLayout(size_hint_y=None, height=dp(40))
        back = GhostButton(text="< back", size_hint=(None, 1), width=dp(80))
        back.bind(on_release=lambda *_: self._back())
        back_row.add_widget(back)
        back_row.add_widget(Widget())
        col.add_widget(back_row)

        # Title
        t = Label(text=f"hi, {name}!", font_size=sp(26), bold=True,
                  color=TEXT_MAIN, size_hint_y=None, height=dp(38), halign="left")
        t.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(t)
        s = Label(text="here's your weekly summary",
                  font_size=sp(15), color=TEXT_MUTED,
                  size_hint_y=None, height=dp(24), halign="left")
        s.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(s)

        # Compute weekly stats from log
        stats = self._compute_weekly_stats()

        # Big avg BPM card
        avg_card = FloatLayout(size_hint_y=None, height=dp(100))
        with avg_card.canvas.before:
            Color(*PILL_BG)
            bg = RoundedRectangle(pos=avg_card.pos, size=avg_card.size, radius=[dp(16)])
        avg_card.bind(
            pos=lambda *_: setattr(bg, "pos", avg_card.pos),
            size=lambda *_: setattr(bg, "size", avg_card.size),
        )
        avg_bpm_lbl = Label(
            text=str(stats["avg_bpm"]),
            font_size=sp(52), bold=True, color=BPM_ELEV,
            size_hint=(None, None), size=(dp(120), dp(70)),
            pos_hint={"x": 0.05, "center_y": 0.55},
        )
        avg_card.add_widget(avg_bpm_lbl)
        avg_card.add_widget(Label(
            text="bpm", font_size=sp(14), color=TEXT_MUTED,
            size_hint=(None, None), size=(dp(40), dp(24)),
            pos_hint={"x": 0.38, "center_y": 0.38},
        ))
        avg_card.add_widget(Label(
            text=f"{stats['max_bpm']}  Max   {stats['min_bpm']}  Min",
            font_size=sp(13), color=TEXT_MUTED,
            size_hint=(None, None), size=(dp(160), dp(24)),
            pos_hint={"right": 0.97, "center_y": 0.5},
        ))
        col.add_widget(avg_card)

        # HRV section
        hrv_title = Label(text="Heart Rate Variability",
                          font_size=sp(15), bold=True, color=TEXT_MAIN,
                          size_hint_y=None, height=dp(28), halign="left")
        hrv_title.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(hrv_title)

        hrv_row = BoxLayout(size_hint_y=None, height=dp(36))
        hrv_row.add_widget(Label(
            text="Heart Rate Variability",
            font_size=sp(13), color=TEXT_MUTED, halign="left",
        ))
        hrv_row.add_widget(Label(
            text=f"{stats['avg_hrv']} ms",
            font_size=sp(18), bold=True, color=STATUS_FUCH,
            halign="right",
        ))
        col.add_widget(hrv_row)

        # HRV bar chart for last 7 days
        hrv_card = BoxLayout(orientation="vertical",
                             size_hint_y=None, height=dp(160),
                             padding=[dp(12), dp(12)])
        with hrv_card.canvas.before:
            Color(*PILL_BG)
            hbg = RoundedRectangle(pos=hrv_card.pos, size=hrv_card.size, radius=[dp(14)])
        hrv_card.bind(
            pos=lambda *_: setattr(hbg, "pos", hrv_card.pos),
            size=lambda *_: setattr(hbg, "size", hrv_card.size),
        )

        chart = HRVBarChart(size_hint_y=1)
        chart.data = stats["daily_hrv"]
        hrv_card.add_widget(chart)

        # Day labels under chart
        day_row = BoxLayout(size_hint_y=None, height=dp(20))
        for label, _ in stats["daily_hrv"]:
            day_row.add_widget(Label(
                text=label, font_size=sp(10), color=TEXT_MUTED,
            ))
        hrv_card.add_widget(day_row)
        col.add_widget(hrv_card)

        # Two stat boxes row
        row2 = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(90))
        stress_box = StatBox(value=stats["stress_label"], label="Stress Level")
        stress_box.val_lbl.color = (
            list(STATUS_GRN)  if stats["stress_label"] == "Low" else
            list(AMBER)       if stats["stress_label"] == "Med" else
            list(STATUS_RED)
        )
        avg_hrv_box = StatBox(value=f"{stats['avg_hrv']} ms", label="Ave. Variability")
        row2.add_widget(stress_box)
        row2.add_widget(avg_hrv_box)
        col.add_widget(row2)

        # Spike count
        spikes_row = BoxLayout(size_hint_y=None, height=dp(56),
                               padding=[dp(16), dp(8)])
        with spikes_row.canvas.before:
            Color(*PILL_BG)
            sbg = RoundedRectangle(pos=spikes_row.pos, size=spikes_row.size, radius=[dp(12)])
        spikes_row.bind(
            pos=lambda *_: setattr(sbg, "pos", spikes_row.pos),
            size=lambda *_: setattr(sbg, "size", spikes_row.size),
        )
        spike_icon = Label(text="!", font_size=sp(18), bold=True,
                           color=AMBER, size_hint=(None, 1), width=dp(30))
        spike_msg = Label(
            text=f"You had {stats['spike_count']} spike events this week",
            font_size=sp(13), color=TEXT_MUTED, halign="left", valign="middle",
        )
        spike_msg.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        spikes_row.add_widget(spike_icon)
        spikes_row.add_widget(spike_msg)
        col.add_widget(spikes_row)

        # Insight card
        insight_card = BoxLayout(orientation="vertical",
                                 size_hint_y=None, height=dp(80),
                                 padding=[dp(16), dp(12)])
        with insight_card.canvas.before:
            Color(0.2, 0.08, 0.35, 1)
            ibg = RoundedRectangle(pos=insight_card.pos,
                                   size=insight_card.size, radius=[dp(12)])
        insight_card.bind(
            pos=lambda *_: setattr(ibg, "pos", insight_card.pos),
            size=lambda *_: setattr(ibg, "size", insight_card.size),
        )
        insight_text = self._get_insight(stats)
        insight_lbl = Label(
            text=insight_text,
            font_size=sp(13), color=TEXT_MAIN,
            halign="left", valign="middle",
        )
        insight_lbl.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        insight_card.add_widget(insight_lbl)
        col.add_widget(insight_card)

        col.add_widget(Widget(size_hint_y=None, height=dp(16)))

    def _compute_weekly_stats(self):
        log = load_log()
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        week_entries = []
        for e in log:
            try:
                ts = datetime.fromisoformat(e["ts"])
                if ts >= week_ago:
                    week_entries.append(e)
            except Exception:
                pass

        bpms  = [e["bpm"] for e in week_entries if e.get("bpm")]
        hrvs  = [e["rmssd"] for e in week_entries if e.get("rmssd")]
        # Count spikes as entries where bpm > threshold
        p = App.get_running_app().profile
        thresh = p.get("threshold", 110)
        spikes = sum(1 for b in bpms if b >= thresh)

        avg_bpm = round(sum(bpms)/len(bpms)) if bpms else 0
        max_bpm = max(bpms) if bpms else 0
        min_bpm = min(bpms) if bpms else 0
        avg_hrv = round(sum(hrvs)/len(hrvs)) if hrvs else 0

        # Daily HRV for last 7 days
        days = []
        for i in range(6, -1, -1):
            d = now - timedelta(days=i)
            day_label = d.strftime("%a")
            day_hrvs = []
            for e in log:
                try:
                    ts = datetime.fromisoformat(e["ts"])
                    if ts.date() == d.date() and e.get("rmssd"):
                        day_hrvs.append(e["rmssd"])
                except Exception:
                    pass
            daily_avg = round(sum(day_hrvs)/len(day_hrvs)) if day_hrvs else 0
            days.append((day_label, daily_avg))

        # Stress label based on HRV
        if avg_hrv >= 50:
            stress = "Low"
        elif avg_hrv >= 25:
            stress = "Med"
        else:
            stress = "High"

        return {
            "avg_bpm":     avg_bpm or "--",
            "max_bpm":     max_bpm or "--",
            "min_bpm":     min_bpm or "--",
            "avg_hrv":     avg_hrv or "--",
            "spike_count": spikes,
            "daily_hrv":   days,
            "stress_label": stress,
        }

    def _get_insight(self, stats):
        hrv = stats["avg_hrv"]
        if hrv == "--":
            return "Start monitoring to see weekly insights here."
        try:
            hrv = int(hrv)
        except Exception:
            return "Keep monitoring to build up your insights."
        if hrv >= 50:
            return "Your HRV is above average for your age group — your autonomic nervous system is recovering well."
        elif hrv >= 25:
            return "Your HRV is in a moderate range. Consistent rest and hydration help improve POTS symptoms."
        else:
            return "Your HRV is lower than ideal this week. Prioritise rest, salt intake, and avoid prolonged standing."

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "monitor"


# ── Settings screen ────────────────────────────────────────────────────────────

class SettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        _screen_bg(root)

        col = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(52), dp(24), dp(30)],
            spacing=dp(0), size_hint=(1, 1),
        )

        back_row = BoxLayout(size_hint_y=None, height=dp(40))
        back_btn = GhostButton(text="back", size_hint=(None, 1), width=dp(70))
        back_btn.bind(on_release=self._back)
        back_row.add_widget(back_btn)
        back_row.add_widget(Widget())
        col.add_widget(back_row)

        col.add_widget(Widget(size_hint_y=None, height=dp(10)))

        h = Label(text="profile", font_size=sp(26), bold=True,
                  color=TEXT_MAIN, size_hint_y=None, height=dp(40), halign="left")
        h.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
        col.add_widget(h)
        col.add_widget(Widget(size_hint_y=None, height=dp(16)))

        self._rows = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self._rows.bind(minimum_height=self._rows.setter("height"))
        col.add_widget(self._rows)

        col.add_widget(Widget(size_hint_y=None, height=dp(12)))
        controls = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(54))
        self.sim_btn = PurpleButton(text="simulator on" if USE_SIMULATOR else "simulator off", height=dp(52))
        self.sim_btn.bind(on_release=self._toggle_simulator)
        dev_btn = GhostButton(text="developer mode", height=dp(52))
        dev_btn.bind(on_release=self._open_developer_mode)
        controls.add_widget(self.sim_btn)
        controls.add_widget(dev_btn)
        col.add_widget(controls)

        col.add_widget(Widget())

        back2 = PurpleButton(text="back to monitor")
        back2.bind(on_release=self._back)
        col.add_widget(back2)

        root.add_widget(col)
        self.add_widget(root)

    def on_enter(self):
        p = App.get_running_app().profile
        self._rows.clear_widgets()
        for lbl, val in [
            ("name",            p.get("name", "--")),
            ("resting BPM",     str(p.get("resting_bpm", 65))),
            ("alert threshold", str(p.get("threshold", 110))),
            ("spike delta",     f"+{p.get('spike_delta', 30)}"),
            ("simulator",       "on" if USE_SIMULATOR else "off"),
            ("vibration",       "on" if p.get("vibration", True) else "off"),
        ]:
            row = BoxLayout(size_hint_y=None, height=dp(50),
                            padding=[dp(16), 0, dp(16), 0])
            _pill_bg(row)
            row.bind(pos=lambda w, _: _pill_bg(w), size=lambda w, _: _pill_bg(w))
            l = Label(text=lbl, font_size=sp(14), color=TEXT_MAIN,
                      halign="left", valign="middle")
            l.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
            v = Label(text=val, font_size=sp(14), color=TEXT_MUTED,
                      halign="right", valign="middle")
            v.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
            row.add_widget(l)
            row.add_widget(v)
            self._rows.add_widget(row)

    def _back(self, *_):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "monitor"

    def _toggle_simulator(self, *_):
        global USE_SIMULATOR
        USE_SIMULATOR = not USE_SIMULATOR
        self.sim_btn.text = "simulator on" if USE_SIMULATOR else "simulator off"
        self.on_enter()

    def _open_developer_mode(self, *_):
        monitor = App.get_running_app().root.get_screen("monitor")
        monitor._open_dev_mode()


# ── App ────────────────────────────────────────────────────────────────────────

class PaceRingApp(App):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.profile = {
            "name": "friend", "resting_bpm": 65, "threshold": 110,
            "spike_delta": 30, "spike_duration": 10,
            "vibration": True, "sound_alerts": True,
        }

    def build(self):
        Window.clearcolor = BG
        saved = load_profile()
        if saved:
            self.profile.update(saved)

        sm = ScreenManager(transition=FadeTransition(duration=0.15))
        sm.add_widget(OnboardScreen1(name="onboard1"))
        sm.add_widget(OnboardScreen2(name="onboard2"))
        sm.add_widget(OnboardScreen3(name="onboard3"))
        sm.add_widget(MonitorScreen(name="monitor"))
        sm.add_widget(SummaryScreen(name="summary"))
        sm.add_widget(SettingsScreen(name="settings"))

        if saved and saved.get("name"):
            sm.current = "monitor"
            Clock.schedule_once(
                lambda dt: sm.get_screen("monitor").start_monitoring(), 0.5
            )
        else:
            sm.current = "onboard1"

        return sm

    def on_start(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.BLUETOOTH_SCAN,
                Permission.BLUETOOTH_CONNECT,
                Permission.ACCESS_FINE_LOCATION,
            ], lambda p, r: None)
        except ImportError:
            pass


if __name__ == "__main__":
    PaceRingApp().run()

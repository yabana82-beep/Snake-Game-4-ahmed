
import os
import json
import math
import wave
import struct
import random
from datetime import date

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.graphics import (
    Color, Rectangle, RoundedRectangle, Ellipse, Line
)
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


# ==========================================================
# SNAKE GAME 4.6 - NEON ULTIMATE
# RESPONSIVE ANDROID EDITION
# ==========================================================

Window.clearcolor = (0.025, 0.025, 0.09, 1)

SAVE_FILE = "snake_data.json"
GRID_COLS = 16

SKIN_COLORS = {
    "cyan": (
        (0, 1, 0.85, 1),
        (0.05, 0.65, 0.75, 1)
    ),
    "purple": (
        (0.85, 0.35, 1, 1),
        (0.48, 0.18, 0.8, 1)
    ),
    "gold": (
        (1, 0.82, 0.15, 1),
        (0.85, 0.48, 0.05, 1)
    )
}


# ==========================================================
# NEON BUTTON
# ==========================================================

class NeonButton(Button):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)

        self.color = (0.8, 1, 1, 1)
        self.bold = True
        self.font_size = dp(13)

        with self.canvas.before:
            Color(0.08, 0.15, 0.35, 0.98)

            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(10)]
            )

            Color(0, 0.85, 1, 0.85)

            self.glow_line = Line(
                rounded_rectangle=(
                    self.x, self.y,
                    self.width, self.height, dp(10)
                ),
                width=1.2
            )

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas
        )

    def update_canvas(self, *_):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

        self.glow_line.rounded_rectangle = (
            self.x, self.y,
            self.width, self.height, dp(10)
        )


# ==========================================================
# CONTROL PANEL
# ==========================================================

class ControlPanel(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(0.035, 0.045, 0.13, 1)

            self.bg = Rectangle(
                pos=self.pos,
                size=self.size
            )

            Color(0, 0.8, 1, 0.85)

            self.border_line = Line(
                points=[0, 0, 100, 0],
                width=1.3
            )

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas
        )

    def update_canvas(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size

        self.border_line.points = [
            self.x,
            self.y + self.height,
            self.x + self.width,
            self.y + self.height
        ]


# ==========================================================
# GAME BOARD
# ==========================================================

class SnakeBoard(Widget):

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)

        self.app = app

        self.cols = GRID_COLS
        self.rows = 10
        self.cell = 10

        self.snake = []

        self.direction = (1, 0)
        self.next_direction = (1, 0)

        self.food = None
        self.gold_food = None
        self.obstacles = []

        self.score = 0
        self.eaten = 0

        self.paused = False
        self.game_over = False

        self.shield = 0
        self.magnet = 0
        self.turbo = 0

        self.move_timer = 0

        self.normal_speed = 0.16
        self.turbo_speed = 0.08

        self._update_event = Clock.schedule_interval(
            self.update, 0.025
        )

        self.bind(
            pos=self.resize_board,
            size=self.resize_board
        )

    # ------------------------------------------------------
    # BOARD SIZE
    # ------------------------------------------------------

    def resize_board(self, *_):
        if self.width <= 0 or self.height <= 0:
            return

        old_rows = self.rows

        self.cell = self.width / self.cols

        self.rows = max(
            10,
            int(self.height / self.cell)
        )

        if old_rows != self.rows and self.snake:

            self.snake = [
                (x, y % self.rows)
                for x, y in self.snake
            ]

            if self.food:
                self.food = (
                    self.food[0],
                    self.food[1] % self.rows
                )

            if self.gold_food:
                self.gold_food = (
                    self.gold_food[0],
                    self.gold_food[1] % self.rows
                )

            self.obstacles = [
                (x, y % self.rows)
                for x, y in self.obstacles
            ]

            # Remove duplicate positions after resizing.
            self.obstacles = list(set(self.obstacles))

        self.redraw()

    def stop(self):
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None

    def start(self):
        self.resize_board()

        cx = self.cols // 2
        cy = self.rows // 2

        self.snake = [
            (cx, cy),
            (cx - 1, cy),
            (cx - 2, cy)
        ]

        self.direction = (1, 0)
        self.next_direction = (1, 0)

        self.score = 0
        self.eaten = 0

        self.paused = False
        self.game_over = False

        self.shield = 0
        self.magnet = 0
        self.turbo = 0

        self.move_timer = 0
        self.obstacles = []

        self.food = None
        self.gold_food = None

        self.place_food()
        self.redraw()

    # ------------------------------------------------------
    # FREE POSITIONS
    # ------------------------------------------------------

    def random_free_cell(self):
        blocked = set(self.snake)
        blocked.update(self.obstacles)

        if self.food:
            blocked.add(self.food)

        if self.gold_food:
            blocked.add(self.gold_food)

        free = [
            (x, y)
            for x in range(self.cols)
            for y in range(self.rows)
            if (x, y) not in blocked
        ]

        return random.choice(free) if free else None

    def place_food(self):
        self.food = self.random_free_cell()

    def place_gold(self):
        self.gold_food = self.random_free_cell()

    # ------------------------------------------------------
    # DIRECTION
    # ------------------------------------------------------

    def set_direction(self, direction):
        if self.game_over or self.paused:
            return

        directions = {
            "UP": (0, 1),
            "DOWN": (0, -1),
            "LEFT": (-1, 0),
            "RIGHT": (1, 0)
        }

        new_dir = directions.get(direction)

        if not new_dir:
            return

        # Compare with the pending direction too.
        # This prevents fast double-input reversal.
        current = self.next_direction

        if new_dir != (-current[0], -current[1]):
            self.next_direction = new_dir

    # ------------------------------------------------------
    # POWERS
    # ------------------------------------------------------

    def activate_power(self, power):
        if self.game_over or self.paused:
            self.app.message("START THE GAME FIRST")
            return

        if self.app.coins < 5:
            self.app.message("تحتاج 5 عملات!")
            return

        if power == "SHIELD":
            self.shield = 15

        elif power == "MAGNET":
            self.magnet = 20

        elif power == "TURBO":
            self.turbo = 12

        self.app.coins -= 5
        self.app.save_data()

        self.app.message(power + " ACTIVATED")

    def move_magnet(self):
        if self.magnet <= 0 or not self.food:
            return

        hx, hy = self.snake[0]
        fx, fy = self.food

        distance = abs(hx - fx) + abs(hy - fy)

        if distance > 3:
            return

        candidates = []

        if fx < hx:
            candidates.append((fx + 1, fy))
        elif fx > hx:
            candidates.append((fx - 1, fy))

        if fy < hy:
            candidates.append((fx, fy + 1))
        elif fy > hy:
            candidates.append((fx, fy - 1))

        for candidate in candidates:
            if (
                candidate not in self.snake
                and candidate not in self.obstacles
                and candidate != self.gold_food
            ):
                self.food = candidate
                break

    # ------------------------------------------------------
    # GAME UPDATE
    # ------------------------------------------------------

    def update(self, dt):
        if self.app.screen != "game":
            return

        if self.paused or self.game_over:
            return

        if not self.snake:
            return

        # Prevent large time jumps after app interruptions.
        dt = min(dt, 0.1)
        self.move_timer += dt

        # Gradually increase speed with level.
        level_bonus = max(0, self.app.level - 1) * 0.006

        current_speed = max(
            0.075,
            self.normal_speed - level_bonus
        )

        speed = (
            self.turbo_speed
            if self.turbo > 0
            else current_speed
        )

        if self.move_timer < speed:
            return

        self.move_timer = 0

        self.direction = self.next_direction

        dx, dy = self.direction
        hx, hy = self.snake[0]

        new_head = (hx + dx, hy + dy)

        hit_wall = (
            new_head[0] < 0
            or new_head[0] >= self.cols
            or new_head[1] < 0
            or new_head[1] >= self.rows
        )

        # Moving into the old tail position is allowed
        # if the snake is not growing this turn.
        will_eat = (
            new_head == self.food
            or new_head == self.gold_food
        )

        body_to_check = (
            self.snake if will_eat
            else self.snake[:-1]
        )

        hit_body = new_head in body_to_check
        hit_obstacle = new_head in self.obstacles

        if hit_wall or hit_body or hit_obstacle:

            if self.shield > 0:
                self.shield = 0

                if hit_wall:
                    new_head = (
                        new_head[0] % self.cols,
                        new_head[1] % self.rows
                    )

                else:
                    self.app.message("SHIELD BLOCKED HIT")
                    self.redraw()
                    return

            else:
                self.end_game()
                return

        self.snake.insert(0, new_head)

        ate = False
        normal_food_eaten = False

        if new_head == self.food:
            self.score += 1
            self.eaten += 1

            self.app.coins += 1
            self.app.total_food += 1

            ate = True
            normal_food_eaten = True

            self.food = None
            self.place_food()

            if self.eaten % 5 == 0:
                self.place_gold()
                self.app.level += 1
                self.make_obstacles()

                self.app.message(
                    "LEVEL UP! LEVEL " + str(self.app.level)
                )

        elif self.gold_food and new_head == self.gold_food:
            self.score += 5
            self.eaten += 1

            self.app.coins += 5
            self.app.total_food += 1

            self.gold_food = None
            ate = True

            if self.eaten % 5 == 0:
                self.app.level += 1
                self.make_obstacles()

                self.app.message(
                    "LEVEL UP! LEVEL " + str(self.app.level)
                )

        if not ate:
            self.snake.pop()

        if normal_food_eaten:
            self.app.add_mission_progress()

        if self.magnet > 0:
            self.magnet -= 1
            self.move_magnet()

        if self.shield > 0:
            self.shield -= 1

        if self.turbo > 0:
            self.turbo -= 1

        self.app.current_score = self.score

        if ate:
            self.app.save_data()

        self.redraw()

    def make_obstacles(self):
        if self.app.level < 2:
            return

        for _ in range(min(2, self.app.level)):
            position = self.random_free_cell()

            if (
                position
                and position not in self.obstacles
                and position not in self.snake
            ):
                self.obstacles.append(position)

    def end_game(self):
        self.game_over = True

        self.app.games_played += 1

        if self.score > self.app.best:
            self.app.best = self.score

        self.app.save_data()
        self.app.show_game_over()

    def toggle_pause(self):
        if self.game_over:
            return

        self.paused = not self.paused

        self.app.message(
            "PAUSED" if self.paused else "RESUMED"
        )

    # ------------------------------------------------------
    # DRAW BOARD
    # ------------------------------------------------------

    def redraw(self, *_):
        self.canvas.clear()

        if self.width <= 0 or self.height <= 0:
            return

        cell = self.width / self.cols

        board_w = self.cols * cell
        board_h = self.rows * cell

        ox = self.x
        oy = self.y + (self.height - board_h) / 2

        with self.canvas:

            Color(0.025, 0.035, 0.12, 1)

            Rectangle(
                pos=self.pos,
                size=self.size
            )

            # Grid
            Color(0.08, 0.12, 0.25, 1)

            for x in range(self.cols + 1):
                Line(
                    points=[
                        ox + x * cell, oy,
                        ox + x * cell, oy + board_h
                    ],
                    width=0.45
                )

            for y in range(self.rows + 1):
                Line(
                    points=[
                        ox, oy + y * cell,
                        ox + board_w, oy + y * cell
                    ],
                    width=0.45
                )

            # Obstacles
            for x, y in self.obstacles:
                Color(0.9, 0.15, 0.35, 1)

                RoundedRectangle(
                    pos=(
                        ox + x * cell + 1,
                        oy + y * cell + 1
                    ),
                    size=(cell - 2, cell - 2),
                    radius=[dp(3)]
                )

            # Normal food
            if self.food:
                fx, fy = self.food

                Color(1, 0.18, 0.35, 1)

                Ellipse(
                    pos=(
                        ox + fx * cell + cell * 0.15,
                        oy + fy * cell + cell * 0.15
                    ),
                    size=(cell * 0.7, cell * 0.7)
                )

            # Golden food
            if self.gold_food:
                gx, gy = self.gold_food

                Color(1, 0.82, 0.05, 1)

                Ellipse(
                    pos=(
                        ox + gx * cell + cell * 0.1,
                        oy + gy * cell + cell * 0.1
                    ),
                    size=(cell * 0.8, cell * 0.8)
                )

            # Snake
            head_color, body_color = SKIN_COLORS.get(
                self.app.selected_skin,
                SKIN_COLORS["cyan"]
            )

            for index, (sx, sy) in enumerate(self.snake):

                if index == 0:
                    Color(*head_color)
                else:
                    Color(*body_color)

                RoundedRectangle(
                    pos=(
                        ox + sx * cell + 1,
                        oy + sy * cell + 1
                    ),
                    size=(cell - 2, cell - 2),
                    radius=[dp(4)]
                )

            # Shield
            if self.shield > 0 and self.snake:
                hx, hy = self.snake[0]

                Color(0.2, 0.65, 1, 0.8)

                Line(
                    circle=(
                        ox + (hx + 0.5) * cell,
                        oy + (hy + 0.5) * cell,
                        cell * 0.75
                    ),
                    width=1.5
                )


# ==========================================================
# MAIN APP
# ==========================================================

class SnakeApp(App):

    def build(self):
        self.title = "Snake Game 4.6 Neon Ultimate"

        self.data_path = os.path.join(
            self.user_data_dir,
            SAVE_FILE
        )

        self.coins = 100
        self.best = 0
        self.level = 1

        self.games_played = 0
        self.total_food = 0

        self.daily_date = ""
        self.mission_date = ""
        self.mission_progress = 0
        self.mission_claimed = False

        self.current_score = 0

        self.owned_items = ["cyan"]
        self.selected_skin = "cyan"

        self.music_enabled = True
        self.sound = None

        self.screen = "menu"

        self.board = None
        self.hud_event = None

        self.root = FloatLayout()

        # Bind only once to avoid duplicate callbacks.
        self.root.bind(size=self.on_root_resize)

        self.load_data()
        self.create_music()
        self.show_menu()

        return self.root

    # ------------------------------------------------------
    # ROOT RESIZE
    # ------------------------------------------------------

    def on_root_resize(self, *_):
        if self.screen == "game":
            self.layout_game()

    # ------------------------------------------------------
    # SAVE / LOAD
    # ------------------------------------------------------

    def load_data(self):
        try:
            if not os.path.exists(self.data_path):
                return

            with open(
                self.data_path,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            self.coins = data.get("coins", 100)
            self.best = data.get("best", 0)
            self.level = data.get("level", 1)

            self.games_played = data.get(
                "games_played", 0
            )

            self.total_food = data.get(
                "total_food", 0
            )

            self.daily_date = data.get(
                "daily_date", ""
            )

            self.mission_date = data.get(
                "mission_date", ""
            )

            self.mission_progress = data.get(
                "mission_progress", 0
            )

            self.mission_claimed = data.get(
                "mission_claimed", False
            )

            self.music_enabled = data.get(
                "music_enabled", True
            )

            self.owned_items = data.get(
                "owned_items", ["cyan"]
            )

            self.selected_skin = data.get(
                "selected_skin", "cyan"
            )

            if not isinstance(self.owned_items, list):
                self.owned_items = ["cyan"]

            if "cyan" not in self.owned_items:
                self.owned_items.append("cyan")

            if self.selected_skin not in self.owned_items:
                self.selected_skin = "cyan"

            self.coins = max(0, int(self.coins))
            self.best = max(0, int(self.best))
            self.level = max(1, int(self.level))

            self.games_played = max(
                0, int(self.games_played)
            )

            self.total_food = max(
                0, int(self.total_food)
            )

            self.mission_progress = max(
                0,
                min(5, int(self.mission_progress))
            )

        except Exception as e:
            print("LOAD ERROR:", e)

    def save_data(self):
        data = {
            "coins": self.coins,
            "best": self.best,
            "level": self.level,
            "games_played": self.games_played,
            "total_food": self.total_food,
            "daily_date": self.daily_date,
            "mission_date": self.mission_date,
            "mission_progress": self.mission_progress,
            "mission_claimed": self.mission_claimed,
            "music_enabled": self.music_enabled,
            "owned_items": self.owned_items,
            "selected_skin": self.selected_skin
        }

        try:
            os.makedirs(
                self.user_data_dir,
                exist_ok=True
            )

            temp_path = self.data_path + ".tmp"

            with open(
                temp_path,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            os.replace(
                temp_path,
                self.data_path
            )

        except Exception as e:
            print("SAVE ERROR:", e)

    # ------------------------------------------------------
    # MISSIONS
    # ------------------------------------------------------

    def refresh_mission(self):
        today = str(date.today())

        if self.mission_date != today:
            self.mission_date = today
            self.mission_progress = 0
            self.mission_claimed = False
            self.save_data()

    def add_mission_progress(self):
        self.refresh_mission()

        if self.mission_claimed:
            return

        self.mission_progress = min(
            5,
            self.mission_progress + 1
        )

        if self.mission_progress >= 5:
            self.mission_claimed = True
            self.coins += 15

            self.message(
                "MISSION COMPLETE! +15 COINS"
            )

        self.save_data()

    # ------------------------------------------------------
    # MUSIC
    # ------------------------------------------------------

    def create_music(self):
        try:
            os.makedirs(
                self.user_data_dir,
                exist_ok=True
            )

            music_path = os.path.join(
                self.user_data_dir,
                "dreamy_ambient.wav"
            )

            if not os.path.exists(music_path):

                sample_rate = 11025
                duration = 16
                total = sample_rate * duration

                chords = [
                    [261.63, 329.63, 392.00, 493.88],
                    [220.00, 261.63, 329.63, 392.00],
                    [174.61, 220.00, 261.63, 329.63],
                    [196.00, 246.94, 293.66, 392.00]
                ]

                melody = [
                    523.25, 659.25, 783.99, 659.25,
                    587.33, 659.25, 783.99, 880.00,
                    783.99, 659.25, 587.33, 523.25,
                    493.88, 587.33, 659.25, 523.25
                ]

                samples = []

                for i in range(total):
                    t = i / sample_rate

                    chord_index = int(t / 4) % 4
                    next_index = (chord_index + 1) % 4
                    local_time = t % 4

                    blend = max(
                        0.0,
                        min(
                            1.0,
                            (local_time - 3.5) / 0.5
                        )
                    )

                    pad = 0.0
                    next_pad = 0.0

                    for j, freq in enumerate(chords[chord_index]):
                        pad += (
                            math.sin(2 * math.pi * freq * t)
                            * (0.045 / (j + 1))
                        )

                    for j, freq in enumerate(chords[next_index]):
                        next_pad += (
                            math.sin(2 * math.pi * freq * t)
                            * (0.045 / (j + 1))
                        )

                    pad = (
                        pad * (1 - blend)
                        + next_pad * blend
                    )

                    bass_freq = chords[chord_index][0] / 2

                    bass = math.sin(
                        2 * math.pi * bass_freq * t
                    ) * 0.055

                    note_index = (
                        int(t / 1.0) % len(melody)
                    )

                    note_time = t % 1.0
                    frequency = melody[note_index]

                    envelope = (
                        math.exp(-3.0 * note_time)
                        * min(1.0, note_time / 0.035)
                    )

                    bell = (
                        math.sin(
                            2 * math.pi * frequency * t
                        )
                        + 0.25 * math.sin(
                            2 * math.pi * frequency * 2 * t
                        )
                    ) * envelope * 0.055

                    atmosphere = (
                        math.sin(2 * math.pi * 0.12 * t)
                        * 0.012
                    )

                    value = (
                        pad + bass + bell + atmosphere
                    )

                    fade = min(
                        1.0,
                        t / 0.25,
                        (duration - t) / 0.25
                    )

                    value *= max(0.0, fade)
                    value = max(
                        -0.8,
                        min(0.8, value)
                    )

                    samples.append(
                        int(value * 32767)
                    )

                with wave.open(music_path, "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(sample_rate)

                    wav.writeframes(
                        struct.pack(
                            "<" + "h" * len(samples),
                            *samples
                        )
                    )

            self.sound = SoundLoader.load(music_path)

            if self.sound:
                self.sound.loop = True
                self.sound.volume = 0.18

                if self.music_enabled:
                    self.sound.play()

        except Exception as e:
            print("MUSIC ERROR:", e)

    def toggle_music(self):
        self.music_enabled = not self.music_enabled

        if self.sound:
            if self.music_enabled:
                self.sound.play()
            else:
                self.sound.stop()

        self.save_data()

        self.message(
            "MUSIC ON"
            if self.music_enabled
            else "MUSIC OFF"
        )

    # ------------------------------------------------------
    # UI HELPERS
    # ------------------------------------------------------

    def clear_screen(self):
        self.root.clear_widgets()

    def add_title(self, text, y=0.84):
        label = Label(
            text=text,
            font_size=dp(27),
            bold=True,
            color=(0, 1, 0.9, 1),
            size_hint=(0.9, None),
            height=dp(55),
            pos_hint={
                "center_x": 0.5,
                "center_y": y
            }
        )

        self.root.add_widget(label)

    def add_button(self, text, callback, y, width=0.72):
        btn = NeonButton(
            text=text,
            size_hint=(width, None),
            height=dp(48),
            pos_hint={
                "center_x": 0.5,
                "center_y": y
            }
        )

        btn.bind(
            on_release=lambda *_: callback()
        )

        self.root.add_widget(btn)
        return btn

    def message(self, text):
        toast = Label(
            text=text,
            color=(0.2, 1, 0.8, 1),
            bold=True,
            font_size=dp(15),
            size_hint=(0.9, None),
            height=dp(35),
            pos_hint={
                "center_x": 0.5,
                "top": 0.97
            }
        )

        self.root.add_widget(toast)

        Clock.schedule_once(
            lambda dt:
            self.root.remove_widget(toast)
            if toast.parent else None,
            1.7
        )

    def stop_game_events(self):
        if self.hud_event:
            self.hud_event.cancel()
            self.hud_event = None

        if self.board:
            self.board.stop()
            self.board = None

    # ------------------------------------------------------
    # MAIN MENU
    # ------------------------------------------------------

    def show_menu(self):
        self.stop_game_events()

        self.screen = "menu"
        self.clear_screen()

        self.add_title("SNAKE GAME 4.6", 0.85)

        info = Label(
            text=(
                "[color=00ffff]NEON ULTIMATE EDITION[/color]\n\n"
                "COINS: " + str(self.coins)
                + "\nBEST: " + str(self.best)
                + "\nLEVEL: " + str(self.level)
            ),
            markup=True,
            font_size=dp(18),
            size_hint=(0.9, None),
            height=dp(110),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.68
            }
        )

        self.root.add_widget(info)

        self.add_button(
            "PLAY", self.start_game, 0.51
        )

        self.add_button(
            "SHOP", self.show_shop, 0.40
        )

        self.add_button(
            "DAILY REWARD", self.claim_daily, 0.29
        )

        self.add_button(
            "MISSIONS", self.show_missions, 0.18
        )

        self.add_button(
            "MUSIC: " + (
                "ON" if self.music_enabled else "OFF"
            ),
            self.toggle_music,
            0.08
        )

    # ------------------------------------------------------
    # GAME SCREEN
    # ------------------------------------------------------

    def start_game(self):
        self.stop_game_events()

        self.screen = "game"
        self.clear_screen()

        self.control_panel = ControlPanel()
        self.root.add_widget(self.control_panel)

        self.board = SnakeBoard(self)
        self.root.add_widget(self.board)

        # HUD
        self.hud = Label(
            text="SCORE: 0     COINS: " + str(self.coins),
            color=(0, 1, 0.9, 1),
            bold=True,
            font_size=dp(13),
            size_hint=(None, None)
        )

        self.root.add_widget(self.hud)

        self.level_label = Label(
            text="LEVEL " + str(self.level),
            color=(1, 0.8, 0.2, 1),
            font_size=dp(12),
            size_hint=(None, None)
        )

        self.root.add_widget(self.level_label)

        # Top buttons
        self.pause_button = NeonButton(text="PAUSE")
        self.restart_button = NeonButton(text="RESTART")
        self.menu_button = NeonButton(text="MENU")

        for btn in (
            self.pause_button,
            self.restart_button,
            self.menu_button
        ):
            btn.size_hint = (None, None)
            self.root.add_widget(btn)

        self.pause_button.bind(
            on_release=lambda *_:
            self.board.toggle_pause()
            if self.board else None
        )

        self.restart_button.bind(
            on_release=lambda *_: self.restart_game()
        )

        self.menu_button.bind(
            on_release=lambda *_: self.show_menu()
        )

        # Direction buttons with clear arrow symbols.
        self.direction_buttons = {}

        arrow_labels = {
            "UP": "↑",
            "DOWN": "↓",
            "LEFT": "←",
            "RIGHT": "→"
        }

        for name in ("UP", "DOWN", "LEFT", "RIGHT"):

            btn = NeonButton(
                text=arrow_labels[name]
            )

            btn.size_hint = (None, None)
            btn.font_size = dp(27)

            btn.bind(
                on_release=lambda instance, d=name:
                self.board.set_direction(d)
                if self.board else None
            )

            self.direction_buttons[name] = btn
            self.root.add_widget(btn)

        # Power buttons
        self.power_buttons = {}

        for power in ("SHIELD", "MAGNET", "TURBO"):

            btn = NeonButton(text=power)
            btn.size_hint = (None, None)

            btn.bind(
                on_release=lambda instance, p=power:
                self.board.activate_power(p)
                if self.board else None
            )

            self.power_buttons[power] = btn
            self.root.add_widget(btn)

        self.layout_game()

        self.board.start()

        self.hud_event = Clock.schedule_interval(
            self.update_hud, 0.15
        )

    # ------------------------------------------------------
    # RESPONSIVE LAYOUT
    # ------------------------------------------------------

    def layout_game(self, *_):
        if self.screen != "game" or not self.board:
            return

        w = self.root.width
        h = self.root.height

        if w <= 0 or h <= 0:
            return

        # Responsive bottom control area.
        control_h = min(
            dp(220),
            max(dp(155), h * 0.30)
        )

        control_h = min(
            control_h,
            h * 0.43
        )

        board_h = max(0, h - control_h)

        self.control_panel.pos = (0, 0)
        self.control_panel.size = (w, control_h)

        self.board.pos = (0, control_h)
        self.board.size = (w, board_h)

        # HUD
        self.hud.size = (
            max(dp(80), w - dp(105)),
            dp(28)
        )

        self.hud.pos = (
            dp(3),
            h - dp(35)
        )

        self.hud.font_size = dp(12)

        self.level_label.size = (
            dp(100),
            dp(24)
        )

        self.level_label.pos = (
            w - dp(103),
            h - dp(35)
        )

        # Top buttons
        top_y = max(
            h - dp(75),
            control_h + dp(3)
        )

        self.pause_button.size = (
            dp(68), dp(30)
        )

        self.pause_button.pos = (
            dp(5), top_y
        )

        self.pause_button.font_size = dp(10)

        self.restart_button.size = (
            dp(80), dp(30)
        )

        self.restart_button.pos = (
            w - dp(85), top_y
        )

        self.restart_button.font_size = dp(10)

        self.menu_button.size = (
            dp(58), dp(30)
        )

        self.menu_button.pos = (
            w / 2 - dp(29), top_y
        )

        self.menu_button.font_size = dp(10)

        # --------------------------------------------------
        # POWER ROW
        # --------------------------------------------------

        gap = dp(5)

        power_h = min(
            dp(32),
            max(dp(24), control_h * 0.17)
        )

        power_margin = dp(7)

        power_y = max(
            dp(5),
            control_h - power_h - power_margin
        )

        power_gap = dp(5)

        power_width = min(
            dp(100),
            max(
                dp(45),
                (w - dp(24) - power_gap * 2) / 3
            )
        )

        total_width = (
            power_width * 3
            + power_gap * 2
        )

        start_x = (w - total_width) / 2

        for i, power in enumerate(
            ("SHIELD", "MAGNET", "TURBO")
        ):

            btn = self.power_buttons[power]

            btn.size = (
                power_width,
                power_h
            )

            btn.pos = (
                start_x + i * (
                    power_width + power_gap
                ),
                power_y
            )

            btn.font_size = dp(9)

        # --------------------------------------------------
        # DIRECTION PAD - FIXED CROSS LAYOUT
        # --------------------------------------------------

        # The entire cross must fit between the bottom
        # and the power row.
        dpad_bottom = dp(6)
        dpad_gap = dp(4)

        available_height = max(
            dp(45),
            power_y - dpad_bottom - dp(8)
        )

        side_by_height = (
            available_height - 2 * dpad_gap
        ) / 3

        side_by_width = (
            w - 2 * dpad_gap
        ) / 3

        button_side = min(
            dp(72),
            side_by_height,
            side_by_width
        )

        button_side = max(
            dp(22),
            button_side
        )

        cx = w / 2

        # Cross positions:
        #              UP
        #       LEFT  DOWN  RIGHT
        #
        # The positions are calculated from the bottom,
        # so DOWN can never receive a negative Y value.

        middle_y = (
            dpad_bottom + button_side + dpad_gap
        )

        positions = {
            "DOWN": (
                cx - button_side / 2,
                dpad_bottom
            ),

            "LEFT": (
                cx - button_side - dpad_gap,
                middle_y
            ),

            "RIGHT": (
                cx + dpad_gap,
                middle_y
            ),

            "UP": (
                cx - button_side / 2,
                middle_y + button_side + dpad_gap
            )
        }

        for name, (x, y) in positions.items():

            btn = self.direction_buttons[name]

            # Keep every button inside the panel.
            x = max(
                0,
                min(x, w - button_side)
            )

            y = max(
                0,
                min(y, control_h - button_side)
            )

            btn.size = (
                button_side,
                button_side
            )

            btn.pos = (x, y)

            btn.font_size = max(
                dp(20),
                button_side * 0.48
            )

    # ------------------------------------------------------
    # HUD UPDATE
    # ------------------------------------------------------

    def update_hud(self, dt):
        if self.screen != "game":
            return False

        if self.board and self.hud:

            self.hud.text = (
                "SCORE: " + str(self.board.score)
                + "   COINS: " + str(self.coins)
            )

            self.level_label.text = (
                "LEVEL " + str(self.level)
            )

            if self.board.paused:
                self.pause_button.text = "RESUME"
            else:
                self.pause_button.text = "PAUSE"

        return True

    def restart_game(self):
        self.level = 1
        self.save_data()

        self.start_game()
        self.message("NEW GAME")

    # ------------------------------------------------------
    # GAME OVER
    # ------------------------------------------------------

    def show_game_over(self):
        if self.screen != "game":
            return

        overlay = Label(
            text=(
                "[color=ff3355]GAME OVER[/color]\n"
                "[color=ffffff]SCORE: "
                + str(self.board.score)
                + "[/color]\n"
                "[color=00ffff]Press RESTART to play again[/color]"
            ),
            markup=True,
            halign="center",
            valign="middle",
            bold=True,
            font_size=dp(20),
            size_hint=(0.9, None),
            height=dp(120),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.60
            }
        )

        self.root.add_widget(overlay)
        self.game_over_label = overlay

    # ------------------------------------------------------
    # DAILY REWARD
    # ------------------------------------------------------

    def claim_daily(self):
        today = str(date.today())

        if self.daily_date == today:
            self.message(
                "DAILY REWARD ALREADY CLAIMED"
            )
            return

        self.daily_date = today
        self.coins += 20

        self.save_data()

        self.message("+20 COINS DAILY REWARD")
        self.show_menu()

    # ------------------------------------------------------
    # MISSIONS
    # ------------------------------------------------------

    def show_missions(self):
        self.refresh_mission()

        self.screen = "missions"
        self.clear_screen()

        self.add_title("DAILY MISSIONS", 0.86)

        status = (
            "COMPLETED!"
            if self.mission_claimed
            else "IN PROGRESS"
        )

        info = Label(
            text=(
                "MISSION 1\n"
                "Eat 5 normal foods today\n\n"
                "Progress: "
                + str(self.mission_progress)
                + "/5\n\n"
                "Reward: 15 COINS\n\n"
                + status
                + "\n\nBEST SCORE: "
                + str(self.best)
            ),
            font_size=dp(17),
            halign="center",
            valign="middle",
            size_hint=(0.9, None),
            height=dp(250),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.56
            }
        )

        self.root.add_widget(info)

        self.add_button(
            "BACK", self.show_menu, 0.20
        )

    # ------------------------------------------------------
    # SHOP
    # ------------------------------------------------------

    def show_shop(self):
        self.screen = "shop"
        self.clear_screen()

        self.add_title("NEON SHOP", 0.90)

        info = Label(
            text=(
                "YOUR COINS: " + str(self.coins)
                + "\nSELECTED SKIN: "
                + self.selected_skin.upper()
            ),
            font_size=dp(17),
            color=(1, 0.85, 0.2, 1),
            size_hint=(0.9, None),
            height=dp(55),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.77
            }
        )

        self.root.add_widget(info)

        self.add_button(
            self.skin_button_text("cyan", 20),
            lambda: self.buy_or_select("cyan", 20),
            0.63
        )

        self.add_button(
            self.skin_button_text("purple", 30),
            lambda: self.buy_or_select("purple", 30),
            0.49
        )

        self.add_button(
            self.skin_button_text("gold", 50),
            lambda: self.buy_or_select("gold", 50),
            0.35
        )

        self.add_button(
            "BACK", self.show_menu, 0.19
        )

    def skin_button_text(self, item, price):
        if item == self.selected_skin:
            return item.upper() + " - SELECTED"

        if item in self.owned_items:
            return "SELECT " + item.upper()

        return (
            item.upper()
            + " SKIN - "
            + str(price)
            + " COINS"
        )

    def buy_or_select(self, item, price):
        if item in self.owned_items:

            self.selected_skin = item
            self.save_data()

            self.message(
                item.upper() + " SKIN SELECTED"
            )

            self.show_shop()
            return

        if self.coins < price:
            self.message("NOT ENOUGH COINS")
            return

        self.coins -= price
        self.owned_items.append(item)
        self.selected_skin = item

        self.save_data()

        self.message("PURCHASE SUCCESSFUL")
        self.show_shop()

    def buy_item(self, item, price):
        self.buy_or_select(item, price)

    def get_owned_items(self):
        return list(self.owned_items)

    def save_owned_items(self, items):
        self.owned_items = list(items)
        self.save_data()

    # ------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------

    def on_pause(self):
        if self.board and self.screen == "game":
            self.board.paused = True

        self.save_data()
        return True

    def on_stop(self):
        self.stop_game_events()
        self.save_data()

        if self.sound:
            self.sound.stop()


if __name__ == "__main__":
    SnakeApp().run()

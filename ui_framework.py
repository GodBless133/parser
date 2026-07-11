"""
ui_framework.py
================

UI-фреймворк для Telegram Parser & Inviter PRO v5.0
Автор: zippa

Содержит:
  - Палитра тёмной темы (DarkZippa)
  - Анимированные кнопки (hover, press)
  - Анимированные progress bars (плавное заполнение)
  - Пульсирующие индикаторы статуса
  - Toast-уведомления (slide-in)
  - Splash screen с анимацией логотипа и подписью "by zippa"
  - Анимированные счётчики (tween)
  - Кастомные scrollbars
  - Fade-in анимации для вкладок

Зависимости: только tkinter (stdlib) + Pillow (для splash).
"""

import tkinter as tk
from tkinter import ttk
import math
import time
import threading
from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass


# =====================================================================
# ПАЛИТРА ТЁМНОЙ ТЕМЫ "DarkZippa"
# =====================================================================
class Theme:
    """Цветовая палитра DarkZippa — глубокий тёмный фон с фиолетово-циановыми акцентами."""

    # Фоны
    BG_DEEP = "#0d1117"          # самый тёмный (фон окна)
    BG_BASE = "#161b22"          # основной фон панелей
    BG_CARD = "#1c2230"          # карточки
    BG_ELEVATED = "#242b3d"      # приподнятые элементы
    BG_INPUT = "#0d1117"         # поля ввода

    # Текст
    TEXT_PRIMARY = "#e6edf3"     # основной текст
    TEXT_SECONDARY = "#8b949e"   # вторичный
    TEXT_MUTED = "#6e7681"       # приглушённый
    TEXT_INVERSE = "#0d1117"     # текст на акцентных кнопках

    # Акценты
    ACCENT_PRIMARY = "#a371f7"   # фиолетовый (основной акцент)
    ACCENT_SECONDARY = "#39d0d8" # циан (вторичный)
    ACCENT_PINK = "#ff7eb6"      # розовый (успех выделенный)
    ACCENT_ORANGE = "#ffa657"    # оранжевый (предупреждение)
    ACCENT_BLUE = "#58a6ff"      # синий (info)
    ACCENT_GREEN = "#3fb950"     # зелёный (успех)
    ACCENT_RED = "#f85149"       # красный (ошибка)
    ACCENT_YELLOW = "#e3b341"    # жёлтый (warning)

    # Границы
    BORDER = "#30363d"
    BORDER_FOCUS = "#a371f7"
    BORDER_HOVER = "#58a6ff"

    # Шрифты
    FONT_TITLE = ("Segoe UI", 16, "bold")
    FONT_H1 = ("Segoe UI", 13, "bold")
    FONT_H2 = ("Segoe UI", 11, "bold")
    FONT_BODY = ("Segoe UI", 10)
    FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
    FONT_SMALL = ("Segoe UI", 9)
    FONT_TINY = ("Segoe UI", 8)
    FONT_MONO = ("Cascadia Mono", 9)
    FONT_MONO_SMALL = ("Cascadia Mono", 8)

    # Брендинг
    AUTHOR = "zippa"
    APP_NAME = "Telegram Parser & Inviter PRO"
    VERSION = "5.0"


# =====================================================================
# АНИМИРОВАННАЯ КНОПКА
# =====================================================================
class AnimatedButton(tk.Canvas):
    """Canvas-кнопка с hover/press анимациями.

    Поддерживает:
      - Плавный переход цвета при hover (transition через 8 кадров)
      - Лёгкое "нажатие" при press (scale 0.97)
      - Скруглённые углы
      - Иконку-эмодзи слева
      - Состояние disabled
    """

    def __init__(
        self,
        parent,
        text: str = "",
        icon: str = "",
        command: Optional[Callable] = None,
        width: int = 140,
        height: int = 36,
        bg: str = Theme.ACCENT_PRIMARY,
        fg: str = Theme.TEXT_INVERSE,
        hover_bg: Optional[str] = None,
        radius: int = 8,
        font=Theme.FONT_BODY_BOLD,
        **kwargs,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent.cget("bg") if hasattr(parent, "cget") else Theme.BG_BASE,
            highlightthickness=0,
            **kwargs,
        )
        self.text = text
        self.icon = icon
        self.command = command
        self.base_bg = bg
        self.hover_bg = hover_bg or self._lighten(bg, 0.15)
        self.fg = fg
        self.radius = radius
        self.font = font
        self.width = width
        self.height = height
        self.state_normal = True
        self._anim_job = None
        self._current_bg = bg
        self._target_bg = bg
        self._scale = 1.0

        self._draw()

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<space>", lambda e: self._on_press(e))

    @staticmethod
    def _lighten(hex_color: str, amount: float = 0.1) -> str:
        """Осветлить HEX-цвет на amount (0..1)."""
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            r = min(255, int(r + (255 - r) * amount))
            g = min(255, int(g + (255 - g) * amount))
            b = min(255, int(b + (255 - b) * amount))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _draw(self):
        self.delete("all")
        w, h = self.width, self.height
        scaled_w = int(w * self._scale)
        scaled_h = int(h * self._scale)
        offset_x = (w - scaled_w) // 2
        offset_y = (h - scaled_h) // 2

        # Тень (мягкая)
        if self.state_normal:
            self._draw_rounded_rect(offset_x + 1, offset_y + 2, scaled_w, scaled_h,
                                     self.radius, fill="#000000", stipple="gray25")

        # Основная заливка
        bg = self._current_bg if self.state_normal else Theme.BG_ELEVATED
        self._draw_rounded_rect(offset_x, offset_y, scaled_w, scaled_h,
                                self.radius, fill=bg, outline="")

        # Текст с иконкой
        full_text = f"{self.icon}  {self.text}" if self.icon else self.text
        text_color = self.fg if self.state_normal else Theme.TEXT_MUTED
        self.create_text(
            w // 2, h // 2,
            text=full_text,
            fill=text_color,
            font=self.font,
        )

    def _draw_rounded_rect(self, x, y, w, h, r, **kwargs):
        """Скруглённый прямоугольник через polygon+arcs (fallback если нет radius)."""
        if r <= 0:
            return self.create_rectangle(x, y, x + w, y + h, **kwargs)
        points = []
        # Top-left arc
        points.extend([x + r, y, x + w - r, y])
        # Top-right arc
        for i in range(r):
            angle = math.pi / 2 * (1 - i / r)
            points.extend([x + w - r + r * math.cos(angle), y + r - r * math.sin(angle)])
        # Right side
        points.extend([x + w, y + r, x + w, y + h - r])
        # Bottom-right arc
        for i in range(r):
            angle = math.pi / 2 * (1 - i / r)
            points.extend([x + w - r + r * math.sin(angle), y + h - r + r * math.cos(angle)])
        # Bottom
        points.extend([x + w - r, y + h, x + r, y + h])
        # Bottom-left arc
        for i in range(r):
            angle = math.pi / 2 * (1 - i / r)
            points.extend([x + r - r * math.cos(angle), y + h - r + r * math.sin(angle)])
        # Left
        points.extend([x, y + h - r, x, y + r])
        # Top-left arc
        for i in range(r):
            angle = math.pi / 2 * (1 - i / r)
            points.extend([x + r - r * math.sin(angle), y + r - r * math.cos(angle)])
        return self.create_polygon(points, smooth=True, **kwargs)

    def _animate_color(self, target: str, steps: int = 10, delay: int = 12):
        """Плавный переход цвета."""
        if self._anim_job:
            self.after_cancel(self._anim_job)

        def _interp(c1, c2, t):
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            return f"#{r:02x}{g:02x}{b:02x}"

        def _step(step):
            if step > steps:
                self._current_bg = target
                self._draw()
                return
            t = step / steps
            self._current_bg = _interp(self._current_bg, target, t * 0.3 + 0.1)
            self._draw()
            self._anim_job = self.after(delay, lambda: _step(step + 1))

        _step(0)

    def _on_enter(self, event):
        if self.state_normal:
            self._animate_color(self.hover_bg, steps=8, delay=10)
            self.config(cursor="hand2")

    def _on_leave(self, event):
        if self.state_normal:
            self._animate_color(self.base_bg, steps=8, delay=10)
            self.config(cursor="")

    def _on_press(self, event):
        if self.state_normal:
            self._scale = 0.96
            self._draw()

    def _on_release(self, event):
        if self.state_normal:
            self._scale = 1.0
            self._draw()
            if self.command:
                self.after(50, self.command)

    def configure(self, cnf=None, **kw):
        if cnf is not None and "state" in (cnf if isinstance(cnf, dict) else {}):
            state = cnf["state"] if isinstance(cnf, dict) else kw.get("state")
            self.state_normal = (state != "disabled")
            self._draw()
        if "text" in kw:
            self.text = kw.pop("text")
            self._draw()
        if "command" in kw:
            self.command = kw.pop("command")
        if "bg" in kw:
            self.base_bg = kw.pop("bg")
            self._current_bg = self.base_bg
            self._draw()
        # Игнорируем остальное
        return ()

    def config(self, cnf=None, **kw):
        return self.configure(cnf, **kw)

    def cget(self, key):
        if key == "text":
            return self.text
        return ""


# =====================================================================
# АНИМИРОВАННЫЙ PROGRESS BAR
# =====================================================================
class AnimatedProgress(tk.Canvas):
    """Progress bar с плавной анимацией заполнения и градиентом."""

    def __init__(self, parent, width: int = 400, height: int = 8,
                 bg: str = Theme.BG_INPUT, fill_color: str = Theme.ACCENT_PRIMARY,
                 **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.fill_color = fill_color
        self._displayed = 0.0  # текущее отображаемое значение
        self._target = 0.0
        self._anim_job = None
        self._draw()

    def _draw(self):
        self.delete("all")
        # Track
        self._draw_rounded(0, 0, self.width, self.height, self.height // 2,
                           fill=Theme.BG_ELEVATED)
        # Fill
        fill_w = max(self.height, int(self.width * self._displayed))
        if fill_w > 0:
            self._draw_rounded(0, 0, fill_w, self.height, self.height // 2,
                               fill=self.fill_color)
            # Блик (highlight на верхней половине)
            self._draw_rounded(1, 1, fill_w - 2, self.height // 2 - 1,
                               max(1, self.height // 4),
                               fill=self._lighten(self.fill_color, 0.3),
                               stipple="gray50")

    @staticmethod
    def _lighten(hex_color: str, amount: float) -> str:
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            r = min(255, int(r + (255 - r) * amount))
            g = min(255, int(g + (255 - g) * amount))
            b = min(255, int(b + (255 - b) * amount))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _draw_rounded(self, x, y, w, h, r, **kwargs):
        if r <= 0 or w <= 2 or h <= 2:
            return self.create_rectangle(x, y, x + w, y + h, **kwargs)
        r = min(r, w // 2, h // 2)
        points = []
        # TL
        for i in range(r + 1):
            angle = math.pi / 2 * (i / r)
            points.extend([x + r - r * math.cos(angle), y + r - r * math.sin(angle)])
        # TR
        for i in range(r + 1):
            angle = math.pi / 2 * (i / r)
            points.extend([x + w - r + r * math.sin(angle), y + r - r * math.cos(angle)])
        # BR
        for i in range(r + 1):
            angle = math.pi / 2 * (i / r)
            points.extend([x + w - r + r * math.cos(angle), y + h - r + r * math.sin(angle)])
        # BL
        for i in range(r + 1):
            angle = math.pi / 2 * (i / r)
            points.extend([x + r - r * math.sin(angle), y + h - r + r * math.cos(angle)])
        return self.create_polygon(points, smooth=True, **kwargs)

    def set_value(self, value: float, animated: bool = True):
        """Установить значение 0..1 (или 0..100 — автодетект)."""
        if value > 1.5:
            value = value / 100.0
        self._target = max(0.0, min(1.0, value))
        if not animated:
            self._displayed = self._target
            self._draw()
            return
        if self._anim_job:
            self.after_cancel(self._anim_job)
        self._animate()

    def _animate(self):
        diff = self._target - self._displayed
        if abs(diff) < 0.001:
            self._displayed = self._target
            self._draw()
            return
        # Easing — exponential approach
        self._displayed += diff * 0.18
        self._draw()
        self._anim_job = self.after(16, self._animate)


# =====================================================================
# ПУЛЬСИРУЮЩИЙ ИНДИКАТОР СТАТУСА
# =====================================================================
class PulseIndicator(tk.Canvas):
    """Пульсирующая точка-индикатор статуса.

    Цвет: green/yellow/red/grey
    Анимация: плавное расширение/сжатие ореола
    """

    def __init__(self, parent, size: int = 14, color: str = "green",
                 pulsing: bool = True, **kwargs):
        super().__init__(parent, width=size + 8, height=size + 8,
                         bg=parent.cget("bg") if hasattr(parent, "cget") else Theme.BG_BASE,
                         highlightthickness=0, **kwargs)
        self.size = size
        self.color_name = color
        self.pulsing = pulsing
        self._phase = 0.0
        self._anim_job = None

        self._colors = {
            "green": Theme.ACCENT_GREEN,
            "yellow": Theme.ACCENT_YELLOW,
            "red": Theme.ACCENT_RED,
            "grey": Theme.TEXT_MUTED,
            "blue": Theme.ACCENT_BLUE,
            "purple": Theme.ACCENT_PRIMARY,
        }
        self._draw()
        if self.pulsing:
            self._animate()

    def _draw(self):
        self.delete("all")
        color = self._colors.get(self.color_name, Theme.TEXT_MUTED)
        cx = (self.size + 8) // 2
        cy = (self.size + 8) // 2

        if self.pulsing:
            # Ореол (pulse)
            halo_size = self.size + int(self._phase * 8)
            halo_alpha = 1.0 - self._phase
            # Tkinter не поддерживает alpha, используем stipple
            stipple_map = ["", "gray25", "gray50", "gray75"]
            stip = stipple_map[min(3, int(halo_alpha * 4))]
            if stip:
                self.create_oval(
                    cx - halo_size // 2, cy - halo_size // 2,
                    cx + halo_size // 2, cy + halo_size // 2,
                    fill=color, outline="", stipple=stip,
                )

        # Основная точка
        self.create_oval(
            cx - self.size // 2, cy - self.size // 2,
            cx + self.size // 2, cy + self.size // 2,
            fill=color, outline="",
        )

    def _animate(self):
        self._phase += 0.05
        if self._phase >= 1.0:
            self._phase = 0.0
        self._draw()
        self._anim_job = self.after(50, self._animate)

    def set_color(self, color: str, pulsing: Optional[bool] = None):
        self.color_name = color
        if pulsing is not None:
            if pulsing and not self.pulsing:
                self.pulsing = True
                self._animate()
            elif not pulsing and self.pulsing:
                self.pulsing = False
                if self._anim_job:
                    self.after_cancel(self._anim_job)
                self._draw()
            else:
                self.pulsing = pulsing
        else:
            self._draw()


# =====================================================================
# TOAST-УВЕДОМЛЕНИЯ
# =====================================================================
class Toast:
    """Slide-in уведомление в правом нижнем углу.

    Использование:
        Toast.show(root, "Готово!", "Парсинг завершён", level="success")
    """

    _active: List["Toast"] = []

    def __init__(self, parent: tk.Misc, title: str, message: str = "",
                 level: str = "info", duration: int = 4000,
                 width: int = 320, height: int = 80):
        self.parent = parent
        self.title = title
        self.message = message
        self.level = level
        self.duration = duration
        self.width = width
        self.height = height

        # Цвета по уровню
        colors = {
            "info": (Theme.ACCENT_BLUE, "ℹ️"),
            "success": (Theme.ACCENT_GREEN, "✅"),
            "warning": (Theme.ACCENT_ORANGE, "⚠️"),
            "error": (Theme.ACCENT_RED, "❌"),
        }
        accent, icon = colors.get(level, colors["info"])

        # Сдвигаем существующие тоасты вверх
        for t in Toast._active:
            try:
                t._shift_up(self.height + 10)
            except Exception:
                pass

        # Создаём окно
        self.win = tk.Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        # Прозрачность (если поддерживается)
        try:
            self.win.attributes("-alpha", 0.0)
        except tk.TclError:
            pass

        self.win.configure(bg=Theme.BG_CARD)

        # Позиция: правый нижний угол
        self._update_position(initial=True)

        # Контент
        frame = tk.Frame(self.win, bg=Theme.BG_CARD)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Левая акцентная полоса
        accent_bar = tk.Frame(frame, bg=accent, width=4)
        accent_bar.pack(side="left", fill="y", padx=(0, 8))

        # Контент-фрейм
        content = tk.Frame(frame, bg=Theme.BG_CARD)
        content.pack(side="left", fill="both", expand=True, pady=8)

        # Иконка + заголовок
        header = tk.Frame(content, bg=Theme.BG_CARD)
        header.pack(fill="x", padx=8)
        tk.Label(header, text=icon, font=Theme.FONT_H2, bg=Theme.BG_CARD,
                 fg=accent).pack(side="left", padx=(0, 6))
        tk.Label(header, text=title, font=Theme.FONT_BODY_BOLD, bg=Theme.BG_CARD,
                 fg=Theme.TEXT_PRIMARY).pack(side="left")

        if message:
            tk.Label(content, text=message, font=Theme.FONT_SMALL, bg=Theme.BG_CARD,
                     fg=Theme.TEXT_SECONDARY, wraplength=width - 60, justify="left").pack(
                fill="x", padx=8, pady=(2, 0))

        # Закрытие по клику
        for w in (self.win, frame, content, accent_bar, header):
            w.bind("<Button-1>", lambda e: self.close())

        # Рамка
        try:
            self.win.configure(highlightbackground=Theme.BORDER, highlightthickness=1)
        except Exception:
            pass

        Toast._active.append(self)

        # Анимация появления
        self._fade_in()
        # Автозакрытие
        self.win.after(duration, lambda: self.close())

    def _update_position(self, initial: bool = False):
        self.win.update_idletasks()
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()
        x = sw - self.width - 20
        y = sh - self.height - 60
        # Учитываем активные тоасты
        for t in Toast._active:
            if t is self:
                break
            y -= (t.height + 10)
        if initial:
            # Стартовая позиция — за правым краем (для slide-in)
            x = sw + 10
        self.win.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def _shift_up(self, delta: int):
        try:
            cur = self.win.geometry()
            # Формат: WxH+X+Y
            parts = cur.split("+")
            new_y = int(parts[2]) - delta
            self.win.geometry(f"+{parts[1]}+{new_y}")
        except Exception:
            pass

    def _fade_in(self):
        """Slide-in справа + fade-in."""
        sw = self.parent.winfo_screenwidth()
        target_x = sw - self.width - 20
        cur_geom = self.win.geometry()
        cur_x = int(cur_geom.split("+")[1])
        alpha = 0.0
        steps = 15

        def _step(step):
            nonlocal alpha
            if step > steps:
                self.win.geometry(f"+{target_x}+{cur_geom.split('+')[2]}")
                try:
                    self.win.attributes("-alpha", 1.0)
                except tk.TclError:
                    pass
                return
            t = step / steps
            # ease-out
            ease = 1 - (1 - t) ** 3
            new_x = int(sw + 10 + (target_x - sw - 10) * ease)
            cur_y = cur_geom.split("+")[2]
            self.win.geometry(f"+{new_x}+{cur_y}")
            alpha = ease
            try:
                self.win.attributes("-alpha", alpha)
            except tk.TclError:
                pass
            self.win.after(16, lambda: _step(step + 1))

        _step(0)

    def close(self):
        """Fade-out и закрытие."""
        if not self.win.winfo_exists():
            return
        alpha = 1.0
        steps = 10

        def _step(step):
            nonlocal alpha
            if step > steps:
                try:
                    self.win.destroy()
                except Exception:
                    pass
                if self in Toast._active:
                    Toast._active.remove(self)
                return
            alpha = 1.0 - step / steps
            try:
                self.win.attributes("-alpha", alpha)
            except tk.TclError:
                pass
            self.win.after(16, lambda: _step(step + 1))

        _step(0)

    @classmethod
    def show(cls, parent: tk.Misc, title: str, message: str = "",
             level: str = "info", duration: int = 4000):
        return cls(parent, title, message, level, duration)


# =====================================================================
# АНИМИРОВАННЫЙ СЧЁТЧИК (TWEEN)
# =====================================================================
class AnimatedCounter:
    """Плавная анимация числовых значений (tween от текущего к целевому).

    Использование:
        counter = AnimatedCounter(label_widget)
        counter.set(123)
    """

    def __init__(self, label: tk.Label, duration_ms: int = 800, fmt: str = "{}"):
        self.label = label
        self.duration = duration_ms
        self.fmt = fmt
        self._current = 0
        self._target = 0
        self._job = None
        self._start_time = 0

    def set(self, value: int, fmt: Optional[str] = None):
        if fmt:
            self.fmt = fmt
        self._target = value
        if self._job:
            self.label.after_cancel(self._job)
        self._start_time = time.time()
        self._initial = self._current
        self._animate()

    def _animate(self):
        elapsed = (time.time() - self._start_time) * 1000
        if elapsed >= self.duration:
            self._current = self._target
            try:
                self.label.config(text=self.fmt.format(self._current))
            except Exception:
                pass
            return
        t = elapsed / self.duration
        # ease-out cubic
        ease = 1 - (1 - t) ** 3
        self._current = int(self._initial + (self._target - self._initial) * ease)
        try:
            self.label.config(text=self.fmt.format(self._current))
        except Exception:
            pass
        self._job = self.label.after(16, self._animate)


# =====================================================================
# SPLASH SCREEN с подписью "by zippa"
# =====================================================================
class SplashScreen:
    """Анимированный splash screen при запуске.

    Показывает:
      - Анимированный логотип (пульсирующий круг с градиентом)
      - Название приложения
      - Версию
      - Авторскую подпись "by zippa" с эффектом печати
      - Прогресс загрузки

    Использование:
        splash = SplashScreen(root)
        root.after(2500, splash.close)
    """

    def __init__(self, parent: tk.Tk, duration_ms: int = 3000):
        self.parent = parent
        self.duration = duration_ms
        self.win = tk.Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=Theme.BG_DEEP)

        # Размер
        w, h = 480, 320
        sw = parent.winfo_screenwidth()
        sh = parent.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        # Рамка
        try:
            self.win.configure(highlightbackground=Theme.ACCENT_PRIMARY, highlightthickness=2)
        except Exception:
            pass

        # Fade-in
        try:
            self.win.attributes("-alpha", 0.0)
        except tk.TclError:
            pass

        # Холст для анимации логотипа
        canvas = tk.Canvas(self.win, width=w, height=h, bg=Theme.BG_DEEP,
                           highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Логотип (рисуем на canvas)
        self.logo_canvas = canvas
        self._phase = 0.0
        self._draw_logo()

        # Текстовые элементы
        canvas.create_text(w // 2, 200, text=Theme.APP_NAME,
                           font=Theme.FONT_TITLE, fill=Theme.TEXT_PRIMARY)
        canvas.create_text(w // 2, 230, text=f"Version {Theme.VERSION}",
                           font=Theme.FONT_SMALL, fill=Theme.TEXT_SECONDARY)

        # "by zippa" — авторская подпись (с эффектом печати)
        self.author_text_id = canvas.create_text(
            w // 2, 270, text="", font=("Segoe UI", 12, "italic"),
            fill=Theme.ACCENT_PRIMARY,
        )

        # Прогресс загрузки
        self.progress_y = 295
        self.progress_id = canvas.create_rectangle(
            w // 2 - 100, self.progress_y,
            w // 2 - 100, self.progress_y + 3,
            fill=Theme.ACCENT_SECONDARY, outline="",
        )
        canvas.create_rectangle(
            w // 2 - 100, self.progress_y,
            w // 2 + 100, self.progress_y + 3,
            fill=Theme.BG_ELEVATED, outline="",
        )
        # Перерисовываем прогресс поверх
        self.progress_id = canvas.create_rectangle(
            w // 2 - 100, self.progress_y,
            w // 2 - 100, self.progress_y + 3,
            fill=Theme.ACCENT_SECONDARY, outline="",
        )
        self.progress_canvas = canvas

        # Старт анимаций
        self._animate_logo()
        self._fade_in()
        self._type_author()
        self._animate_progress()

        # Автозакрытие
        self.win.after(duration_ms, self.close)

    def _draw_logo(self):
        """Рисует пульсирующий круг-логотип."""
        self.logo_canvas.delete("logo")
        cx, cy = 240, 100
        base_r = 35
        r = base_r + int(self._phase * 8)
        # Ореол
        stipple_map = ["", "gray25", "gray50", "gray75"]
        for i in range(4, 0, -1):
            halo_r = r + i * 6
            stip = stipple_map[min(3, 4 - i)]
            if stip:
                self.logo_canvas.create_oval(
                    cx - halo_r, cy - halo_r, cx + halo_r, cy + halo_r,
                    fill=Theme.ACCENT_PRIMARY, outline="", stipple=stip, tags="logo",
                )
        # Основной круг (градиент через несколько окружностей)
        for i in range(8, 0, -1):
            ratio = i / 8
            cr = int(r * ratio)
            # Цвет от фиолетового к циану
            t = 1 - ratio
            r1, g1, b1 = 0xa3, 0x71, 0xf7  # фиолетовый
            r2, g2, b2 = 0x39, 0xd0, 0xd8  # циан
            rr = int(r1 + (r2 - r1) * t)
            gg = int(g1 + (g2 - g1) * t)
            bb = int(b1 + (b2 - b1) * t)
            color = f"#{rr:02x}{gg:02x}{bb:02x}"
            self.logo_canvas.create_oval(
                cx - cr, cy - cr, cx + cr, cy + cr,
                fill=color, outline="", tags="logo",
            )
        # Иконка молнии в центре
        self.logo_canvas.create_text(
            cx, cy, text="⚡", font=("Segoe UI", 22), fill=Theme.TEXT_INVERSE, tags="logo",
        )

    def _animate_logo(self):
        self._phase += 0.04
        if self._phase >= 1.0:
            self._phase = 0.0
        self._draw_logo()
        self.win.after(50, self._animate_logo)

    def _fade_in(self):
        alpha = 0.0
        steps = 20

        def _step(step):
            nonlocal alpha
            if step > steps:
                try:
                    self.win.attributes("-alpha", 1.0)
                except tk.TclError:
                    pass
                return
            alpha = step / steps
            try:
                self.win.attributes("-alpha", alpha)
            except tk.TclError:
                pass
            self.win.after(16, lambda: _step(step + 1))

        _step(0)

    def _type_author(self):
        """Эффект печати для 'by zippa'."""
        target = "✦ crafted by zippa ✦"
        current = [""]

        def _step():
            if len(current[0]) < len(target):
                current[0] = target[: len(current[0]) + 1]
                try:
                    self.progress_canvas.itemconfig(self.author_text_id, text=current[0])
                except Exception:
                    return
                # Случайная задержка для эффекта печати
                delay = 60 + (hash(current[0]) % 40)
                self.win.after(delay, _step)

        self.win.after(500, _step)

    def _animate_progress(self):
        """Анимация прогресс-бара загрузки."""
        target_x = 100  # от -100 до +100
        steps = int(self.duration / 16)

        def _step(step):
            if step > steps:
                return
            t = step / steps
            ease = 1 - (1 - t) ** 2
            cur_w = int(200 * ease)
            try:
                self.progress_canvas.coords(
                    self.progress_id,
                    240 - 100, self.progress_y,
                    240 - 100 + cur_w, self.progress_y + 3,
                )
            except Exception:
                return
            self.win.after(16, lambda: _step(step + 1))

        _step(0)

    def close(self):
        """Fade-out и закрытие."""
        if not self.win.winfo_exists():
            return
        alpha = 1.0
        steps = 10

        def _step(step):
            nonlocal alpha
            if step > steps:
                try:
                    self.win.destroy()
                except Exception:
                    pass
                return
            alpha = 1.0 - step / steps
            try:
                self.win.attributes("-alpha", alpha)
            except tk.TclError:
                pass
            self.win.after(16, lambda: _step(step + 1))

        _step(0)


# =====================================================================
# ПРИМЕНЕНИЕ ТЁМНОЙ ТЕМЫ К ttk
# =====================================================================
def apply_dark_theme(style: ttk.Style):
    """Применить тёмную тему DarkZippa ко всем ttk-виджетам."""
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Базовые стили
    style.configure(".", background=Theme.BG_BASE, foreground=Theme.TEXT_PRIMARY,
                    fieldbackground=Theme.BG_INPUT, bordercolor=Theme.BORDER,
                    lightcolor=Theme.BORDER, darkcolor=Theme.BORDER,
                    troughcolor=Theme.BG_INPUT, selectbackground=Theme.ACCENT_PRIMARY,
                    selectforeground=Theme.TEXT_INVERSE, font=Theme.FONT_BODY)

    # TFrame
    style.configure("TFrame", background=Theme.BG_BASE)

    # TLabel
    style.configure("TLabel", background=Theme.BG_BASE, foreground=Theme.TEXT_PRIMARY)
    style.configure("Title.TLabel", font=Theme.FONT_TITLE, foreground=Theme.TEXT_PRIMARY,
                    background=Theme.BG_BASE)
    style.configure("H1.TLabel", font=Theme.FONT_H1, foreground=Theme.TEXT_PRIMARY,
                    background=Theme.BG_BASE)
    style.configure("Muted.TLabel", font=Theme.FONT_SMALL,
                    foreground=Theme.TEXT_SECONDARY, background=Theme.BG_BASE)

    # TLabelframe
    style.configure("TLabelframe", background=Theme.BG_BASE,
                    foreground=Theme.ACCENT_SECONDARY, bordercolor=Theme.BORDER)
    style.configure("TLabelframe.Label", background=Theme.BG_BASE,
                    foreground=Theme.ACCENT_SECONDARY, font=Theme.FONT_H2)

    # TButton
    style.configure("TButton", background=Theme.BG_ELEVATED,
                    foreground=Theme.TEXT_PRIMARY, bordercolor=Theme.BORDER,
                    focuscolor=Theme.ACCENT_PRIMARY, font=Theme.FONT_BODY,
                    padding=(12, 6))
    style.map("TButton",
              background=[("active", Theme.ACCENT_PRIMARY), ("disabled", Theme.BG_ELEVATED)],
              foreground=[("disabled", Theme.TEXT_MUTED)])

    # Accent buttons
    style.configure("Accent.TButton", background=Theme.ACCENT_PRIMARY,
                    foreground=Theme.TEXT_INVERSE, font=Theme.FONT_BODY_BOLD,
                    padding=(14, 8), bordercolor=Theme.ACCENT_PRIMARY)
    style.map("Accent.TButton",
              background=[("active", Theme.ACCENT_PINK), ("disabled", Theme.BG_ELEVATED)],
              foreground=[("disabled", Theme.TEXT_MUTED)])

    # Success / Error / Warning
    style.configure("Success.TButton", background=Theme.ACCENT_GREEN,
                    foreground=Theme.TEXT_INVERSE, font=Theme.FONT_BODY_BOLD,
                    padding=(14, 8))
    style.map("Success.TButton",
              background=[("active", "#5dd674"), ("disabled", Theme.BG_ELEVATED)],
              foreground=[("disabled", Theme.TEXT_MUTED)])

    style.configure("Error.TButton", background=Theme.ACCENT_RED,
                    foreground=Theme.TEXT_INVERSE, font=Theme.FONT_BODY_BOLD,
                    padding=(14, 8))
    style.map("Error.TButton",
              background=[("active", "#ff6b63"), ("disabled", Theme.BG_ELEVATED)],
              foreground=[("disabled", Theme.TEXT_MUTED)])

    style.configure("Warning.TButton", background=Theme.ACCENT_ORANGE,
                    foreground=Theme.TEXT_INVERSE, font=Theme.FONT_BODY_BOLD,
                    padding=(14, 8))

    # TEntry
    style.configure("TEntry", fieldbackground=Theme.BG_INPUT,
                    foreground=Theme.TEXT_PRIMARY, bordercolor=Theme.BORDER,
                    lightcolor=Theme.BORDER, darkcolor=Theme.BORDER,
                    insertcolor=Theme.ACCENT_PRIMARY, padding=6)
    style.map("TEntry",
              bordercolor=[("focus", Theme.ACCENT_PRIMARY)],
              lightcolor=[("focus", Theme.ACCENT_PRIMARY)],
              darkcolor=[("focus", Theme.ACCENT_PRIMARY)])

    # TCombobox
    style.configure("TCombobox", fieldbackground=Theme.BG_INPUT,
                    background=Theme.BG_ELEVATED, foreground=Theme.TEXT_PRIMARY,
                    arrowcolor=Theme.ACCENT_PRIMARY, bordercolor=Theme.BORDER,
                    padding=6)
    style.map("TCombobox",
              fieldbackground=[("readonly", Theme.BG_INPUT)],
              bordercolor=[("focus", Theme.ACCENT_PRIMARY)])
    # Выпадающий список — option_add на уровне root (не style)
    try:
        root = style.master
        if root is not None:
            root.option_add("*TCombobox*Listbox.background", Theme.BG_ELEVATED)
            root.option_add("*TCombobox*Listbox.foreground", Theme.TEXT_PRIMARY)
            root.option_add("*TCombobox*Listbox.selectBackground", Theme.ACCENT_PRIMARY)
            root.option_add("*TCombobox*Listbox.selectForeground", Theme.TEXT_INVERSE)
            root.option_add("*TCombobox*Listbox.font", Theme.FONT_BODY)
    except Exception:
        pass

    # TCheckbutton
    style.configure("TCheckbutton", background=Theme.BG_BASE,
                    foreground=Theme.TEXT_PRIMARY, indicatorcolor=Theme.BG_INPUT,
                    focuscolor=Theme.ACCENT_PRIMARY, font=Theme.FONT_BODY)
    style.map("TCheckbutton",
              background=[("active", Theme.BG_BASE)],
              indicatorcolor=[("selected", Theme.ACCENT_PRIMARY),
                              ("pressed", Theme.ACCENT_PRIMARY)])

    # TRadiobutton
    style.configure("TRadiobutton", background=Theme.BG_BASE,
                    foreground=Theme.TEXT_PRIMARY, indicatorcolor=Theme.BG_INPUT,
                    focuscolor=Theme.ACCENT_PRIMARY, font=Theme.FONT_BODY)
    style.map("TRadiobutton",
              background=[("active", Theme.BG_BASE)],
              indicatorcolor=[("selected", Theme.ACCENT_PRIMARY)])

    # TNotebook (вкладки)
    style.configure("TNotebook", background=Theme.BG_DEEP, bordercolor=Theme.BORDER,
                    tabmargins=(2, 5, 2, 0))
    style.configure("TNotebook.Tab", background=Theme.BG_ELEVATED,
                    foreground=Theme.TEXT_SECONDARY, padding=(20, 10),
                    font=Theme.FONT_BODY, bordercolor=Theme.BORDER)
    style.map("TNotebook.Tab",
              background=[("selected", Theme.BG_BASE), ("active", Theme.BG_ELEVATED)],
              foreground=[("selected", Theme.ACCENT_PRIMARY)],
              expand=[("selected", (1, 1, 1, 0))])

    # Treeview
    style.configure("Treeview", background=Theme.BG_BASE,
                    fieldbackground=Theme.BG_BASE, foreground=Theme.TEXT_PRIMARY,
                    bordercolor=Theme.BORDER, rowheight=28, font=Theme.FONT_BODY)
    style.configure("Treeview.Heading", background=Theme.BG_ELEVATED,
                    foreground=Theme.ACCENT_SECONDARY, font=Theme.FONT_BODY_BOLD,
                    relief="flat", padding=(8, 6))
    style.map("Treeview",
              background=[("selected", Theme.ACCENT_PRIMARY)],
              foreground=[("selected", Theme.TEXT_INVERSE)])
    style.map("Treeview.Heading",
              background=[("active", Theme.BG_CARD)])

    # Scrollbar
    style.configure("Vertical.TScrollbar", background=Theme.BG_ELEVATED,
                    troughcolor=Theme.BG_INPUT, bordercolor=Theme.BG_INPUT,
                    arrowcolor=Theme.TEXT_SECONDARY, gripcount=0)
    style.map("Vertical.TScrollbar",
              background=[("active", Theme.ACCENT_PRIMARY)])
    style.configure("Horizontal.TScrollbar", background=Theme.BG_ELEVATED,
                    troughcolor=Theme.BG_INPUT, bordercolor=Theme.BG_INPUT,
                    arrowcolor=Theme.TEXT_SECONDARY)
    style.map("Horizontal.TScrollbar",
              background=[("active", Theme.ACCENT_PRIMARY)])

    # Progressbar
    style.configure("Horizontal.TProgressbar", background=Theme.ACCENT_PRIMARY,
                    troughcolor=Theme.BG_INPUT, bordercolor=Theme.BG_INPUT,
                    lightcolor=Theme.ACCENT_PRIMARY, darkcolor=Theme.ACCENT_PRIMARY)

    # Spinbox
    style.configure("TSpinbox", fieldbackground=Theme.BG_INPUT,
                    foreground=Theme.TEXT_PRIMARY, arrowcolor=Theme.ACCENT_PRIMARY,
                    bordercolor=Theme.BORDER)


# =====================================================================
# СТИЛИЗОВАННЫЙ SCROLLEDTEXT
# =====================================================================
def styled_scrolledtext(parent, **kwargs) -> tk.Text:
    """Создать Text-виджет с тёмной темой и стилизованным скроллбаром."""
    defaults = dict(
        bg=Theme.BG_INPUT,
        fg=Theme.TEXT_PRIMARY,
        insertbackground=Theme.ACCENT_PRIMARY,
        selectbackground=Theme.ACCENT_PRIMARY,
        selectforeground=Theme.TEXT_INVERSE,
        font=Theme.FONT_MONO,
        relief="flat",
        highlightthickness=1,
        highlightbackground=Theme.BORDER,
        highlightcolor=Theme.ACCENT_PRIMARY,
        padx=8,
        pady=6,
        wrap=tk.WORD,
    )
    defaults.update(kwargs)
    text = tk.Text(parent, **defaults)

    # Стилизованный скроллбар
    sb = ttk.Scrollbar(parent, command=text.yview)
    text.config(yscrollcommand=sb.set)

    return text, sb


# =====================================================================
# ABOUT DIALOG
# =====================================================================
def show_about_dialog(parent: tk.Tk):
    """Красивое окно 'О программе' с авторской подписью."""
    win = tk.Toplevel(parent)
    win.title("О программе")
    win.configure(bg=Theme.BG_DEEP)
    win.transient(parent)
    win.grab_set()
    win.resizable(False, False)

    w, h = 460, 380
    sw = parent.winfo_screenwidth()
    sh = parent.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    try:
        win.attributes("-alpha", 0.0)
    except tk.TclError:
        pass

    # Анимированный логотип
    logo_canvas = tk.Canvas(win, width=w, height=120, bg=Theme.BG_DEEP,
                            highlightthickness=0)
    logo_canvas.pack(fill="x")

    phase = [0.0]
    def draw_logo():
        logo_canvas.delete("all")
        cx, cy = w // 2, 60
        base_r = 30
        r = base_r + int(phase[0] * 6)
        stipple_map = ["", "gray25", "gray50", "gray75"]
        for i in range(4, 0, -1):
            halo_r = r + i * 5
            stip = stipple_map[min(3, 4 - i)]
            if stip:
                logo_canvas.create_oval(
                    cx - halo_r, cy - halo_r, cx + halo_r, cy + halo_r,
                    fill=Theme.ACCENT_PRIMARY, outline="", stipple=stip,
                )
        for i in range(8, 0, -1):
            ratio = i / 8
            cr = int(r * ratio)
            t = 1 - ratio
            r1, g1, b1 = 0xa3, 0x71, 0xf7
            r2, g2, b2 = 0x39, 0xd0, 0xd8
            rr = int(r1 + (r2 - r1) * t)
            gg = int(g1 + (g2 - g1) * t)
            bb = int(b1 + (b2 - b1) * t)
            color = f"#{rr:02x}{gg:02x}{bb:02x}"
            logo_canvas.create_oval(cx - cr, cy - cr, cx + cr, cy + cr,
                                    fill=color, outline="")
        logo_canvas.create_text(cx, cy, text="⚡", font=("Segoe UI", 20),
                                fill=Theme.TEXT_INVERSE)
        phase[0] += 0.05
        if phase[0] >= 1.0:
            phase[0] = 0.0
        win.after(50, draw_logo)
    draw_logo()

    # Информация
    info_frame = tk.Frame(win, bg=Theme.BG_DEEP)
    info_frame.pack(fill="both", expand=True, padx=20, pady=10)

    tk.Label(info_frame, text=Theme.APP_NAME, font=Theme.FONT_TITLE,
             bg=Theme.BG_DEEP, fg=Theme.TEXT_PRIMARY).pack()
    tk.Label(info_frame, text=f"Version {Theme.VERSION} (Multi-Account Edition)",
             font=Theme.FONT_BODY, bg=Theme.BG_DEEP,
             fg=Theme.TEXT_SECONDARY).pack(pady=(0, 16))

    # Карточка с автором
    author_card = tk.Frame(info_frame, bg=Theme.BG_CARD, highlightthickness=1,
                           highlightbackground=Theme.ACCENT_PRIMARY)
    author_card.pack(fill="x", pady=10, ipady=8)

    tk.Label(author_card, text="✦  crafted by zippa  ✦",
             font=("Segoe UI", 14, "italic bold"), bg=Theme.BG_CARD,
             fg=Theme.ACCENT_PRIMARY).pack(pady=(8, 4))
    tk.Label(author_card, text="Telegram: @zippa  •  2024-2025",
             font=Theme.FONT_SMALL, bg=Theme.BG_CARD,
             fg=Theme.TEXT_SECONDARY).pack(pady=(0, 8))

    # Особенности
    features = [
        "✅  Multi-account: Telethon / Pyrogram / TData",
        "✅  Ротация аккаунтов с пер-аккаунтной статистикой",
        "✅  Тёмная тема DarkZippa с анимациями",
        "✅  Поддержка прокси SOCKS5 / HTTP",
        "✅  Сухой прогон и фильтр по last_seen",
    ]
    for f in features:
        tk.Label(info_frame, text=f, font=Theme.FONT_SMALL, bg=Theme.BG_DEEP,
                 fg=Theme.TEXT_PRIMARY, anchor="w").pack(fill="x", pady=1)

    # Закрыть
    def close():
        alpha = 1.0
        def fade(step):
            nonlocal alpha
            if step > 10:
                win.destroy()
                return
            alpha = 1.0 - step / 10
            try:
                win.attributes("-alpha", alpha)
            except tk.TclError:
                pass
            win.after(16, lambda: fade(step + 1))
        fade(0)

    AnimatedButton(info_frame, text="Закрыть", icon="✕", command=close,
                   bg=Theme.BG_ELEVATED, hover_bg=Theme.ACCENT_PRIMARY,
                   width=120, height=34).pack(pady=14)

    # Fade-in
    def fade_in(step):
        if step > 20:
            try:
                win.attributes("-alpha", 1.0)
            except tk.TclError:
                pass
            return
        try:
            win.attributes("-alpha", step / 20)
        except tk.TclError:
            pass
        win.after(16, lambda: fade_in(step + 1))
    fade_in(0)

    win.bind("<Escape>", lambda e: close())
    win.focus_force()

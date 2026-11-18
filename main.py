"""
main.py
错题题号转换助手 - Windows 桌面界面
基于 CustomTkinter 构建，提供后缀触发词与全局快捷键配置、文案模板定制及实时预览。
"""

import ctypes
import os
import sys
import tempfile
import threading
import tkinter as tk
import traceback
from tkinter import messagebox


class _NullStream:
    """在 PyInstaller --noconsole (console=False) 模式下为 None 的 stdout/stderr 提供安全空流"""

    encoding = "utf-8"

    def write(self, _data) -> int:
        return 0

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        return False


if sys.stdout is None:
    sys.stdout = _NullStream()
if sys.stderr is None:
    sys.stderr = _NullStream()


def _report_fatal_error(err: BaseException) -> None:
    """在无控制台模式下记录启动异常并弹窗提示（支持回退目录与原生 Win32 弹窗）"""
    base_dir = (
        os.path.dirname(os.path.abspath(sys.executable))
        if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.abspath(__file__))
    )
    appdata_dir = os.path.join(
        os.environ.get("APPDATA")
        or os.environ.get("LOCALAPPDATA")
        or os.path.expanduser("~"),
        "错题快速转换助手",
    )
    candidates = [
        os.path.join(base_dir, "crash.log"),
        os.path.join(appdata_dir, "crash.log"),
        os.path.join(tempfile.gettempdir(), "错题快速转换助手_crash.log"),
    ]
    detail = traceback.format_exc()
    saved_log_path = None
    for path in candidates:
        try:
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(detail)
            saved_log_path = path
            break
        except Exception:
            continue

    log_hint = f"\n\n详细日志已保存至：\n{saved_log_path}" if saved_log_path else f"\n\n错误详情：\n{detail[:600]}"
    msg = f"程序启动异常：{err}{log_hint}"

    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("启动失败", msg)
        root.destroy()
        return
    except Exception:
        pass

    if sys.platform.startswith("win"):
        try:
            ctypes.windll.user32.MessageBoxW(0, msg, "错题快速转换助手 - 启动失败", 0x10)
        except Exception:
            pass


try:
    import darkdetect

    _orig_darkdetect_theme = getattr(darkdetect, "theme", None)

    def _safe_darkdetect_theme():
        try:
            res = _orig_darkdetect_theme() if callable(_orig_darkdetect_theme) else "Light"
            return res if res in ("Dark", "Light") else "Light"
        except Exception:
            return "Light"

    darkdetect.theme = _safe_darkdetect_theme

    import customtkinter as ctk
    from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker

    _orig_activate_dpi = ScalingTracker.activate_high_dpi_awareness
    _orig_get_dpi_scaling = ScalingTracker.get_window_dpi_scaling

    @classmethod
    def _safe_activate_dpi(cls):
        try:
            _orig_activate_dpi()
        except Exception:
            cls.deactivate_automatic_dpi_awareness = True

    @classmethod
    def _safe_get_window_dpi_scaling(cls, window) -> float:
        try:
            val = _orig_get_dpi_scaling(window)
            if not isinstance(val, (int, float)) or val <= 0.25 or val > 5.0:
                return 1.0
            return float(val)
        except Exception:
            return 1.0

    ScalingTracker.activate_high_dpi_awareness = _safe_activate_dpi
    ScalingTracker.get_window_dpi_scaling = _safe_get_window_dpi_scaling

    import keyboard
    import pyperclip

    from core_engine import (
        HotkeyManager,
        format_output,
        load_config,
        parse_numbers,
        save_config,
    )
except Exception as _boot_exc:
    _report_fatal_error(_boot_exc)
    sys.exit(1)

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# Warm Paper (Light) / Warm Graphite (Dark) 色阶
PALETTE = {
    "bg": ("#F7F4EE", "#161513"),
    "card": ("#FDFBF7", "#1C1A18"),
    "surface": ("#F2EDE4", "#262421"),
    "surface_hover": ("#E8E1D5", "#302D29"),
    "border": ("#E4DDD0", "#2E2B27"),
    "text_primary": ("#1F1B16", "#EFE9DE"),
    "text_secondary": ("#5E554A", "#AAA398"),
    "text_muted": ("#7B7266", "#8A847A"),
    "accent": ("#2563EB", "#3B82F6"),
    "accent_hover": ("#1D4ED8", "#2563EB"),
    "positive": ("#16A34A", "#4ADE80"),
    "negative": ("#DC2626", "#F87171"),
    "warning": ("#B45309", "#FBBF24"),
}


class ModernHotkeyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("错题题号转换助手")
        self.geometry("720x820")
        self.minsize(640, 740)
        self.configure(fg_color=PALETTE["bg"])

        self.config_data = load_config()
        self.is_recording = False
        self.recording_thread = None

        # 字体体系：以字号与色彩区分层次，减少粗体滥用
        self.font_title = ctk.CTkFont(family="Microsoft YaHei UI", size=20, weight="bold")
        self.font_section = ctk.CTkFont(family="Microsoft YaHei UI", size=15, weight="bold")
        self.font_normal = ctk.CTkFont(family="Microsoft YaHei UI", size=14)
        self.font_label = ctk.CTkFont(family="Microsoft YaHei UI", size=13)
        self.font_small = ctk.CTkFont(family="Microsoft YaHei UI", size=12)
        self.font_mono = ctk.CTkFont(family="Consolas", size=13)
        self.font_preview = ctk.CTkFont(family="Microsoft YaHei UI", size=15)

        self._create_widgets()

        self.hotkey_mgr = HotkeyManager(
            config_getter=lambda: self.config_data,
            on_status_change=self._on_hotkey_status_changed,
        )
        self.after(100, self.hotkey_mgr.start)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=24, pady=(16, 8))

        self._build_header(self.main_scroll)
        self._build_status_bar(self.main_scroll)
        self._build_trigger_card(self.main_scroll)
        self._build_template_card(self.main_scroll)
        self._build_test_card(self.main_scroll)
        self._build_footer(self)

    def _make_card(self, parent, bottom_gap: int = 16) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=PALETTE["card"],
            border_width=1,
            border_color=PALETTE["border"],
        )
        card.pack(fill="x", pady=(0, bottom_gap))
        return card

    def _make_keycap(self, parent, text: str) -> ctk.CTkFrame:
        cap = ctk.CTkFrame(
            parent,
            corner_radius=6,
            fg_color=PALETTE["surface"],
            border_width=1,
            border_color=PALETTE["border"],
        )
        ctk.CTkLabel(
            cap,
            text=text,
            font=self.font_mono,
            text_color=PALETTE["text_primary"],
        ).pack(padx=8, pady=2)
        return cap

    def _secondary_button_kwargs(self) -> dict:
        return {
            "corner_radius": 8,
            "font": self.font_label,
            "fg_color": PALETTE["surface"],
            "text_color": PALETTE["text_primary"],
            "hover_color": PALETTE["surface_hover"],
            "border_width": 1,
            "border_color": PALETTE["border"],
        }

    # ---------------- 页面模块构建 ----------------

    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(4, 16))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", fill="y")

        ctk.CTkLabel(
            title_box,
            text="错题题号转换助手",
            font=self.font_title,
            text_color=PALETTE["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="在批改输入框键入数字与触发词，自动展开为规范评语",
            font=self.font_small,
            text_color=PALETTE["text_muted"],
        ).pack(anchor="w", pady=(4, 0))

        self.theme_menu = ctk.CTkOptionMenu(
            header,
            values=["浅色模式", "深色模式", "跟随系统"],
            width=112,
            height=32,
            corner_radius=8,
            font=self.font_label,
            fg_color=PALETTE["surface"],
            button_color=PALETTE["surface"],
            button_hover_color=PALETTE["surface_hover"],
            text_color=PALETTE["text_primary"],
            command=self._change_appearance_mode,
        )
        self.theme_menu.set("浅色模式")
        self.theme_menu.pack(side="right", anchor="n")

    def _build_status_bar(self, parent):
        self.status_card = self._make_card(parent, bottom_gap=16)

        inner = ctk.CTkFrame(self.status_card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        self.lbl_status_dot = ctk.CTkLabel(
            inner,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color=PALETTE["positive"],
        )
        self.lbl_status_dot.pack(side="left", padx=(0, 8))

        self.lbl_status_text = ctk.CTkLabel(
            inner,
            text="正在启动后台监听",
            font=self.font_normal,
            text_color=PALETTE["text_primary"],
        )
        self.lbl_status_text.pack(side="left")

        self.btn_toggle_listen = ctk.CTkButton(
            inner,
            text="暂停监听",
            width=96,
            height=32,
            command=self._toggle_listener,
            **self._secondary_button_kwargs(),
        )
        self.btn_toggle_listen.pack(side="right")

    def _build_trigger_card(self, parent):
        card = self._make_card(parent, bottom_gap=16)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(
            body,
            text="触发方式",
            font=self.font_section,
            text_color=PALETTE["text_primary"],
        ).pack(anchor="w", pady=(0, 12))

        # 方式 1：后缀触发词
        box1 = ctk.CTkFrame(
            body,
            corner_radius=8,
            fg_color=PALETTE["surface"],
            border_width=1,
            border_color=PALETTE["border"],
        )
        box1.pack(fill="x", pady=(0, 12))

        box1_inner = ctk.CTkFrame(box1, fg_color="transparent")
        box1_inner.pack(fill="x", padx=12, pady=12)

        self.switch_trigger = ctk.CTkSwitch(
            box1_inner,
            text="后缀触发词",
            font=self.font_normal,
            text_color=PALETTE["text_primary"],
            progress_color=PALETTE["accent"],
            command=self._on_trigger_config_changed,
        )
        if self.config_data.get("enable_trigger_word", True):
            self.switch_trigger.select()
        else:
            self.switch_trigger.deselect()
        self.switch_trigger.pack(anchor="w")

        row_trig = ctk.CTkFrame(box1_inner, fg_color="transparent")
        row_trig.pack(fill="x", pady=(12, 0))

        ctk.CTkLabel(
            row_trig,
            text="触发字符",
            font=self.font_label,
            text_color=PALETTE["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        self.entry_trigger_word = ctk.CTkEntry(
            row_trig,
            width=96,
            height=36,
            font=self.font_mono,
            corner_radius=8,
            fg_color=PALETTE["card"],
            border_color=PALETTE["border"],
            text_color=PALETTE["text_primary"],
            justify="center",
        )
        self.entry_trigger_word.insert(0, self.config_data.get("trigger_word", "qqq"))
        self.entry_trigger_word.pack(side="left", padx=(0, 8))
        self.entry_trigger_word.bind("<KeyRelease>", lambda e: self._on_trigger_config_changed())

        ctk.CTkButton(
            row_trig,
            text="保存",
            width=72,
            height=36,
            command=self._on_trigger_config_changed,
            **self._secondary_button_kwargs(),
        ).pack(side="left")

        example_row = ctk.CTkFrame(row_trig, fg_color="transparent")
        example_row.pack(side="right")
        ctk.CTkLabel(
            example_row,
            text="示例",
            font=self.font_small,
            text_color=PALETTE["text_muted"],
        ).pack(side="left", padx=(0, 8))
        self._make_keycap(example_row, "135").pack(side="left")
        ctk.CTkLabel(
            example_row,
            text="+",
            font=self.font_small,
            text_color=PALETTE["text_muted"],
        ).pack(side="left", padx=4)
        self._make_keycap(example_row, self.config_data.get("trigger_word", "qqq")).pack(side="left")
        ctk.CTkLabel(
            example_row,
            text="自动展开",
            font=self.font_small,
            text_color=PALETTE["text_muted"],
        ).pack(side="left", padx=(8, 0))

        # 方式 2：全局快捷键
        box2 = ctk.CTkFrame(
            body,
            corner_radius=8,
            fg_color=PALETTE["surface"],
            border_width=1,
            border_color=PALETTE["border"],
        )
        box2.pack(fill="x")

        box2_inner = ctk.CTkFrame(box2, fg_color="transparent")
        box2_inner.pack(fill="x", padx=12, pady=12)

        self.switch_hotkey = ctk.CTkSwitch(
            box2_inner,
            text="全局快捷键",
            font=self.font_normal,
            text_color=PALETTE["text_primary"],
            progress_color=PALETTE["accent"],
            command=self._on_trigger_config_changed,
        )
        if self.config_data.get("enable_hotkey", True):
            self.switch_hotkey.select()
        else:
            self.switch_hotkey.deselect()
        self.switch_hotkey.pack(anchor="w")

        row_hk = ctk.CTkFrame(box2_inner, fg_color="transparent")
        row_hk.pack(fill="x", pady=(12, 0))

        ctk.CTkLabel(
            row_hk,
            text="当前按键",
            font=self.font_label,
            text_color=PALETTE["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        self.entry_hotkey = ctk.CTkEntry(
            row_hk,
            width=128,
            height=36,
            font=self.font_mono,
            corner_radius=8,
            fg_color=PALETTE["card"],
            border_color=PALETTE["border"],
            text_color=PALETTE["text_primary"],
            justify="center",
        )
        self.entry_hotkey.insert(0, self.config_data.get("hotkey", "alt+q"))
        self.entry_hotkey.pack(side="left", padx=(0, 8))

        self.btn_record = ctk.CTkButton(
            row_hk,
            text="录制按键",
            width=96,
            height=36,
            corner_radius=8,
            font=self.font_label,
            fg_color=PALETTE["accent"],
            hover_color=PALETTE["accent_hover"],
            text_color="#FFFFFF",
            command=self._start_record_hotkey,
        )
        self.btn_record.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row_hk,
            text="应用",
            width=72,
            height=36,
            command=self._save_manual_hotkey,
            **self._secondary_button_kwargs(),
        ).pack(side="left")

        self.lbl_hk_tip = ctk.CTkLabel(
            box2_inner,
            text="键入数字后按此快捷键原地替换，也支持划选文本后替换",
            font=self.font_small,
            text_color=PALETTE["text_muted"],
        )
        self.lbl_hk_tip.pack(anchor="w", pady=(8, 0))

    def _build_template_card(self, parent):
        card = self._make_card(parent, bottom_gap=16)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(
            body,
            text="文案模板与格式",
            font=self.font_section,
            text_color=PALETTE["text_primary"],
        ).pack(anchor="w", pady=(0, 12))

        # 预设模板
        row_preset = ctk.CTkFrame(body, fg_color="transparent")
        row_preset.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            row_preset,
            text="快捷预设",
            font=self.font_label,
            text_color=PALETTE["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        presets = [
            ("题号模板", "本次作业的错题题号为：{nums}"),
            ("题数模板", "本次作业的错题数为：{nums}"),
            ("简洁订正", "错题订正：{nums}"),
        ]
        for name, tmpl in presets:
            ctk.CTkButton(
                row_preset,
                text=name,
                width=88,
                height=32,
                command=lambda t=tmpl: self._apply_template_preset(t),
                **self._secondary_button_kwargs(),
            ).pack(side="left", padx=(0, 8))

        # 模板输入框
        row_tmpl = ctk.CTkFrame(body, fg_color="transparent")
        row_tmpl.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            row_tmpl,
            text="文案模板",
            font=self.font_label,
            text_color=PALETTE["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        self.entry_template = ctk.CTkEntry(
            row_tmpl,
            height=36,
            corner_radius=8,
            font=self.font_normal,
            fg_color=PALETTE["surface"],
            border_color=PALETTE["border"],
            text_color=PALETTE["text_primary"],
        )
        self.entry_template.insert(0, self.config_data.get("template", "本次作业的错题题号为：{nums}"))
        self.entry_template.pack(side="left", fill="x", expand=True)
        self.entry_template.bind("<KeyRelease>", lambda e: self._on_config_param_changed())

        ctk.CTkLabel(
            body,
            text="使用 {nums} 作为题号占位符",
            font=self.font_small,
            text_color=PALETTE["text_muted"],
        ).pack(anchor="w", pady=(0, 12))

        # 分隔符与拆分模式
        row_options = ctk.CTkFrame(body, fg_color="transparent")
        row_options.pack(fill="x")

        ctk.CTkLabel(
            row_options,
            text="题号分隔符",
            font=self.font_label,
            text_color=PALETTE["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        self.cbo_sep = ctk.CTkOptionMenu(
            row_options,
            values=["，(中文逗号)", "、(顿号)", ", (英文逗号)", "  (空格)"],
            width=140,
            height=36,
            corner_radius=8,
            font=self.font_label,
            fg_color=PALETTE["surface"],
            button_color=PALETTE["surface"],
            button_hover_color=PALETTE["surface_hover"],
            text_color=PALETTE["text_primary"],
            command=lambda v: self._on_config_param_changed(),
        )
        sep_map_rev = {"，": "，(中文逗号)", "、": "、(顿号)", ", ": ", (英文逗号)", " ": "  (空格)"}
        cur_sep = self.config_data.get("separator", "，")
        self.cbo_sep.set(sep_map_rev.get(cur_sep, "，(中文逗号)"))
        self.cbo_sep.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            row_options,
            text="数字拆分规则",
            font=self.font_label,
            text_color=PALETTE["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        self.cbo_mode = ctk.CTkOptionMenu(
            row_options,
            values=["智能识别 (按题号递增)", "连续数字逐位拆分", "仅按空格/符号分隔"],
            width=192,
            height=36,
            corner_radius=8,
            font=self.font_label,
            fg_color=PALETTE["surface"],
            button_color=PALETTE["surface"],
            button_hover_color=PALETTE["surface_hover"],
            text_color=PALETTE["text_primary"],
            command=lambda v: self._on_config_param_changed(),
        )
        mode_map_rev = {
            "smart": "智能识别 (按题号递增)",
            "continuous": "连续数字逐位拆分",
            "separated": "仅按空格/符号分隔",
        }
        cur_mode = self.config_data.get("split_mode", "smart")
        self.cbo_mode.set(mode_map_rev.get(cur_mode, "智能识别 (按题号递增)"))
        self.cbo_mode.pack(side="left")

    def _build_test_card(self, parent):
        card = self._make_card(parent, bottom_gap=8)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(
            body,
            text="实时测试与预览",
            font=self.font_section,
            text_color=PALETTE["text_primary"],
        ).pack(anchor="w", pady=(0, 12))

        row_input = ctk.CTkFrame(body, fg_color="transparent")
        row_input.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            row_input,
            text="输入测试",
            font=self.font_label,
            text_color=PALETTE["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        self.entry_test = ctk.CTkEntry(
            row_input,
            height=36,
            corner_radius=8,
            font=self.font_mono,
            fg_color=PALETTE["surface"],
            border_color=PALETTE["border"],
            text_color=PALETTE["text_primary"],
            placeholder_text="输入 135 或 135qqq",
        )
        self.entry_test.insert(0, "135qqq")
        self.entry_test.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_test.bind("<KeyRelease>", lambda e: self._update_test_preview())

        ctk.CTkButton(
            row_input,
            text="转换预览",
            width=88,
            height=36,
            command=self._update_test_preview,
            **self._secondary_button_kwargs(),
        ).pack(side="left")

        preview_box = ctk.CTkFrame(
            body,
            corner_radius=8,
            fg_color=PALETTE["surface"],
            border_width=1,
            border_color=PALETTE["border"],
        )
        preview_box.pack(fill="x")

        preview_inner = ctk.CTkFrame(preview_box, fg_color="transparent")
        preview_inner.pack(fill="x", padx=12, pady=12)

        row_prev_head = ctk.CTkFrame(preview_inner, fg_color="transparent")
        row_prev_head.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            row_prev_head,
            text="输出结果",
            font=self.font_small,
            text_color=PALETTE["text_muted"],
        ).pack(side="left")

        ctk.CTkButton(
            row_prev_head,
            text="复制结果",
            width=80,
            height=32,
            command=self._copy_preview_result,
            **self._secondary_button_kwargs(),
        ).pack(side="right")

        self.lbl_preview_result = ctk.CTkLabel(
            preview_inner,
            text="",
            font=self.font_preview,
            text_color=PALETTE["text_primary"],
            wraplength=580,
            justify="left",
        )
        self.lbl_preview_result.pack(anchor="w")

        self._update_test_preview()

    def _build_footer(self, parent):
        footer = ctk.CTkFrame(parent, height=48, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=24, pady=(4, 16))

        self.switch_topmost = ctk.CTkSwitch(
            footer,
            text="窗口置顶",
            font=self.font_label,
            text_color=PALETTE["text_secondary"],
            progress_color=PALETTE["accent"],
            command=self._toggle_topmost,
        )
        self.switch_topmost.pack(side="left")

        ctk.CTkLabel(
            footer,
            text="后台运行中，在任意输入框键入即可触发",
            font=self.font_small,
            text_color=PALETTE["text_muted"],
        ).pack(side="right")

    # ---------------- 交互业务逻辑 ----------------

    def _change_appearance_mode(self, new_mode: str):
        mode_map = {"浅色模式": "Light", "深色模式": "Dark", "跟随系统": "System"}
        ctk.set_appearance_mode(mode_map.get(new_mode, "Light"))

    def _apply_template_preset(self, tmpl: str):
        self.entry_template.delete(0, tk.END)
        self.entry_template.insert(0, tmpl)
        self._on_config_param_changed()

    def _get_current_separator(self) -> str:
        val = self.cbo_sep.get()
        if "顿号" in val:
            return "、"
        if "英文逗号" in val:
            return ", "
        if "空格" in val:
            return " "
        return "，"

    def _get_current_split_mode(self) -> str:
        val = self.cbo_mode.get()
        if "逐位" in val:
            return "continuous"
        if "仅按空格" in val:
            return "separated"
        return "smart"

    def _on_trigger_config_changed(self):
        trigger = self.entry_trigger_word.get().strip()
        if not trigger:
            trigger = "qqq"
            self.entry_trigger_word.delete(0, tk.END)
            self.entry_trigger_word.insert(0, "qqq")

        self.config_data["trigger_word"] = trigger
        self.config_data["enable_trigger_word"] = bool(self.switch_trigger.get())
        self.config_data["enable_hotkey"] = bool(self.switch_hotkey.get())
        save_config(self.config_data)

        self.hotkey_mgr.reload_triggers()
        self._update_test_preview()

    def _on_config_param_changed(self):
        self.config_data["template"] = self.entry_template.get().strip()
        self.config_data["separator"] = self._get_current_separator()
        self.config_data["split_mode"] = self._get_current_split_mode()
        save_config(self.config_data)
        self._update_test_preview()

    def _update_test_preview(self):
        raw_text = self.entry_test.get().strip()
        cur_trigger = self.config_data.get("trigger_word", "qqq").lower()
        if raw_text.lower().endswith(cur_trigger):
            raw_text = raw_text[:-len(cur_trigger)].strip()

        template = self.entry_template.get().strip() or "本次作业的错题题号为：{nums}"
        separator = self._get_current_separator()
        split_mode = self._get_current_split_mode()

        numbers = parse_numbers(raw_text, split_mode)
        if numbers:
            result = format_output(numbers, template, separator)
            self.lbl_preview_result.configure(text=result, text_color=PALETTE["text_primary"])
        else:
            self.lbl_preview_result.configure(
                text="输入数字后在此查看转换结果",
                text_color=PALETTE["text_muted"],
            )

    def _copy_preview_result(self):
        content = self.lbl_preview_result.cget("text").strip()
        if content and content != "输入数字后在此查看转换结果":
            pyperclip.copy(content)
            messagebox.showinfo("已复制", "转换结果已复制到剪贴板")

    def _toggle_topmost(self):
        self.attributes("-topmost", bool(self.switch_topmost.get()))

    def _toggle_listener(self):
        if self.hotkey_mgr.is_running:
            self.hotkey_mgr.stop()
        else:
            self.hotkey_mgr.start()

    def _on_hotkey_status_changed(self, status_text: str, is_active: bool):
        def update():
            if is_active:
                self.lbl_status_dot.configure(text_color=PALETTE["positive"])
                self.lbl_status_text.configure(text=status_text, text_color=PALETTE["text_primary"])
                self.btn_toggle_listen.configure(text="暂停监听")
            else:
                self.lbl_status_dot.configure(text_color=PALETTE["negative"])
                self.lbl_status_text.configure(text=status_text, text_color=PALETTE["text_secondary"])
                self.btn_toggle_listen.configure(text="恢复监听")

        self.after(0, update)

    def _start_record_hotkey(self):
        if self.is_recording:
            return

        self.is_recording = True
        self.btn_record.configure(text="等待按键...", fg_color=PALETTE["warning"])
        self.lbl_hk_tip.configure(
            text="请按下组合键（如 Alt+Q 或 F8），按 Esc 取消",
            text_color=PALETTE["warning"],
        )

        def worker():
            try:
                recorded = keyboard.read_hotkey(suppress=False)
                self.after(0, lambda: self._on_hotkey_recorded(recorded))
            except Exception as e:
                self.after(0, lambda: self._on_record_failed(str(e)))

        self.recording_thread = threading.Thread(target=worker, daemon=True)
        self.recording_thread.start()

    def _on_hotkey_recorded(self, recorded_hotkey: str):
        self.is_recording = False
        self.btn_record.configure(text="录制按键", fg_color=PALETTE["accent"])

        if recorded_hotkey.lower() == "esc":
            self.lbl_hk_tip.configure(text="已取消录制，快捷键未改变", text_color=PALETTE["text_muted"])
            return

        new_hotkey = recorded_hotkey.strip().lower()
        self.entry_hotkey.delete(0, tk.END)
        self.entry_hotkey.insert(0, new_hotkey)
        self._apply_new_hotkey(new_hotkey)

    def _on_record_failed(self, err_msg: str):
        self.is_recording = False
        self.btn_record.configure(text="录制按键", fg_color=PALETTE["accent"])
        self.lbl_hk_tip.configure(text=f"录制按键失败：{err_msg}", text_color=PALETTE["negative"])

    def _save_manual_hotkey(self):
        raw_key = self.entry_hotkey.get().strip().lower()
        if not raw_key:
            messagebox.showwarning("提示", "快捷键不能为空")
            return
        self._apply_new_hotkey(raw_key)

    def _apply_new_hotkey(self, hotkey_str: str):
        success = self.hotkey_mgr.update_hotkey(hotkey_str)
        if success:
            self.config_data["hotkey"] = hotkey_str
            save_config(self.config_data)
            self.lbl_hk_tip.configure(
                text=f"快捷键已更新为 {hotkey_str}",
                text_color=PALETTE["positive"],
            )
        else:
            self.lbl_hk_tip.configure(
                text=f"快捷键 {hotkey_str} 注册失败",
                text_color=PALETTE["negative"],
            )

    def _on_close(self):
        try:
            self.hotkey_mgr.stop()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    try:
        app = ModernHotkeyApp()
        app.mainloop()
    except Exception as exc:
        _report_fatal_error(exc)

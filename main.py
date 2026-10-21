"""
main.py
错题题号快速转换助手 - 现代精美 GUI 界面（大字体舒适版）
采用 CustomTkinter 打造现代化 Fluent/macOS 质感桌面 UI：
- 放大字体层次，清晰醒目，阅读不费眼
- 支持浅色/深色主题自由切换
- 支持后缀触发词（如 135qqq）与全局快捷键（如 Alt+Q）
- 模块化卡片布局、圆角按键、平滑开关与实时测试预览
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk
import keyboard
import pyperclip

from core_engine import (
    DEFAULT_CONFIG,
    HotkeyManager,
    format_output,
    load_config,
    parse_numbers,
    save_config,
)

# 设置主题风格
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class ModernHotkeyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("错题输入快速转换助手")
        # 放大窗口尺寸以适配更大字体
        self.geometry("700x860")
        self.minsize(640, 780)

        # 加载配置
        self.config_data = load_config()

        # 录制状态标识
        self.is_recording = False
        self.recording_thread = None

        # ---------------- 字体设定（大号清晰版） ----------------
        self.font_title = ctk.CTkFont(family="Microsoft YaHei UI", size=20, weight="bold")
        self.font_subtitle = ctk.CTkFont(family="Microsoft YaHei UI", size=16, weight="bold")
        self.font_normal = ctk.CTkFont(family="Microsoft YaHei UI", size=14)
        self.font_bold = ctk.CTkFont(family="Microsoft YaHei UI", size=14, weight="bold")
        self.font_small = ctk.CTkFont(family="Microsoft YaHei UI", size=12)
        self.font_mono = ctk.CTkFont(family="Consolas", size=15, weight="bold")

        # 构建现代化 UI
        self._create_widgets()

        # 初始化后台监听管理器
        self.hotkey_mgr = HotkeyManager(
            config_getter=lambda: self.config_data,
            on_status_change=self._on_hotkey_status_changed,
        )

        # 启动热键与输入监听
        self.after(100, self.hotkey_mgr.start)

        # 关闭清理
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=16, pady=12)

        # 1. 顶部 Header 品牌与控制栏
        self._build_header(self.main_scroll)

        # 2. 状态胶囊栏
        self._build_status_pill(self.main_scroll)

        # 3. 核心触发方式卡片（后缀词 qqq 与快捷键）
        self._build_trigger_card(self.main_scroll)

        # 4. 文案模板与格式规则卡片
        self._build_template_card(self.main_scroll)

        # 5. 实时测试与预览卡片
        self._build_test_card(self.main_scroll)

        # 6. 底部工具栏与操作提示
        self._build_footer(self)

    # ---------------- 页面模块构建 ----------------

    def _build_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(4, 12))

        # 左侧标题与副标题
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="y")

        lbl_app_title = ctk.CTkLabel(
            title_box,
            text="✍️ 错题输入快速转换助手",
            font=self.font_title,
            text_color=("#1E293B", "#F8FAFC"),
        )
        lbl_app_title.pack(anchor="w")

        lbl_app_sub = ctk.CTkLabel(
            title_box,
            text="无需选中 · 连敲 qqq 自动展开 · 支持全局快捷键与多模板定制",
            font=self.font_small,
            text_color=("#64748B", "#94A3B8"),
        )
        lbl_app_sub.pack(anchor="w", pady=(2, 0))

        # 右侧主题切换
        self.theme_menu = ctk.CTkOptionMenu(
            header_frame,
            values=["浅色模式", "深色模式", "跟随系统"],
            width=110,
            height=32,
            font=self.font_normal,
            command=self._change_appearance_mode,
        )
        self.theme_menu.set("浅色模式")
        self.theme_menu.pack(side="right", padx=(8, 0))

    def _build_status_pill(self, parent):
        self.status_card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=("#F0FDF4", "#064E3B"),
            border_width=1,
            border_color=("#BBF7D0", "#059669"),
        )
        self.status_card.pack(fill="x", pady=(0, 14), ipady=6)

        self.lbl_status_dot = ctk.CTkLabel(
            self.status_card,
            text="●",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#16A34A", "#4ADE80"),
        )
        self.lbl_status_dot.pack(side="left", padx=(14, 4))

        self.lbl_status_text = ctk.CTkLabel(
            self.status_card,
            text="正在启动后台监听...",
            font=self.font_bold,
            text_color=("#166534", "#D1FAE5"),
        )
        self.lbl_status_text.pack(side="left", padx=4)

        self.btn_toggle_listen = ctk.CTkButton(
            self.status_card,
            text="暂停监听",
            width=96,
            height=32,
            corner_radius=8,
            font=self.font_normal,
            fg_color=("#DC2626", "#B91C1C"),
            hover_color=("#B91C1C", "#991B1B"),
            command=self._toggle_listener,
        )
        self.btn_toggle_listen.pack(side="right", padx=12)

    def _build_trigger_card(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=14, fg_color=("#FFFFFF", "#1E293B"))
        card.pack(fill="x", pady=(0, 14), padx=2, ipady=6)

        # 标题栏
        lbl_head = ctk.CTkLabel(card, text="⚡ 快捷触发方式设置", font=self.font_subtitle, text_color=("#1E293B", "#F8FAFC"))
        lbl_head.pack(anchor="w", padx=16, pady=(12, 8))

        # 方式 1：后缀触发词（如 qqq）
        box1 = ctk.CTkFrame(card, corner_radius=10, fg_color=("#F8FAFC", "#0F172A"), border_width=1, border_color=("#E2E8F0", "#334155"))
        box1.pack(fill="x", padx=14, pady=(4, 10), ipadx=8, ipady=10)

        row1 = ctk.CTkFrame(box1, fg_color="transparent")
        row1.pack(fill="x")

        self.switch_trigger = ctk.CTkSwitch(
            row1,
            text="启用后缀连续敲击展开（极速推荐）",
            font=self.font_bold,
            text_color=("#2563EB", "#60A5FA"),
            command=self._on_trigger_config_changed,
        )
        if self.config_data.get("enable_trigger_word", True):
            self.switch_trigger.select()
        else:
            self.switch_trigger.deselect()
        self.switch_trigger.pack(side="left", padx=4)

        row_input = ctk.CTkFrame(box1, fg_color="transparent")
        row_input.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(row_input, text="触发字符：", font=self.font_normal).pack(side="left", padx=(4, 2))
        self.entry_trigger_word = ctk.CTkEntry(
            row_input,
            width=90,
            height=36,
            font=self.font_mono,
            corner_radius=8,
            justify="center",
        )
        self.entry_trigger_word.insert(0, self.config_data.get("trigger_word", "qqq"))
        self.entry_trigger_word.pack(side="left", padx=4)
        self.entry_trigger_word.bind("<KeyRelease>", lambda e: self._on_trigger_config_changed())

        btn_save_trig = ctk.CTkButton(
            row_input,
            text="保存触发词",
            width=96,
            height=36,
            corner_radius=8,
            font=self.font_normal,
            command=self._on_trigger_config_changed,
        )
        btn_save_trig.pack(side="left", padx=6)

        keycap_badge = ctk.CTkLabel(
            row_input,
            text="示例：键入 [ 135 ] + [ qqq ]  ➔  自动展开",
            font=self.font_small,
            text_color=("#64748B", "#94A3B8"),
        )
        keycap_badge.pack(side="right", padx=6)

        # 方式 2：键盘快捷键
        box2 = ctk.CTkFrame(card, corner_radius=10, fg_color=("#F8FAFC", "#0F172A"), border_width=1, border_color=("#E2E8F0", "#334155"))
        box2.pack(fill="x", padx=14, pady=(4, 14), ipadx=8, ipady=10)

        row2 = ctk.CTkFrame(box2, fg_color="transparent")
        row2.pack(fill="x")

        self.switch_hotkey = ctk.CTkSwitch(
            row2,
            text="启用键盘全局快捷键",
            font=self.font_bold,
            command=self._on_trigger_config_changed,
        )
        if self.config_data.get("enable_hotkey", True):
            self.switch_hotkey.select()
        else:
            self.switch_hotkey.deselect()
        self.switch_hotkey.pack(side="left", padx=4)

        row_hk = ctk.CTkFrame(box2, fg_color="transparent")
        row_hk.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(row_hk, text="当前快捷键：", font=self.font_normal).pack(side="left", padx=(4, 2))
        self.entry_hotkey = ctk.CTkEntry(
            row_hk,
            width=130,
            height=36,
            font=self.font_mono,
            corner_radius=8,
            justify="center",
        )
        self.entry_hotkey.insert(0, self.config_data.get("hotkey", "alt+q").upper())
        self.entry_hotkey.pack(side="left", padx=4)

        self.btn_record = ctk.CTkButton(
            row_hk,
            text="🎙️ 录制新按键",
            width=100,
            height=36,
            corner_radius=8,
            font=self.font_normal,
            fg_color=("#3B82F6", "#2563EB"),
            command=self._start_record_hotkey,
        )
        self.btn_record.pack(side="left", padx=6)

        btn_apply_hk = ctk.CTkButton(
            row_hk,
            text="应用",
            width=66,
            height=36,
            corner_radius=8,
            font=self.font_normal,
            fg_color=("#64748B", "#475569"),
            command=self._save_manual_hotkey,
        )
        btn_apply_hk.pack(side="left", padx=2)

        self.lbl_hk_tip = ctk.CTkLabel(
            box2,
            text="打出数字后按此键自动就地替换（亦支持划选旧文本后按键替换）",
            font=self.font_small,
            text_color=("#64748B", "#94A3B8"),
        )
        self.lbl_hk_tip.pack(anchor="w", padx=4, pady=(8, 0))

    def _build_template_card(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=14, fg_color=("#FFFFFF", "#1E293B"))
        card.pack(fill="x", pady=(0, 14), padx=2, ipady=6)

        lbl_head = ctk.CTkLabel(card, text="📝 文案模板与格式规则", font=self.font_subtitle, text_color=("#1E293B", "#F8FAFC"))
        lbl_head.pack(anchor="w", padx=16, pady=(12, 8))

        # 预设模板选择栏
        row_preset = ctk.CTkFrame(card, fg_color="transparent")
        row_preset.pack(fill="x", padx=14, pady=(2, 8))

        ctk.CTkLabel(row_preset, text="快捷预设：", font=self.font_small, text_color=("#64748B", "#94A3B8")).pack(side="left", padx=(2, 6))

        presets = [
            ("题号模板", "本次作业的错题题号为：{nums}"),
            ("题数模板", "本次作业的错题数为：{nums}"),
            ("简洁订正", "错题订正：{nums}"),
        ]
        for name, tmpl in presets:
            btn = ctk.CTkButton(
                row_preset,
                text=name,
                width=86,
                height=30,
                corner_radius=6,
                font=self.font_normal,
                fg_color=("#F1F5F9", "#334155"),
                text_color=("#334155", "#F8FAFC"),
                hover_color=("#E2E8F0", "#475569"),
                command=lambda t=tmpl: self._apply_template_preset(t),
            )
            btn.pack(side="left", padx=4)

        # 模板输入框
        row_tmpl = ctk.CTkFrame(card, fg_color="transparent")
        row_tmpl.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(row_tmpl, text="文案模板：", font=self.font_normal).pack(side="left", padx=(2, 4))
        self.entry_template = ctk.CTkEntry(
            row_tmpl,
            height=38,
            corner_radius=8,
            font=self.font_normal,
        )
        self.entry_template.insert(0, self.config_data.get("template", "本次作业的错题题号为：{nums}"))
        self.entry_template.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.entry_template.bind("<KeyRelease>", lambda e: self._on_config_param_changed())

        lbl_placeholder_tip = ctk.CTkLabel(
            card,
            text="💡 提示：模板中的 {nums} 会被自动替换为生成的题号，支持随意编写你的个性评语",
            font=self.font_small,
            text_color=("#64748B", "#94A3B8"),
        )
        lbl_placeholder_tip.pack(anchor="w", padx=18, pady=(2, 8))

        # 分隔符与拆分模式
        row_options = ctk.CTkFrame(card, fg_color="transparent")
        row_options.pack(fill="x", padx=14, pady=(4, 12))

        ctk.CTkLabel(row_options, text="题号分隔符：", font=self.font_normal).pack(side="left", padx=(2, 4))
        self.cbo_sep = ctk.CTkOptionMenu(
            row_options,
            values=["，(中文逗号)", "、(顿号)", ", (英文逗号)", "  (空格)"],
            width=136,
            height=34,
            corner_radius=8,
            font=self.font_normal,
            command=lambda v: self._on_config_param_changed(),
        )
        sep_map_rev = {"，": "，(中文逗号)", "、": "、(顿号)", ", ": ", (英文逗号)", " ": "  (空格)"}
        cur_sep = self.config_data.get("separator", "，")
        self.cbo_sep.set(sep_map_rev.get(cur_sep, "，(中文逗号)"))
        self.cbo_sep.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row_options, text="数字拆分规则：", font=self.font_normal).pack(side="left", padx=(4, 4))
        self.cbo_mode = ctk.CTkOptionMenu(
            row_options,
            values=["智能识别 (按题号递增)", "连续数字逐位拆分", "仅按空格/符号分隔"],
            width=190,
            height=34,
            corner_radius=8,
            font=self.font_normal,
            command=lambda v: self._on_config_param_changed(),
        )
        mode_map_rev = {"smart": "智能识别 (按题号递增)", "continuous": "连续数字逐位拆分", "separated": "仅按空格/符号分隔"}
        cur_mode = self.config_data.get("split_mode", "smart")
        self.cbo_mode.set(mode_map_rev.get(cur_mode, "智能识别 (按题号递增)"))
        self.cbo_mode.pack(side="left")

    def _build_test_card(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=14, fg_color=("#FFFFFF", "#1E293B"))
        card.pack(fill="x", pady=(0, 14), padx=2, ipady=6)

        lbl_head = ctk.CTkLabel(card, text="🧪 实时测试与预览", font=self.font_subtitle, text_color=("#1E293B", "#F8FAFC"))
        lbl_head.pack(anchor="w", padx=16, pady=(12, 8))

        # 测试输入行
        row_input = ctk.CTkFrame(card, fg_color="transparent")
        row_input.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(row_input, text="输入测试：", font=self.font_normal).pack(side="left", padx=(2, 4))
        self.entry_test = ctk.CTkEntry(
            row_input,
            height=38,
            corner_radius=8,
            font=self.font_normal,
            placeholder_text="输入 135 或 135qqq 测试...",
        )
        self.entry_test.insert(0, "135qqq")
        self.entry_test.pack(side="left", fill="x", expand=True, padx=4)
        self.entry_test.bind("<KeyRelease>", lambda e: self._update_test_preview())

        btn_test_run = ctk.CTkButton(
            row_input,
            text="转换预览",
            width=88,
            height=38,
            corner_radius=8,
            font=self.font_normal,
            command=self._update_test_preview,
        )
        btn_test_run.pack(side="left", padx=(4, 0))

        # 预览卡片
        preview_box = ctk.CTkFrame(
            card,
            corner_radius=10,
            fg_color=("#F8FAFC", "#0F172A"),
            border_width=1,
            border_color=("#E2E8F0", "#334155"),
        )
        preview_box.pack(fill="x", padx=14, pady=(10, 12), ipady=8)

        row_prev_head = ctk.CTkFrame(preview_box, fg_color="transparent")
        row_prev_head.pack(fill="x", padx=12, pady=(4, 4))
        ctk.CTkLabel(row_prev_head, text="结果预览：", font=self.font_small, text_color=("#64748B", "#94A3B8")).pack(side="left")

        btn_copy = ctk.CTkButton(
            row_prev_head,
            text="📋 一键复制",
            width=86,
            height=28,
            corner_radius=6,
            font=self.font_normal,
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#1E293B", "#F8FAFC"),
            hover_color=("#CBD5E1", "#475569"),
            command=self._copy_preview_result,
        )
        btn_copy.pack(side="right")

        self.lbl_preview_result = ctk.CTkLabel(
            preview_box,
            text="",
            font=self.font_bold,
            text_color=("#0F172A", "#F1F5F9"),
            wraplength=580,
            justify="left",
        )
        self.lbl_preview_result.pack(anchor="w", padx=12, pady=(2, 6))

        # 初始预览
        self._update_test_preview()

    def _build_footer(self, parent):
        footer = ctk.CTkFrame(parent, height=48, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=18, pady=(4, 12))

        self.switch_topmost = ctk.CTkSwitch(
            footer,
            text="窗口置顶",
            font=self.font_normal,
            command=self._toggle_topmost,
        )
        self.switch_topmost.pack(side="left")

        lbl_guide = ctk.CTkLabel(
            footer,
            text="✨ 在任意软件中直接输入 135qqq，文字瞬间自动展开！",
            font=self.font_bold,
            text_color=("#2563EB", "#60A5FA"),
        )
        lbl_guide.pack(side="right")

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
        elif "英文逗号" in val:
            return ", "
        elif "空格" in val:
            return " "
        return "，"

    def _get_current_split_mode(self) -> str:
        val = self.cbo_mode.get()
        if "逐位" in val:
            return "continuous"
        elif "仅按空格" in val:
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
        else:
            result = "（等待输入数字... 例如输入 135 或 135qqq）"

        self.lbl_preview_result.configure(text=result)

    def _copy_preview_result(self):
        content = self.lbl_preview_result.cget("text").strip()
        if content and not content.startswith("（"):
            pyperclip.copy(content)
            messagebox.showinfo("已复制", "转换结果已复制到剪贴板！")

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
                self.lbl_status_dot.configure(text_color=("#16A34A", "#4ADE80"))
                self.lbl_status_text.configure(text=status_text, text_color=("#166534", "#D1FAE5"))
                self.status_card.configure(
                    fg_color=("#F0FDF4", "#064E3B"),
                    border_color=("#BBF7D0", "#059669"),
                )
                self.btn_toggle_listen.configure(
                    text="暂停监听",
                    fg_color=("#DC2626", "#B91C1C"),
                    hover_color=("#B91C1C", "#991B1B"),
                )
            else:
                self.lbl_status_dot.configure(text_color=("#DC2626", "#F87171"))
                self.lbl_status_text.configure(text=status_text, text_color=("#991B1B", "#FCA5A5"))
                self.status_card.configure(
                    fg_color=("#FEF2F2", "#450A0A"),
                    border_color=("#FECACA", "#991B1B"),
                )
                self.btn_toggle_listen.configure(
                    text="恢复监听",
                    fg_color=("#16A34A", "#15803D"),
                    hover_color=("#15803D", "#166534"),
                )

        self.after(0, update)

    def _start_record_hotkey(self):
        if self.is_recording:
            return

        self.is_recording = True
        self.btn_record.configure(text="⌛ 请按键...", fg_color=("#D97706", "#B45309"))
        self.lbl_hk_tip.configure(text="👉 正在监听键盘... 请直接按下你的快捷组合键（如 F8 或 Alt+Q，按 Esc 取消）", text_color=("#D97706", "#FBBF24"))

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
        self.btn_record.configure(text="🎙️ 录制新按键", fg_color=("#3B82F6", "#2563EB"))

        if recorded_hotkey.lower() == "esc":
            self.lbl_hk_tip.configure(text="已取消录制，快捷键未改变", text_color=("#64748B", "#94A3B8"))
            return

        new_hotkey = recorded_hotkey.strip().lower()
        self.entry_hotkey.delete(0, tk.END)
        self.entry_hotkey.insert(0, new_hotkey.upper())
        self._apply_new_hotkey(new_hotkey)

    def _on_record_failed(self, err_msg: str):
        self.is_recording = False
        self.btn_record.configure(text="🎙️ 录制新按键", fg_color=("#3B82F6", "#2563EB"))
        self.lbl_hk_tip.configure(text=f"录制按键失败: {err_msg}", text_color=("#DC2626", "#F87171"))

    def _save_manual_hotkey(self):
        raw_key = self.entry_hotkey.get().strip().lower()
        if not raw_key:
            messagebox.showwarning("提示", "快捷键不能为空！")
            return
        self._apply_new_hotkey(raw_key)

    def _apply_new_hotkey(self, hotkey_str: str):
        success = self.hotkey_mgr.update_hotkey(hotkey_str)
        if success:
            self.config_data["hotkey"] = hotkey_str
            save_config(self.config_data)
            self.lbl_hk_tip.configure(text=f"✅ 快捷键已更新为: {hotkey_str.upper()}", text_color=("#16A34A", "#4ADE80"))
        else:
            self.lbl_hk_tip.configure(text=f"❌ 快捷键 '{hotkey_str.upper()}' 注册失败", text_color=("#DC2626", "#F87171"))

    def _on_close(self):
        try:
            self.hotkey_mgr.stop()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = ModernHotkeyApp()
    app.mainloop()

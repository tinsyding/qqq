"""
core_engine.py
错题题号转换工具 - 核心逻辑模块
支持两种触发机制：
1. 触发词自动展开（如输入 135qqq，打完 3 个 q 瞬间自动擦除并展开）
2. 全局快捷键触发（如按 Alt+Q 或 F8，支持免选中自动退格与划选替换）
"""

import json
import os
import re
import sys
import threading
import time
from typing import Callable, List, Optional, Tuple

import keyboard
import mouse
import pyperclip

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "hotkey": "alt+q",
    "enable_hotkey": True,
    "trigger_word": "qqq",
    "enable_trigger_word": True,
    "template": "本次作业的错题题号为：{nums}",
    "separator": "，",
    "split_mode": "smart",  # "smart", "continuous", "separated"
    "no_selection_mode": True,  # 快捷键触发时是否免选中文本
}


def load_config() -> dict:
    """加载配置文件，若不存在则创建默认配置"""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> bool:
    """保存配置到本地 json 文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}", file=sys.stderr)
        return False


def smart_split_digits(digits: str) -> List[str]:
    """
    将纯数字串切分为严格递增的题号序列，题号数量尽可能多；
    数量相同时优先选择最大题号更小的切分方式。
    例如 "157111325" -> ['1', '5', '7', '11', '13', '25']，"135" -> ['1', '3', '5']。
    若不存在递增切分，则退化为逐位拆分。
    """
    n = len(digits)
    if n <= 1:
        return list(digits)

    memo = {}

    def solve(pos: int, prev: int):
        if pos == n:
            return ()
        key = (pos, prev)
        if key in memo:
            return memo[key]

        best = None
        for end in range(pos + 1, n + 1):
            token = digits[pos:end]
            if len(token) > 1 and token[0] == "0":
                continue
            value = int(token)
            if value <= prev:
                continue
            rest = solve(end, value)
            if rest is None:
                continue
            candidate = (token,) + rest
            if (
                best is None
                or len(candidate) > len(best)
                or (len(candidate) == len(best) and int(candidate[-1]) < int(best[-1]))
            ):
                best = candidate

        memo[key] = best
        return best

    result = solve(0, -1)
    return list(result) if result is not None else list(digits)


def parse_numbers(raw_text: str, mode: str = "smart") -> List[str]:
    """
    智能解析输入的数字串：
    - smart: 若含有空格/逗号/分号/换行等分隔符，按整体提取数字（如 "1 3 12" -> ['1', '3', '12']）；
             若纯连续无分隔符（如 "135"），按题号递增规律智能切分
             （"135" -> ['1', '3', '5']，"157111325" -> ['1', '5', '7', '11', '13', '25']）。
    - continuous: 强制逐位拆分每一个数字字符。
    - separated: 仅提取由分隔符隔开的连续数字串。
    """
    text = raw_text.strip()
    if not text:
        return []

    if mode == "continuous":
        return re.findall(r"\d", text)

    if mode == "separated":
        return re.findall(r"\d+", text)

    # 默认 smart 智能模式
    has_explicit_separator = bool(re.search(r"[\s,，、;；\|/]", text))

    if has_explicit_separator:
        nums = re.findall(r"\d+", text)
    else:
        if len(text) > 1 and text.isdigit():
            nums = smart_split_digits(text)
        else:
            nums = re.findall(r"\d+", text)

    return nums


def format_output(numbers: List[str], template: str = "本次作业的错题题号为：{nums}", separator: str = "，") -> str:
    """根据提取的数字列表、分隔符和模板拼接最终文案"""
    nums_str = separator.join(numbers)
    if "{nums}" in template:
        return template.replace("{nums}", nums_str)
    return f"{template}{nums_str}"


class KeyBuffer:
    """
    实时记录最近键入的字符：
    1. 监听触发词（如 qqq）即时触发展开
    2. 支持快捷键免选中文本自动退格替换
    """

    def __init__(self, on_trigger_match: Optional[Callable[[str, int], None]] = None, timeout: float = 12.0):
        self.buffer: List[Tuple[str, float]] = []  # [(char, timestamp)]
        self.timeout = timeout
        self.on_trigger_match = on_trigger_match
        self.lock = threading.Lock()
        self.is_replacing = False  # 防止自动退格/粘贴时的按键干扰

    def on_key_event(self, event, config: dict):
        if event.event_type != "down" or self.is_replacing:
            return

        # 忽略组合功能键
        try:
            if keyboard.is_pressed("ctrl") or keyboard.is_pressed("alt") or keyboard.is_pressed("windows"):
                return
        except Exception:
            pass

        name = event.name
        now = time.time()

        with self.lock:
            self._prune_expired(now)

            if name == "backspace":
                if self.buffer:
                    self.buffer.pop()
                return
            elif name in ("enter", "tab", "esc", "left", "right", "up", "down", "home", "end", "page up", "page down"):
                self.buffer.clear()
                return
            elif name == "space":
                self.buffer.append((" ", now))
                if len(self.buffer) > 40:
                    self.buffer.pop(0)
            elif name and len(name) == 1:
                self.buffer.append((name, now))
                if len(self.buffer) > 40:
                    self.buffer.pop(0)
            else:
                return

            # ---------------- 触发词检测 (例如 qqq) ----------------
            if config.get("enable_trigger_word", True):
                trigger = config.get("trigger_word", "qqq").strip()
                if trigger:
                    match_result = self._check_trigger_match(trigger)
                    if match_result and self.on_trigger_match:
                        num_str, erase_count = match_result
                        self.buffer.clear()
                        # 启动线程执行替换，避免阻塞键盘底层钩子
                        threading.Thread(
                            target=self.on_trigger_match,
                            args=(num_str, erase_count),
                            daemon=True,
                        ).start()

    def on_mouse_click(self, event=None):
        if not self.is_replacing:
            with self.lock:
                self.buffer.clear()

    def _prune_expired(self, now: float):
        self.buffer = [item for item in self.buffer if now - item[1] <= self.timeout]

    def _check_trigger_match(self, trigger: str) -> Optional[Tuple[str, int]]:
        """
        检查当前缓冲区是否以触发词结尾（不区分大小写），且前面是数字串。
        返回 (数字文本, 需要回退删除的总字符数)。
        例如刚敲了 '135qqq' -> 返回 ('135', 6)
             刚敲了 '1 3 12qqq' -> 返回 ('1 3 12', 9)
        """
        if not self.buffer:
            return None

        text = "".join(char for char, _ in self.buffer)
        trigger_lower = trigger.lower()

        if not text.lower().endswith(trigger_lower):
            return None

        # 剥离触发词部分
        prefix = text[:-len(trigger)]
        # 查找前缀末尾的连续数字与可能存在的分隔符
        match = re.search(r"(\d[\d\s,，、;；]*)$", prefix)
        if not match:
            return None

        num_str = match.group(1)
        if not any(c.isdigit() for c in num_str):
            return None

        total_erase_count = len(num_str) + len(trigger)
        return (num_str, total_erase_count)

    def get_trailing_numbers(self) -> Optional[Tuple[str, int]]:
        """用于快捷键触发时获取末尾刚刚敲入的数字部分及字符个数"""
        now = time.time()
        with self.lock:
            self._prune_expired(now)
            if not self.buffer:
                return None

            text = "".join(char for char, _ in self.buffer)
            match = re.search(r"(\d[\d\s,，、;；]*)$", text)
            if match:
                matched_str = match.group(1)
                if any(c.isdigit() for c in matched_str):
                    return (matched_str, len(matched_str))
            return None

    def clear(self):
        with self.lock:
            self.buffer.clear()


class HotkeyManager:
    """全局热键、后缀触发词与替换逻辑管理器"""

    def __init__(self, config_getter: Callable[[], dict], on_status_change: Optional[Callable[[str, bool], None]] = None):
        self.config_getter = config_getter
        self.on_status_change = on_status_change
        self.current_hotkey: Optional[str] = None
        self.is_running: bool = False
        self._lock = threading.Lock()

        # 按键历史缓冲区（挂载触发词匹配回调）
        self.key_buffer = KeyBuffer(on_trigger_match=self._on_trigger_word_matched)
        self._key_hook = None
        self._mouse_hook = None

    def start(self) -> bool:
        """启动监听"""
        with self._lock:
            config = self.config_getter()
            try:
                # 挂载键盘钩子
                if not self._key_hook:
                    self._key_hook = keyboard.hook(lambda e: self.key_buffer.on_key_event(e, self.config_getter()))
                if not self._mouse_hook:
                    try:
                        self._mouse_hook = mouse.on_click(self.key_buffer.on_mouse_click)
                    except Exception:
                        pass

                # 绑定快捷键（如果开启）
                self._bind_hotkey(config)
                self.is_running = True
                self._notify_status()
                return True
            except Exception as e:
                self.is_running = False
                if self.on_status_change:
                    self.on_status_change(f"启动失败: {e}", False)
                return False

    def _bind_hotkey(self, config: dict):
        """绑定快捷键"""
        if self.current_hotkey:
            try:
                keyboard.remove_hotkey(self.current_hotkey)
            except Exception:
                pass
            self.current_hotkey = None

        if config.get("enable_hotkey", True):
            hotkey = config.get("hotkey", "alt+q").strip().lower()
            if hotkey:
                keyboard.add_hotkey(hotkey, self._on_hotkey_triggered, suppress=False)
                self.current_hotkey = hotkey

    def _notify_status(self):
        config = self.config_getter()
        parts = []
        if config.get("enable_trigger_word", True) and config.get("trigger_word"):
            parts.append(f"后缀输入【{config.get('trigger_word')}】触发")
        if config.get("enable_hotkey", True) and self.current_hotkey:
            parts.append(f"快捷键【{self.current_hotkey.upper()}】")

        desc = " & ".join(parts) if parts else "未启用任何触发方式"
        if self.on_status_change:
            self.on_status_change(f"监听中 ({desc})", True)

    def stop(self):
        """停止热键监听"""
        with self._lock:
            if self.current_hotkey:
                try:
                    keyboard.remove_hotkey(self.current_hotkey)
                except Exception:
                    pass
                self.current_hotkey = None

            if self._key_hook:
                try:
                    keyboard.unhook(self._key_hook)
                except Exception:
                    pass
                self._key_hook = None

            if self._mouse_hook:
                try:
                    mouse.unhook(self._mouse_hook)
                except Exception:
                    pass
                self._mouse_hook = None

            self.key_buffer.clear()
            self.is_running = False
            if self.on_status_change:
                self.on_status_change("已暂停监听", False)

    def reload_triggers(self):
        """配置更新后重新载入热键和触发设置"""
        with self._lock:
            config = self.config_getter()
            self._bind_hotkey(config)
            if self.is_running:
                self._notify_status()

    def update_hotkey(self, new_hotkey: str) -> bool:
        """更新热键设置并重新绑定"""
        new_hotkey = new_hotkey.strip().lower()
        with self._lock:
            try:
                if self.current_hotkey:
                    try:
                        keyboard.remove_hotkey(self.current_hotkey)
                    except Exception:
                        pass
                    self.current_hotkey = None

                if new_hotkey:
                    keyboard.add_hotkey(new_hotkey, self._on_hotkey_triggered, suppress=False)
                    self.current_hotkey = new_hotkey

                self._notify_status()
                return True
            except Exception as e:
                if self.on_status_change:
                    self.on_status_change(f"热键 '{new_hotkey}' 无效: {e}", False)
                return False

    # ---------------- 触发事件处理 ----------------

    def _on_trigger_word_matched(self, num_str: str, erase_count: int):
        """当用户在输入框中连续敲出触发词（如 135qqq）时执行自动替换"""
        config = self.config_getter()
        template = config.get("template", "本次作业的错题题号为：{nums}")
        separator = config.get("separator", "，")
        split_mode = config.get("split_mode", "smart")

        try:
            self.key_buffer.is_replacing = True
            # 等待最后一个按键在目标程序上渲染完毕
            time.sleep(0.04)

            numbers = parse_numbers(num_str, split_mode)
            if not numbers:
                return

            # 连续退格擦除刚刚键入的内容（包括数字和触发词 qqq）
            for _ in range(erase_count):
                keyboard.send("backspace")
                time.sleep(0.004)

            time.sleep(0.02)
            transformed_text = format_output(numbers, template, separator)
            pyperclip.copy(transformed_text)
            time.sleep(0.03)
            keyboard.send("ctrl+v")

        except Exception as e:
            print(f"触发词替换出错: {e}", file=sys.stderr)
        finally:
            self.key_buffer.is_replacing = False

    def _on_hotkey_triggered(self):
        """热键触发时在单独线程中执行转换"""
        threading.Thread(target=self._execute_hotkey_replacement, daemon=True).start()

    def _execute_hotkey_replacement(self):
        """快捷键触发替换逻辑"""
        config = self.config_getter()
        template = config.get("template", "本次作业的错题题号为：{nums}")
        separator = config.get("separator", "，")
        split_mode = config.get("split_mode", "smart")
        no_selection_mode = config.get("no_selection_mode", True)

        try:
            self.key_buffer.is_replacing = True
            time.sleep(0.06)

            # 1. 免选中模式：从缓冲区获取末尾刚键入的数字
            if no_selection_mode:
                trailing_info = self.key_buffer.get_trailing_numbers()
                if trailing_info:
                    matched_str, char_count = trailing_info
                    numbers = parse_numbers(matched_str, split_mode)
                    if numbers:
                        self.key_buffer.clear()
                        for _ in range(char_count):
                            keyboard.send("backspace")
                            time.sleep(0.004)

                        time.sleep(0.02)
                        transformed_text = format_output(numbers, template, separator)
                        pyperclip.copy(transformed_text)
                        time.sleep(0.03)
                        keyboard.send("ctrl+v")
                        return

            # 2. 选区模式：复制选中的文本并替换
            try:
                original_clipboard = pyperclip.paste()
            except Exception:
                original_clipboard = ""

            pyperclip.copy("")
            keyboard.send("ctrl+c")

            copied_text = ""
            start_time = time.time()
            while time.time() - start_time < 0.25:
                try:
                    copied_text = pyperclip.paste()
                    if copied_text:
                        break
                except Exception:
                    pass
                time.sleep(0.02)

            if copied_text and copied_text.strip():
                numbers = parse_numbers(copied_text, split_mode)
                if numbers:
                    transformed_text = format_output(numbers, template, separator)
                    pyperclip.copy(transformed_text)
                    time.sleep(0.03)
                    keyboard.send("ctrl+v")
                    self.key_buffer.clear()
                    return

            if original_clipboard:
                pyperclip.copy(original_clipboard)

        except Exception as e:
            print(f"快捷键替换出错: {e}", file=sys.stderr)
        finally:
            self.key_buffer.is_replacing = False

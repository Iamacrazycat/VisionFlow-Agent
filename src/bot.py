"""
AutoRocoBot — 精简编排器。

只负责组装组件（EventBus、State、Detector、Strategy）和运行主循环。
所有业务逻辑已拆分到 detector.py、strategies/、state.py、events.py 中。
"""
import time
import logging

from config import CONFIG
from src.state import BotState
from src.events import EventBus
from src.detector import BattleDetector
from src.strategies import create_strategy
from src.utils import log_audit, normalize_poll_interval
from src.vision import load_templates, preprocess
from src.window import find_window_by_keyword, get_client_rect_on_screen, capture_window_bgr
from src.stats import get_daily_battle_count

try:
    import win32gui
except ImportError:
    win32gui = None


class AutoRocoBot:
    """ 机器人编排器：负责组装组件并运行主循环流程 """

    def __init__(self) -> None:
        """ 初始化机器人，加载模板并配置检测逻辑 """

        self.state = BotState()
        self.event_bus = EventBus()
        self.templates = load_templates()
        self.interval = normalize_poll_interval(CONFIG.poll_interval_sec)

        self.detector = BattleDetector(self.event_bus, self.state, self.templates)
        self.strategy = None  # 由 prompt_mode() 设置

    def prompt_mode(self) -> None:
        """ 用户交互界面：选择运行模式并初始化对应策略 """
        logging.info("Starting detector.")
        logging.info("This script is for authorized testing only.")

        print("\n请选择运行模式:")
        print("1: 聚能模式 (自动键入 X)")
        print("2: 逃跑模式 (自动键入 ESC 并点击确认)")
        print("3: 智能挂机模式 (基于 HP 血条颜色自动判断：粉色聚能，绿色逃跑)")
        print("4: 仅统计模式 (只记录次数，不执行任何动作)")
        print("有问题或新功能建议请提 issue。如果这个项目对你有帮助，欢迎点个 Star 支持一下。")
        print("\n[提示] 脚本支持自适应分辨率，推荐使用 2K（2560x1600 或 2560x1440）以获得更高识别精度。")
        print("[提示] 逃跑模式使用物理点击，请确保'是'按钮露出且不被其他窗口遮挡。")
        
        daily_count = get_daily_battle_count()
        print(f"\n[统计] 今天已经进行了 {daily_count} 次有效战斗。")

        choice = input("请输入选项 (1, 2, 3 或 4): ").strip()
        if choice == "2":
            self.state.selected_mode = "escape"
        elif choice == "3":
            self.state.selected_mode = "smart"
        elif choice == "4":
            self.state.selected_mode = "stat"
        else:
            self.state.selected_mode = "battle"

        mode_display = {
            "battle": "聚能模式",
            "escape": "逃跑模式",
            "smart": "智能挂机模式",
            "stat": "仅统计模式",
        }[self.state.selected_mode]
        logging.info("已选择模式: %s", mode_display)

        log_audit(
            "MODE_SELECTED",
            mode=self.state.selected_mode,
            match_threshold=CONFIG.match_threshold,
            trigger_cooldown_sec=CONFIG.trigger_cooldown_sec,
            escape_click_method=CONFIG.escape_click_method,
        )

        # 创建策略并注册到事件总线
        self.strategy = create_strategy(
            self.state.selected_mode, self.event_bus, self.state, self.templates
        )

    def run(self) -> None:
        """ 主循环：执行 截图 -> 检测 -> 分发 -> 策略执行 流程 """
        while True:
            hwnd = find_window_by_keyword(CONFIG.window_title_keyword)
            if hwnd is None:
                logging.warning("Game window not found: %s", CONFIG.window_title_keyword)
                time.sleep(self.interval)
                continue

            left, top, width, height = get_client_rect_on_screen(hwnd)
            if width <= 0 or height <= 0:
                logging.warning("Invalid window size: %sx%s", width, height)
                time.sleep(self.interval)
                continue

            full_window_bgr = capture_window_bgr(hwnd)
            cap_h, cap_w = full_window_bgr.shape[:2]

            # 全图处理
            frame_processed = preprocess(full_window_bgr)

            # 交给检测器——内部会自动通过 EventBus 触发 Strategy
            self.detector.process_frame(
                frame_processed,
                hwnd=hwnd,
                full_frame=full_window_bgr,
                width=cap_w,
                height=cap_h,
            )

            time.sleep(self.interval)

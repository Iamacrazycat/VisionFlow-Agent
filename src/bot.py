import time
import logging

from config import CONFIG
from src.state import BotState
from src.events import EventBus
from src.detector import VisionOrchestratorDetector
from src.strategies import create_strategy
from src.utils import log_audit, normalize_poll_interval
from src.vision import load_templates, preprocess
from src.window import find_window_by_keyword, get_client_rect_on_screen, capture_window_bgr
from src.stats import get_daily_battle_count

class AutoRocoBot:
    """ 机器人编排器：负责组装组件并运行主循环流程 """

    def __init__(self) -> None:
        """ 初始化机器人，加载模板并配置检测逻辑 """

        self.state = BotState()
        self.event_bus = EventBus()
        self.templates = load_templates()

        self.detector = VisionOrchestratorDetector(self.event_bus, self.state, self.templates)
        self.strategy = None

    def set_mode(self, mode: str) -> None:
        """ 动态设置运行模式并初始化对应策略 """
        self.state.selected_mode = mode
        
        # 创建新策略并注册
        self.strategy = create_strategy(
            mode, self.event_bus, self.state, self.templates
        )
        
        log_audit(
            "MODE_CHANGED",
            mode=mode,
            match_threshold=CONFIG.match_threshold,
        )

    def step(self) -> None:
        """ 执行一帧的检测和处理流程 (非阻塞) """
        # 再次检查运行状态，防止在 timer 间隔内被关闭
        if not CONFIG.is_running:
            return

        hwnd = find_window_by_keyword(CONFIG.window_title_keyword)
        if hwnd is None:
            # 没找到窗口时只记录一次日志，避免刷屏
            logging.warning("Game window not found: %s", CONFIG.window_title_keyword)
            return

        left, top, width, height = get_client_rect_on_screen(hwnd)
        if width <= 0 or height <= 0:
            logging.warning("Invalid window size: %sx%s", width, height)
            return

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

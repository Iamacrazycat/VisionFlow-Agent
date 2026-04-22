"""
逃跑模式策略。

检测到战斗后按 ESC 键逃跑，并自动查找"是"确认按钮点击。
"""
import time
import logging

from config import CONFIG
from src.events import BattleDetectedEvent
from src.state import BotState
from src.strategies.base import ActionStrategy
from src.input import press_once, click_at
from src.vision import Template, best_yes_score_and_loc, map_to_window
from src.window import capture_window_bgr
from src.utils import log_audit
from typing import List


class EscapeStrategy(ActionStrategy):
    """ 逃跑策略：进入战斗后自动执行 按ESC -> 找确认按钮 -> 点击 的逃跑流程 """

    def __init__(self, state: BotState, templates: List[Template]) -> None:
        """ 初始化逃跑策略，加载识别所需的模板 """

        self.state = state
        self.templates = templates

    def on_battle_detected(self, event: BattleDetectedEvent) -> None:
        """ 战斗检测回调：触发逃跑动作逻辑 """

        if not self.state.can_trigger(CONFIG.trigger_cooldown_sec):
            return

        self._execute_escape(event)

    def _execute_escape(self, event: BattleDetectedEvent) -> None:
        """ 私有方法：执行具体的按键模拟和按钮匹配逻辑 """

        hwnd = event.hwnd
        width = event.width
        height = event.height

        # 按下 ESC 键
        press_once(hwnd, "esc")
        logging.info("Triggered Escape")
        log_audit(
            "TRIGGER_ESCAPE_KEY",
            mode=self.state.selected_mode,
            decided_action="escape",
            key="esc",
            hwnd=hwnd,
            score=round(event.score, 4),
            template=event.template_name,
            cooldown_sec=CONFIG.trigger_cooldown_sec,
        )

        # 查找并点击确认按钮
        button_clicked = False
        yes_threshold = CONFIG.match_threshold * CONFIG.escape_yes_threshold_ratio

        for i in range(CONFIG.escape_max_attempts):
            time.sleep(CONFIG.escape_retry_delay_sec)
            full_shot = capture_window_bgr(hwnd)
            score, loc = best_yes_score_and_loc(full_shot, self.templates)

            if score >= yes_threshold:
                # 使用统一转换工具处理坐标映射
                click_x, click_y = map_to_window(loc, full_shot.shape[:2], (height, width))
                
                if click_at(hwnd, click_x, click_y):
                    button_clicked = True
                    log_audit(
                        "ESCAPE_YES_CLICK_SUCCESS",
                        mode=self.state.selected_mode,
                        hwnd=hwnd,
                        score=round(event.score, 4),
                        template=event.template_name,
                        yes_score=round(score, 4),
                        threshold=round(yes_threshold, 4),
                        click_x=click_x,
                        click_y=click_y,
                        click_method="physical",
                        attempt=i + 1,
                    )
                    break

        if not button_clicked:
            logging.warning("Could not find confirmation button '%s' after ESC", CONFIG.yes_template_name)
            log_audit(
                "ESCAPE_YES_CLICK_FAILED",
                mode=self.state.selected_mode,
                hwnd=hwnd,
                score=round(event.score, 4),
                template=event.template_name,
                threshold=round(yes_threshold, 4),
                click_method="physical",
            )

        # 逃跑有额外冷却
        self.state.mark_triggered(extra_cooldown=CONFIG.escape_extra_cooldown_sec)
        # 按照需求，“执行后回归空状态”
        self.state.reset_to_none()

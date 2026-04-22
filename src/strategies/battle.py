"""
聚能模式策略。

检测到战斗后自动按下 X 键进行聚能。
"""
import logging

from config import CONFIG
from src.events import BattleDetectedEvent
from src.state import BotState
from src.strategies.base import ActionStrategy
from src.input import press_once
from src.stats import increment_daily_battle
from src.utils import log_audit


class BattleStrategy(ActionStrategy):
    """ 聚能策略：进入战斗后循环键入指定动作键 (X) """

    def __init__(self, state: BotState) -> None:
        """ 初始化战斗策略，绑定全局状态 """

        self.state = state

    def on_battle_detected(self, event: BattleDetectedEvent) -> None:
        """ 战斗检测回调：依据状态机执行按键逻辑 """
        from src.state import RobotState

        if not self.state.can_trigger(CONFIG.trigger_cooldown_sec):
            return

        # 统计逻辑：只有状态从非战斗切换过来时才增加计数
        if self.state.last_non_none_state == RobotState.NON_BATTLE:
             new_count = increment_daily_battle()
             logging.info("=== 确认进入新战斗！今日累计战斗次数: %d ===", new_count)

        # 执行按键
        press_once(event.hwnd, CONFIG.press_key)
        logging.info("Triggered key: %s (State: %s)", CONFIG.press_key, self.state.current_state.name)

        log_audit(
            "TRIGGER_BATTLE_KEY",
            mode=self.state.selected_mode,
            decided_action="battle",
            key=CONFIG.press_key,
            hwnd=event.hwnd,
            score=round(event.score, 4),
            template=event.template_name,
            cooldown_sec=CONFIG.trigger_cooldown_sec,
        )

        self.state.mark_triggered()
        # 按照需求，“执行后回归空状态”，以便下一帧重新通过状态机判定逻辑
        self.state.reset_to_none()

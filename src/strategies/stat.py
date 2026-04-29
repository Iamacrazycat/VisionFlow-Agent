"""
仅统计模式策略。

只记录有效战斗次数，不执行任何按键或点击动作。
"""
import logging

from config import CONFIG
from src.events import LifecycleTriggerEvent
from src.state import BotState
from src.strategies.base import ActionStrategy
from src.stats import increment_daily_battle
from src.utils import log_audit


class StatStrategy(ActionStrategy):
    """ 统计策略：仅观察并记录战斗计数，不执行任何攻击或逃跑操作 """

    def __init__(self, state: BotState) -> None:
        """ 初始化统计策略 """
        self.state = state

    def on_battle_detected(self, event: LifecycleTriggerEvent) -> None:
        """ 战斗检测回调：仅执行统计和日志记录 """
        from src.state import AgentState

        if not self.state.can_trigger(CONFIG.trigger_cooldown_sec):
            return

        # 统计逻辑：只有状态从非战斗切换过来时才增加计数
        if self.state.last_non_none_state == AgentState.IDLE:
             new_count = increment_daily_battle()
             logging.info("=== [仅统计] 触发新生命周期！今日累计有效调度次数: %d ===", new_count)

             log_audit(
                 "STAT_BATTLE_DETECTED",
                 mode=self.state.selected_mode,
                 hwnd=event.hwnd,
                 score=round(event.score, 4),
                 template=event.template_name,
                 total_count=new_count
             )

        # 虽然不做动作，但由于检测主循环依然在运行，我们需要通过标记 triggered 和 reset
        # 来维持状态机的步调一致，防止在同一帧中重复触发计数逻辑。
        self.state.mark_triggered()
        self.state.reset_to_none()

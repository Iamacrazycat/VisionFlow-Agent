"""
智能挂机模式策略。

根据 HP 血条颜色自动判断：
- 粉色 (#ff3fa1) → 有效战斗（委托 BattleStrategy）
- 绿色 (#73c615) → 意外遭遇（委托 EscapeStrategy）

仅在每场新战斗的首帧进行颜色检测，后续帧复用缓存的决策。
"""
import logging

from config import CONFIG
from src.events import LifecycleTriggerEvent
from src.state import BotState
from src.strategies.base import ActionStrategy
from src.strategies.battle import BattleStrategy
from src.strategies.escape import EscapeStrategy
from src.vision import Template, detect_hp_bar_color
from src.utils import log_audit
from typing import List


class SmartStrategy(ActionStrategy):
    """ 智能策略：根据 HP 血条颜色自动决策 (粉色聚能 / 绿色逃跑) """

    def __init__(self, state: BotState, templates: List[Template]) -> None:
        """ 初始化智能策略并组装内部的战斗/逃跑子策略 """
        self.state = state
        self.templates = templates
        self._battle = BattleStrategy(state)
        self._escape = EscapeStrategy(state, templates)

    def on_battle_detected(self, event: LifecycleTriggerEvent) -> None:
        """ 战斗检测回调：依据状态机当前状态分发任务 """
        from src.state import AgentState

        if not self.state.can_trigger(CONFIG.trigger_cooldown_sec):
            return

        state = self.state.current_state

        if state == AgentState.LIFECYCLE_A:
            self._battle.on_battle_detected(event)
        elif state == AgentState.LIFECYCLE_B:
            self._escape.on_battle_detected(event)
        else:
            # 状态不明确或处于 NONE/OTHER，不执行任何动作
            logging.debug("Smart Mode: State is %s, idling...", state.name)

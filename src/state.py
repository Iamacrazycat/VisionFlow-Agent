from enum import Enum
import time
import logging


class AgentState(Enum):
    """ 机器人运行状态枚举 """
    NONE = "none"               # 未知/过渡态
    IDLE = "idle"   # 非战斗（世界地图）
    LIFECYCLE_A = "charge"    # 蓄能战斗
    LIFECYCLE_B = "escape"    # 逃跑战斗
    OTHER = "other"             # 其他界面


class BotState:
    """ 全局状态存储类 (Store)：维护机器人显式状态机 """

    def __init__(self) -> None:
        """ 初始化所有运行时状态变量 """
        self.current_state: AgentState = AgentState.NONE
        self.last_non_none_state: AgentState = AgentState.NONE

        # ── 动作状态 ──
        self.last_trigger_time: float = 0.0

        # ── 统计与模式 ──
        self.selected_mode: str = "battle"

    def set_state(self, new_state: AgentState) -> None:
        """ 更新当前状态并维护历史记录 """
        if new_state == self.current_state:
            return

        if self.current_state != AgentState.NONE:
            self.last_non_none_state = self.current_state

        logging.info("State Transition: %s -> %s", self.current_state.name, new_state.name)
        self.current_state = new_state

    # ── 动作冷却 ──

    def can_trigger(self, cooldown: float) -> bool:
        """ 判断当前是否已过冷却期 """
        return (time.time() - self.last_trigger_time) >= cooldown

    def mark_triggered(self, extra_cooldown: float = 0.0) -> None:
        """ 标记动作已执行，重置冷却（可叠加额外冷却时间） """
        self.last_trigger_time = time.time() + extra_cooldown

    def reset_to_none(self) -> None:
        """ 强制重置到 NONE 状态（通常在动作执行完成后） """
        self.set_state(AgentState.NONE)

    def __repr__(self) -> str:
        return (
            f"BotState(mode={self.selected_mode}, state={self.current_state.name}, "
            f"last_valid={self.last_non_none_state.name})"
        )

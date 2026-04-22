"""
战斗检测器。

只负责分析帧画面、维护检测状态、在状态变化时发布事件。
不包含任何动作/执行逻辑。
"""
import logging
import numpy as np

from config import CONFIG
from src.events import EventBus, BattleDetectedEvent, BattleEndedEvent
from src.state import BotState
from src.vision import Template
from typing import List


class BattleDetector:
    """ 战斗检测器：分析帧画面、维护检测状态并在状态变化时发布事件 """

    def __init__(
        self,
        event_bus: EventBus,
        state: BotState,
        templates: List[Template],
    ) -> None:
        """ 初始化检测器，绑定事件总线、状态源和识别模板 """

        self.event_bus = event_bus
        self.state = state
        self.templates = templates

    def process_frame(
        self,
        frame_processed: np.ndarray,
        *,
        hwnd: int,
        full_frame: np.ndarray,
        width: int,
        height: int,
    ) -> None:
        """ 核心检测逻辑：星号 (非战斗) -> 背包 (战斗判定) -> HP (动作判定) """
        from src.vision import detect_state_icon, detect_hp_bar_color
        from src.state import RobotState
        from src.utils import save_debug_image
        import time

        # 1. 优先判定是否处于“非战斗状态” (左上角 ROI)
        star_score, star_loc, star_size = detect_state_icon(full_frame, self.templates, "bluestar.png", (0, 0.3, 0, 0.3))
        
        # 调试保存
        if star_score >= CONFIG.debug_save_threshold:
            save_debug_image(full_frame, "star_check", star_score, star_loc, star_size)

        if star_score >= CONFIG.match_threshold:
            if self.state.current_state != RobotState.NON_BATTLE:
                self.state.set_state(RobotState.NON_BATTLE)
            return

        # 2. 判定是否处于“战斗界面” (右下角 ROI，使用 exchange.png 包裹)
        ex_score, ex_loc, ex_size = detect_state_icon(full_frame, self.templates, "exchange.png", (0.5, 1.0, 0.5, 1.0))
        
        # 调试保存
        if ex_score >= CONFIG.debug_save_threshold:
            save_debug_image(full_frame, "exchange_check", ex_score, ex_loc, ex_size)

        # 3. 只有在确定是战斗界面时，才去分析 HP 血条
        in_battle_ui = ex_score >= CONFIG.match_threshold
        
        hp_sift_score = 0.0
        hp_bgr = None
        dist_v, dist_e = 0.0, 0.0
        decided_action = None

        if in_battle_ui:
            # 无论是否已有状态，每一帧都重新尝试获取血条信息用于日志记录
            decided_action, hp_bgr, dist_v, dist_e = detect_hp_bar_color(
                full_frame, self.templates,
                valid_targets=CONFIG.hp_charge_targets,
                escape_bgr=CONFIG.hp_escape_bgr,
                tolerance=CONFIG.hp_color_tolerance
            )
            
            if hp_bgr is not None:
                hp_sift_score = 1.0 

        # 增强版日志：包含 BGR 和 距离信息
        bgr_str = f"BGR={hp_bgr}" if hp_bgr else "BGR=N/A"
        dist_str = f"Dist: V={dist_v:.1f} E={dist_e:.1f}" if hp_bgr else ""
        logging.info("Match Info: star=%.3f, ex=%.3f, sift=%s | %s %s | State: %s", 
                     star_score, ex_score, "OK" if hp_bgr else "FL", bgr_str, dist_str, self.state.current_state.name)

        if in_battle_ui:
            # 状态判定逻辑：基于最新的 decided_action
            if self.state.last_non_none_state == RobotState.NON_BATTLE:
                if decided_action == "battle":
                    self.state.set_state(RobotState.BATTLE_CHARGE)
                elif decided_action == "escape":
                    self.state.set_state(RobotState.BATTLE_ESCAPE)
                else:
                    self.state.set_state(RobotState.NONE)
            
            elif self.state.last_non_none_state in [RobotState.BATTLE_CHARGE, RobotState.BATTLE_ESCAPE]:
                if decided_action == "battle" and self.state.current_state == RobotState.BATTLE_ESCAPE:
                    logging.warning("State Correction: Escape -> Charge detected via color!")
                    self.state.set_state(RobotState.BATTLE_CHARGE)
                elif decided_action == "escape" and self.state.current_state == RobotState.BATTLE_CHARGE:
                    logging.warning("State Correction: Charge -> Escape detected via color!")
                    self.state.set_state(RobotState.BATTLE_ESCAPE)
                
                elif self.state.current_state == RobotState.NONE:
                    self.state.set_state(self.state.last_non_none_state)
            
            elif self.state.current_state == RobotState.NONE:
                if decided_action == "battle": self.state.set_state(RobotState.BATTLE_CHARGE)
                elif decided_action == "escape": self.state.set_state(RobotState.BATTLE_ESCAPE)

            # 发布战斗检测事件
            if self.state.current_state in [RobotState.BATTLE_CHARGE, RobotState.BATTLE_ESCAPE]:
                self.event_bus.publish(BattleDetectedEvent(
                    hwnd=hwnd, full_frame=full_frame, width=width, height=height,
                    score=ex_score, template_name="exchange.png", timestamp=time.time()
                ))
            return

        # 4. 既无星号也无战斗图标，回归 NONE
        if self.state.current_state != RobotState.NONE:
            self.state.set_state(RobotState.NONE)
            
        # 如果从战斗态退出，发布结束事件
        if self.state.last_non_none_state in [RobotState.BATTLE_CHARGE, RobotState.BATTLE_ESCAPE]:
            self.event_bus.publish(BattleEndedEvent(timestamp=time.time()))

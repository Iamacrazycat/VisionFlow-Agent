import time
import json
import os
import logging
from typing import List, Dict, Any

from config import CONFIG
from src.state import BotState, AgentState
from src.events import EventBus, LifecycleTriggerEvent, NonLifecycleTriggerEvent, OtherStateDetectedEvent
from src.strategies.base import ActionStrategy
from src.stats import increment_daily_battle
from src.input import press_once, click_at
from src.vision import best_yes_score_and_loc, map_to_window
from src.window import capture_window_bgr


class CustomSequenceStrategy(ActionStrategy):
    """ 
    自定义序列策略：按照 JSON 脚本中定义的动作进行战斗。
    支持生命周期分支：非战斗、战斗(粉/绿)、其他。
    """

    def __init__(self, event_bus: EventBus, state: BotState, templates: dict) -> None:
        self.state = state
        self.templates = templates
        self.sequence_data: Dict[str, Any] = {}
        self.last_load_time = 0
        self.load_sequence()

    def register(self, event_bus: EventBus) -> None:
        """ 注册所有生命周期事件 """
        event_bus.subscribe(LifecycleTriggerEvent, self.on_battle_detected)
        event_bus.subscribe(NonLifecycleTriggerEvent, self.on_idle_detected)
        event_bus.subscribe(OtherStateDetectedEvent, self.on_other_detected)

    def load_sequence(self) -> None:
        """ 加载当前激活的序列脚本 """
        path = os.path.join(CONFIG.sequence_dir, CONFIG.active_sequence)
        if not os.path.exists(path):
            os.makedirs(CONFIG.sequence_dir, exist_ok=True)
            self.sequence_data = {}
            return

        try:
            mtime = os.path.getmtime(path)
            if mtime > self.last_load_time:
                with open(path, "r", encoding="utf-8") as f:
                    self.sequence_data = json.load(f)
                self.last_load_time = mtime
                logging.info(f"Loaded custom lifecycle sequence: {CONFIG.active_sequence}")
        except Exception as e:
            logging.error(f"Failed to load sequence: {e}")

    def run_action_list(self, steps: List[Dict], hwnd: int, full_frame: Any) -> bool:
        """ 执行一个动作列表，支持步骤级循环 """
        if not steps:
            return True

        for step in steps:
            if not CONFIG.is_running:
                return False

            # 步骤级循环
            repeat_count = int(step.get("repeat", 1))
            count = 0
            while count < repeat_count or repeat_count == -1:
                if not CONFIG.is_running:
                    return False
                
                # 在循环内部检查战斗状态（如果是战斗步骤）
                # 注意：非战斗步骤不需要检查 is_in_battle
                
                action = step.get("action")
                try:
                    if action == "press":
                        key = step.get("key")
                        delay = step.get("delay", 0.1)
                        if key:
                            press_once(hwnd, key)
                            time.sleep(delay)
                    
                    elif action == "click":
                        x, y = step.get("x", 0), step.get("y", 0)
                        delay = step.get("delay", 0.5)
                        click_at(hwnd, x, y)
                        time.sleep(delay)

                    elif action == "template_click":
                        threshold = step.get("threshold", CONFIG.match_threshold)
                        full_shot = capture_window_bgr(hwnd)
                        score, loc = best_yes_score_and_loc(full_shot, self.templates)
                        if score >= threshold:
                            h, w = full_shot.shape[:2]
                            # 这里简单假设当前窗口大小，实际应从 event 传参
                            click_x, click_y = map_to_window(loc, (h, w), (h, w)) # 简化处理
                            click_at(hwnd, click_x, click_y)
                            time.sleep(0.5)

                    elif action == "wait":
                        duration = step.get("duration", 1.0)
                        time.sleep(duration)
                except Exception as e:
                    logging.error(f"Error in action {action}: {e}")
                
                count += 1
                if repeat_count == -1: time.sleep(0.1)
        return True

    def on_battle_detected(self, event: LifecycleTriggerEvent) -> None:
        """ 战斗中分支 """
        if not self.state.can_trigger(CONFIG.trigger_cooldown_sec):
            return

        # 进场统计
        if self.state.last_non_none_state == AgentState.IDLE:
             new_count = increment_daily_battle()
             logging.info("=== 触发新生命周期！今日累计调度次数: %d ===", new_count)

        self.load_sequence()
        
        # 分支逻辑
        current = self.state.current_state
        steps = []
        if current == AgentState.LIFECYCLE_A:
            steps = self.sequence_data.get("lifecycle_a", [])
        elif current == AgentState.LIFECYCLE_B:
            steps = self.sequence_data.get("lifecycle_b", [])
        
        # 如果没有特定分支，回退到通用 steps
        if not steps:
            steps = self.sequence_data.get("steps", [])

        if steps:
            self.run_action_list(steps, event.hwnd, event.full_frame)
            self.state.mark_triggered()

    def on_idle_detected(self, event: NonLifecycleTriggerEvent) -> None:
        """ 非战斗分支 """
        if not self.state.can_trigger(CONFIG.trigger_cooldown_sec):
            return
            
        self.load_sequence()
        steps = self.sequence_data.get("idle", [])
        if steps:
            self.run_action_list(steps, event.hwnd, event.full_frame)
            self.state.mark_triggered()

    def on_other_detected(self, event: OtherStateDetectedEvent) -> None:
        """ 其他分支 """
        if not self.state.can_trigger(CONFIG.trigger_cooldown_sec):
            return
            
        self.load_sequence()
        steps = self.sequence_data.get("other", [])
        if steps:
            self.run_action_list(steps, event.hwnd, event.full_frame)
            self.state.mark_triggered()

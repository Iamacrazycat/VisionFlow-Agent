import time
import logging
import keyboard
import mss
import numpy as np

from config import CONFIG
from src.utils import log_audit, normalize_poll_interval
from src.window import find_window_by_keyword, get_client_rect_on_screen, capture_window_bgr
try:
    import win32gui
except ImportError:
    win32gui = None
from src.vision import (
    load_templates,
    preprocess,
    best_match_score,
    best_yes_score_and_loc,
    detect_purple_ratio,
)
from src.input import press_once, click_at
from src.stats import increment_daily_battle, get_daily_battle_count



class AutoRocoBot:
    def __init__(self):
        self.templates = load_templates()
        self.interval = normalize_poll_interval(CONFIG.poll_interval_sec)
        
        self.selected_mode = "battle"
        self.hit_streak = 0
        self.miss_streak = 0
        self.in_battle_state = False
        self.last_trigger_time = 0.0
        self.last_battle_time = 0.0

    def prompt_mode(self):
        logging.info("Starting detector. Stop hotkey: %s", CONFIG.stop_hotkey)
        logging.info("This script is for authorized testing only.")

        print("\n请选择运行模式:")
        print("1: 聚能模式 (自动键入 X)")
        print("2: 逃跑模式 (自动键入 ESC 并点击确认)")
        print("3: 智能挂机模式 (基于紫底自动判断：紫底则聚能，否则逃跑)")
        print("有问题或新功能建议请提 issue。如果这个项目对你有帮助，欢迎点个 Star 支持一下。")
        print("\n[提示] 脚本支持自适应分辨率，推荐使用 2K（2560x1600 或 2560x1440）以获得更高识别精度。")
        print("[提示] 逃跑模式使用物理点击，请确保“是”按钮露出且不被其他窗口遮挡。")
        
        daily_count = get_daily_battle_count()
        print(f"\n[统计] 今天已经进行了 {daily_count} 次有效战斗。")
        
        choice = input("请输入选项 (1, 2 或 3): ").strip()
        
        if choice == "2":
            self.selected_mode = "escape"
        elif choice == "3":
            self.selected_mode = "smart"
        else:
            self.selected_mode = "battle"

        mode_display = {"battle": "聚能模式", "escape": "逃跑模式", "smart": "智能挂机模式"}[self.selected_mode]
        logging.info("已选择模式: %s", mode_display)
        log_audit(
            "MODE_SELECTED",
            mode=self.selected_mode,
            match_threshold=CONFIG.match_threshold,
            trigger_cooldown_sec=CONFIG.trigger_cooldown_sec,
            escape_click_method=CONFIG.escape_click_method,
        )

    def run(self):
        with mss.mss() as sct:
            while True:
                if win32gui is not None:
                    if keyboard.is_pressed(CONFIG.stop_hotkey):
                        logging.info("Stop hotkey pressed. Exiting.")
                        break
                
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

                scale = width / CONFIG.ref_width
                if abs(scale - 1.0) > 0.05:
                    logging.debug("Scaling templates by factor: %.2f (width=%d)", scale, width)

                full_window_bgr = capture_window_bgr(hwnd)
                
                roi_left = int(width * CONFIG.roi_left_ratio)
                roi_top = int(height * CONFIG.roi_top_ratio)
                roi_w = int(width * CONFIG.roi_width_ratio)
                roi_h = int(height * CONFIG.roi_height_ratio)
                
                frame_bgr = full_window_bgr[roi_top:roi_top+roi_h, roi_left:roi_left+roi_w]
                frame_processed = preprocess(frame_bgr)

                now = time.time()
                detected, score, name = self._process_frame(frame_processed, scale)

                if detected:
                    # If it's been more than 15 seconds since we were last in a battle, it's a new encounter!
                    if now - self.last_battle_time > 15.0:
                        new_count = increment_daily_battle()
                        logging.info("=== 确认进入新战斗！今日累计战斗次数: %d ===", new_count)
                    
                    self.last_battle_time = now
                    
                    is_hit = score >= CONFIG.match_threshold
                    if is_hit and (now - self.last_trigger_time >= CONFIG.trigger_cooldown_sec):
                        self._decide_and_act(hwnd, full_window_bgr, width, height, scale, score, name, now)

                self.in_battle_state = detected
                time.sleep(self.interval)

    def _process_frame(self, frame_processed: np.ndarray, scale: float):
        score, name, center_loc = best_match_score(frame_processed, self.templates, scale=scale)
        is_hit = score >= CONFIG.match_threshold

        if is_hit:
            self.hit_streak += 1
            self.miss_streak = 0
        else:
            self.hit_streak = 0
            self.miss_streak += 1

        if not self.in_battle_state:
            detected = self.hit_streak >= CONFIG.required_hits
        else:
            detected = self.miss_streak < CONFIG.release_misses

        logging.info(
            "score=%.3f hit=%s hit_streak=%d miss_streak=%d tpl=%s",
            score,
            is_hit,
            self.hit_streak,
            self.miss_streak,
            name,
        )
        return detected, score, name

    def _decide_and_act(self, hwnd: int, full_window_bgr: np.ndarray, width: int, height: int, scale: float, score: float, name: str, now: float):
        current_action = self.selected_mode
        
        if self.selected_mode == "smart":
            purple_ratio = detect_purple_ratio(
                full_window_bgr, 
                CONFIG.purple_lower_hsv, 
                CONFIG.purple_upper_hsv
            )
            logging.info("Smart Mode: Detected Purple Ratio = %.4f (Threshold: %.4f)", purple_ratio, CONFIG.smart_mode_purple_ratio_threshold)
            if purple_ratio >= CONFIG.smart_mode_purple_ratio_threshold:
                logging.info("Smart Mode: High purple detected -> Normal Battle (Battle Mode)")
                current_action = "battle"
            else:
                logging.info("Smart Mode: Low purple detected -> Accidental Battle (Escape Mode)")
                current_action = "escape"
            
            log_audit(
                "SMART_MODE_EVALUATION",
                purple_ratio=round(purple_ratio, 4),
                threshold=CONFIG.smart_mode_purple_ratio_threshold,
                action_decided=current_action,
            )

        if current_action == "battle":
            self._execute_battle(hwnd, current_action, score, name)
            self.last_trigger_time = time.time()
        elif current_action == "escape":
            self._execute_escape(hwnd, current_action, score, name, width, height, scale)
            self.last_trigger_time = time.time() + 2.0  # extended cooldown for escape

    def _execute_battle(self, hwnd: int, action: str, score: float, name: str):
        press_once(hwnd, CONFIG.press_key)
        logging.info("Triggered key: %s (Continuous)", CONFIG.press_key)
        log_audit(
            "TRIGGER_BATTLE_KEY",
            mode=self.selected_mode,
            decided_action=action,
            key=CONFIG.press_key,
            hwnd=hwnd,
            score=round(score, 4),
            template=name,
            hit_streak=self.hit_streak,
            miss_streak=self.miss_streak,
            cooldown_sec=CONFIG.trigger_cooldown_sec,
        )

    def _execute_escape(self, hwnd: int, action: str, score: float, name: str, width: int, height: int, scale: float):
        press_once(hwnd, "esc")
        logging.info("Triggered Escape")
        log_audit(
            "TRIGGER_ESCAPE_KEY",
            mode=self.selected_mode,
            decided_action=action,
            key="esc",
            hwnd=hwnd,
            score=round(score, 4),
            template=name,
            hit_streak=self.hit_streak,
            miss_streak=self.miss_streak,
            cooldown_sec=CONFIG.trigger_cooldown_sec,
        )
        
        button_clicked = False
        yes_best_score = -1.0
        yes_best_loc = (0, 0)
        yes_threshold = CONFIG.match_threshold * 0.8
        
        for i in range(10):
            time.sleep(0.3)
            full_shot = capture_window_bgr(hwnd)
            best_score_this_round, best_loc_this_round = best_yes_score_and_loc(
                full_shot,
                self.templates,
                scale,
            )

            if best_score_this_round > yes_best_score:
                yes_best_score = best_score_this_round
                yes_best_loc = best_loc_this_round

            if best_score_this_round >= yes_threshold:
                cap_h, cap_w = full_shot.shape[:2]
                click_x = best_loc_this_round[0]
                click_y = best_loc_this_round[1]
                if cap_w > 0 and cap_h > 0 and (cap_w != width or cap_h != height):
                    click_x = int(round(best_loc_this_round[0] * width / cap_w))
                    click_y = int(round(best_loc_this_round[1] * height / cap_h))
                    click_x = max(0, min(width - 1, click_x))
                    click_y = max(0, min(height - 1, click_y))

                click_ok = click_at(hwnd, click_x, click_y)
                button_clicked = click_ok
                if click_ok:
                    log_audit(
                        "ESCAPE_YES_CLICK_SUCCESS",
                        mode=self.selected_mode,
                        hwnd=hwnd,
                        score=round(score, 4),
                        template=name,
                        yes_score=round(best_score_this_round, 4),
                        threshold=round(yes_threshold, 4),
                        click_x=click_x,
                        click_y=click_y,
                        click_method="physical",
                        attempt=i + 1,
                    )
                    break
        
        if not button_clicked:
            logging.warning("Could not find confirmation button 'yes.png' after ESC")
            log_audit(
                "ESCAPE_YES_CLICK_FAILED",
                mode=self.selected_mode,
                hwnd=hwnd,
                score=round(score, 4),
                template=name,
                best_yes_score=round(yes_best_score, 4),
                best_yes_x=yes_best_loc[0],
                best_yes_y=yes_best_loc[1],
                threshold=round(yes_threshold, 4),
                click_method="physical",
            )

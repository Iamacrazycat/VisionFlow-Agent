import os
import json
import logging
from dataclasses import dataclass, asdict, fields
from typing import Any, Dict


@dataclass
class AppConfig:
    """ 全局配置项：包含窗口名、识别阈值、颜色参数以及各类策略常量 """

    # --- 基础窗口设置 ---
    window_title_keyword: str = "洛克王国：世界"
    poll_interval_sec: float = 3.0

    # --- 战斗触发设置 ---
    press_key: str = "x"
    trigger_cooldown_sec: float = 1.0

    # --- 检测与状态设置 ---
    match_threshold: float = 0.50
    required_hits: int = 1
    release_misses: int = 2

    # --- 智能模式 (模式 3) — HP 血条颜色判断 ---
    hp_charge_targets: tuple = ((161, 63, 255), (114, 41, 114))
    hp_escape_bgr: tuple = (21, 198, 115)
    hp_color_tolerance: float = 65.0
    hp_color_margin_x_ratio: int = 6
    hp_color_margin_y_ratio: int = 4

    # --- 高级视觉 (SIFT 特征匹配 & ROI 区域) ---
    hp_template_name: str = "HP.png"
    hp_roi_ratio_x: float = 0.66
    hp_roi_ratio_y: float = 0.5
    sift_lowe_ratio: float = 0.8
    sift_min_match_count: int = 4
    sift_ransac_threshold: float = 5.0

    # --- 策略：逃跑模式 ---
    escape_click_method: str = "physical"
    yes_template_name: str = "yes.png"
    escape_yes_threshold_ratio: float = 0.8
    escape_max_attempts: int = 10
    escape_retry_delay_sec: float = 0.3
    escape_extra_cooldown_sec: float = 3.0

    # --- 输入模拟设置 ---
    input_key_duration_sec: float = 0.05
    input_mouse_delay_sec: float = 0.1

    # --- 模板文件管理 ---
    template_dir: str = "templates"
    template_pattern: str = "*.png"

    # --- 日志与调试系统 ---
    log_dir: str = "logs"
    debug_image_dir: str = "logs/debug_images"
    debug_save_images: bool = False
    debug_save_threshold: float = 0.2
    sift_match_threshold: float = 0.5
    runtime_log_name: str = "runtime.log"
    audit_log_name: str = "audit.log"

    # --- Web 仪表盘与编排器设置 ---
    # Web 服务端口
    web_port: int = 5001
    active_sequence: str = "default.json"
    sequence_dir: str = "sequences"
    
    # 运行状态控制
    running_mode: str = "smart" # charge, escape, smart, stat, custom
    is_running: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """ 将配置转为字典 """
        return asdict(self)

    def save(self, file_path: str = "config.json") -> None:
        """ 保存配置到 JSON 文件 """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    @classmethod
    def load(cls, file_path: str = "config.json") -> "AppConfig":
        """ 从 JSON 文件加载配置，如果不存在则返回默认配置 """
        if not os.path.exists(file_path):
            config = cls()
            config.save(file_path)
            return config
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                valid_field_names = {f.name for f in fields(cls)}
                filtered_data = {k: v for k, v in data.items() if k in valid_field_names}
                
                # 特殊处理元组 (JSON 中是列表)
                if "hp_charge_targets" in filtered_data:
                    filtered_data["hp_charge_targets"] = tuple(tuple(x) for x in filtered_data["hp_charge_targets"])
                if "hp_escape_bgr" in filtered_data:
                    filtered_data["hp_escape_bgr"] = tuple(filtered_data["hp_escape_bgr"])

                return cls(**filtered_data)
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return cls()


# 初始化全局配置
CONFIG = AppConfig.load()

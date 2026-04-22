from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """ 全局配置项：包含窗口名、识别阈值、颜色参数以及各类策略常量 """

    # --- 基础窗口设置 ---
    # 游戏窗口标题的关键字，用于定位窗口
    window_title_keyword: str = "洛克王国：世界"

    # 轮询间隔时间（秒）。根据要求，必须 <= 5.0。
    poll_interval_sec: float = 3.0

    # --- 战斗触发设置 ---
    # 触发时点击的按键
    press_key: str = "x"
    # 触发冷却时间（秒）。战斗中会以此间隔循环按键。
    trigger_cooldown_sec: float = 1.0

    # --- 检测与状态设置 ---
    # 模板匹配的基本阈值 (仅用于简单场景，现已主推 SIFT)
    match_threshold: float = 0.50
    # 确认进入战斗所需的连续命中帧数
    required_hits: int = 1
    # 确认退出战斗所需的连续未命中帧数
    release_misses: int = 2

    # --- 智能模式 (模式 3) — HP 血条颜色判断 ---
    # 蓄能模式目标色：包含粉色和深紫色 (BGR 格式)
    hp_charge_targets: tuple = ((161, 63, 255), (114, 41, 114))
    # 逃跑模式目标色 (绿色)
    hp_escape_bgr: tuple = (21, 198, 115)
    # 颜色匹配的欧氏距离容差
    hp_color_tolerance: float = 65.0
    # 分析血条颜色时的内部边距比例
    hp_color_margin_x_ratio: int = 6               # w // 6
    hp_color_margin_y_ratio: int = 4               # h // 4

    # --- 高级视觉 (SIFT 特征匹配 & ROI 区域) ---
    # HP 血条模板文件名
    hp_template_name: str = "HP.png"
    # HP 检测区域所占屏幕比例 (从右上角开始计算)
    hp_roi_ratio_x: float = 0.66
    hp_roi_ratio_y: float = 0.5
    # SIFT 匹配的 Lowe's ratio 阈值
    sift_lowe_ratio: float = 0.8
    # SIFT 匹配所需的最少特征点数量
    sift_min_match_count: int = 4
    # RANSAC 算法的重投影阈值
    sift_ransac_threshold: float = 5.0
    # HP 血条匹配的回退阈值（当 SIFT 失败使用模板匹配时）
    # hp_fallback_threshold: float = 0.35

    # --- 策略：逃跑模式 ---
    # 点击方式："physical" 表示模拟物理点击
    escape_click_method: str = "physical"
    # “是”确认按钮模板文件名
    yes_template_name: str = "yes.png"
    # 确认按钮的阈值比例（基于 match_threshold）
    escape_yes_threshold_ratio: float = 0.8
    # 逃跑时尝试查找确认按钮的最大次数
    escape_max_attempts: int = 10
    # 查找按钮的重试间隔（秒）
    escape_retry_delay_sec: float = 0.3
    # 逃跑成功后的额外冷却时间（秒）
    escape_extra_cooldown_sec: float = 3.0

    # --- 输入模拟设置 ---
    # 单次按键按下的持续时间（秒）
    input_key_duration_sec: float = 0.05
    # 鼠标移动或点击的操作延迟（秒）
    input_mouse_delay_sec: float = 0.1

    # --- 模板文件管理 ---
    # 模板存放目录
    template_dir: str = "templates"
    # 模板匹配的文件通配符
    template_pattern: str = "*.png"

    # --- 日志与调试系统 ---
    # 日志存放目录
    log_dir: str = "logs"
    # 调试截图存放目录
    debug_image_dir: str = "logs/debug_images"
    # 是否保存匹配调试截图（全图+画框）
    debug_save_images: bool = False
    # 触发调试保存的最低匹配分数（用于捕捉漂移/噪音）
    debug_save_threshold: float = 0.2
    
    # SIFT 匹配的置信度阈值 (0.0 到 1.0)
    sift_match_threshold: float = 0.5
    
    # 运行时日志文件名
    runtime_log_name: str = "runtime.log"
    # 审计 (Action) 日志文件名
    audit_log_name: str = "audit.log"


CONFIG = AppConfig()

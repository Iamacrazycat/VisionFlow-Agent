from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    # A visible window title keyword for your game client.
    window_title_keyword: str = "洛克王国：世界"

    # Reference resolution for template matching.
    # 2560x1600 is recommended for best matching accuracy.
    ref_width: int = 2560
    ref_height: int = 1600
    require_exact_resolution: bool = False

    # Polling interval must be <= 5.0 seconds per user requirement.
    poll_interval_sec: float = 3.0

    # Trigger exactly one key press on state transition.
    press_key: str = "x"
    # User requirement: If in battle, keep pressing X with 1.0s interval.
    trigger_cooldown_sec: float = 1.0

    # Escape mode uses physical mouse click only.
    # Keep game window and confirmation button visible when triggering escape.
    escape_click_method: str = "physical"

    # Detection settings.
    match_threshold: float = 0.50
    required_hits: int = 1
    release_misses: int = 2
    use_edge_match: bool = True

    # Right-bottom ROI ratios for 2560x1600.
    # These can be tuned without code changes.
    roi_left_ratio: float = 0.77
    roi_top_ratio: float = 0.72
    roi_width_ratio: float = 0.22
    roi_height_ratio: float = 0.27

    # Smart Mode (Mode 3) settings
    # Purple color bounds (HSV format in OpenCV: H:0-179, S:0-255, V:0-255)
    purple_lower_hsv: tuple = (125, 40, 40)
    purple_upper_hsv: tuple = (160, 255, 255)
    # The ratio of purple pixels needed to be considered a "Normal Battle"
    smart_mode_purple_ratio_threshold: float = 0.05

    # Templates.
    template_dir: str = "templates"
    template_pattern: str = "*.png"

    # Runtime controls.
    stop_hotkey: str = "f8"


CONFIG = AppConfig()

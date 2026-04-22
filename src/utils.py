import os
import logging
import json
import cv2
from datetime import datetime

from config import CONFIG

AUDIT_LOGGER_NAME = "audit"


def setup_logging() -> None:
    """ 配置全局运行时日志和审计日志的格式与存放路径 """

    os.makedirs(CONFIG.log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(
                os.path.join(CONFIG.log_dir, CONFIG.runtime_log_name), encoding="utf-8"
            ),
            logging.StreamHandler(),
        ],
    )

    # Dedicated audit log for action traceability.
    audit_logger = logging.getLogger(AUDIT_LOGGER_NAME)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
    # Clear any existing handlers in case setup_logging is called multiple times
    if audit_logger.hasHandlers():
        audit_logger.handlers.clear()
    audit_handler = logging.FileHandler(
        os.path.join(CONFIG.log_dir, CONFIG.audit_log_name), encoding="utf-8"
    )
    audit_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    audit_logger.addHandler(audit_handler)


def log_audit(event: str, **payload: object) -> None:
    """ 记录一次业务审计日志并以此持久化重要动作 """

    data = {"event": event, **payload}
    logging.getLogger(AUDIT_LOGGER_NAME).info(
        json.dumps(data, ensure_ascii=False, sort_keys=True)
    )


def save_debug_image(image: cv2.Mat, label: str, score: float = 0.0, loc: tuple = None, size: tuple = None) -> None:
    """ 保存调试截图。在图像上画出匹配框 (Bounding Box) 和分数标签 """
    if not CONFIG.debug_save_images:
        return

    os.makedirs(CONFIG.debug_image_dir, exist_ok=True)
    
    # 克隆一份以免影响原始图像
    canvas = image.copy()
    
    # 如果提供位置和尺寸，画框和文字
    if loc and size and len(loc) == 2 and len(size) == 2:
        tw, th = size
        # 计算左上角和右下角
        x1, y1 = loc[0] - tw // 2, loc[1] - th // 2
        x2, y2 = x1 + tw, y1 + th
        
        # 画面外的边界保护
        ih, iw = canvas.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(iw - 1, x2), min(ih - 1, y2)
        
        # 画矩形框 (红色, 2像素宽)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        # 写文字背景块以便阅读
        text = f"{label}: {score:.2f}"
        (t_w, t_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)
        cv2.rectangle(canvas, (x1, y1 - t_h - 5), (x1 + t_w, y1), (0, 0, 255), -1)
        cv2.putText(canvas, text, (x1, y1 - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # 生成文件名: HHMMSS_label_score.jpg
    timestamp = datetime.now().strftime("%H%M%S_%f")[:-3]
    filename = f"{timestamp}_{label}_{score:.2f}.jpg"
    path = os.path.join(CONFIG.debug_image_dir, filename)
    
    cv2.imwrite(path, canvas, [cv2.IMWRITE_JPEG_QUALITY, 85])


def normalize_poll_interval(interval: float) -> float:
    """ 对轮询间隔时间进行合法性检查和范围归一化 """

    if interval <= 0:
        logging.warning("poll_interval_sec <= 0, fallback to 5.0")
        return 5.0
    if interval > 5.0:
        logging.warning("poll_interval_sec > 5.0, clamped to 5.0")
        return 5.0
    return interval

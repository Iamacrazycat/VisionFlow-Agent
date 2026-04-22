import os
import glob
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple
import cv2
import numpy as np

from config import CONFIG


@dataclass
class Template:
    """ 识别模板数据类，包含图像矩阵 """
    name: str
    image: np.ndarray


def preprocess(image_bgr: np.ndarray) -> np.ndarray:
    """ 图像预处理：灰度化 + 高斯模糊 """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return gray


def load_templates() -> List[Template]:
    """ 从磁盘加载所有识别模板 """
    pattern = os.path.join(CONFIG.template_dir, CONFIG.template_pattern)
    paths = sorted(glob.glob(pattern))
    templates: List[Template] = []

    for path in paths:
        raw = cv2.imread(path)
        if raw is None:
            logging.warning("skip unreadable template: %s", path)
            continue
        
        # SIFT 匹配通常使用原始灰度图
        processed = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        templates.append(Template(name=os.path.basename(path), image=processed))

    if not templates:
        raise FileNotFoundError(
            "No template images found. Put PNG files into templates/ first."
        )

    logging.info("Loaded %d templates", len(templates))
    return templates


def map_to_window(
    point: Tuple[int, int], current_size: Tuple[int, int], target_size: Tuple[int, int]
) -> Tuple[int, int]:
    """ 将截图中的局部坐标映射回窗口的物理坐标 """
    curr_h, curr_w = current_size
    targ_h, targ_w = target_size
    if curr_h <= 0 or curr_w <= 0:
        return point

    mx, my = point
    # 计算比例并映射
    rx = int(round(mx * targ_w / curr_w))
    ry = int(round(my * targ_h / curr_h))

    # 边界限制
    rx = max(0, min(targ_w - 1, rx))
    ry = max(0, min(targ_h - 1, ry))
    return rx, ry


def match_features(
    frame_gray: np.ndarray, 
    template_gray: np.ndarray, 
    min_matches: int = 4
) -> Optional[Tuple[float, Tuple[int, int, int, int]]]:
    """ 统一的 SIFT 特征匹配函数，返回 (score, rect) """
    sift = cv2.SIFT_create()
    kp_frame, des_frame = sift.detectAndCompute(frame_gray, None)
    kp_tpl, des_tpl = sift.detectAndCompute(template_gray, None)

    if (
        des_tpl is None
        or len(des_tpl) < 2
        or des_frame is None
        or len(des_frame) < 2
    ):
        return None

    # FLANN 匹配
    index_params = dict(algorithm=1, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des_tpl, des_frame, k=2)

    # Lowe's ratio test
    good_matches = [m for m, n in matches if m.distance < CONFIG.sift_lowe_ratio * n.distance]

    match_count = len(good_matches)
    if match_count < min_matches:
        return None

    # 计算置信度分数 (0.0 - 1.0)
    score = min(1.0, match_count / (min_matches * 2))

    src_pts = np.float32([kp_tpl[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, CONFIG.sift_ransac_threshold)

    if M is None:
        return None

    h_tpl, w_tpl = template_gray.shape[:2]
    pts = np.float32([[0, 0], [w_tpl, 0], [w_tpl, h_tpl], [0, h_tpl]]).reshape(-1, 1, 2)
    dst = cv2.perspectiveTransform(pts, M)
    
    # 获取包围矩形
    rect = cv2.boundingRect(np.int32(dst))
    rx, ry, rw, rh = rect

    # 边界检查
    fh, fw = frame_gray.shape[:2]
    rx, ry = max(0, rx), max(0, ry)
    rw, rh = min(rw, fw - rx), min(rh, fh - ry)

    return score, (rx, ry, rw, rh)


def detect_state_icon(
    frame_bgr: np.ndarray, 
    templates: List[Template], 
    template_name: str,
    roi_region: Optional[Tuple[float, float, float, float]] = None, # (y1, y2, x1, x2) ratios
    min_matches: int = 4
) -> Tuple[float, Tuple[int, int], Tuple[int, int]]:
    """ 在指定 ROI 区域通过 SIFT 搜索特定图标 """
    fh, fw = frame_bgr.shape[:2]
    
    if roi_region:
        ry1, ry2, rx1, rx2 = roi_region
        roi_bgr = frame_bgr[int(fh*ry1):int(fh*ry2), int(fw*rx1):int(fw*rx2)]
        roi_offset = (int(fw*rx1), int(fh*ry1))
    else:
        roi_bgr = frame_bgr
        roi_offset = (0, 0)
        
    roi_gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
    
    # 查找模板
    target_tpl = next((t for t in templates if template_name.lower() in t.name.lower()), None)
    if not target_tpl:
        logging.error("Template not found: %s", template_name)
        return 0.0, (0, 0), (0, 0)

    res = match_features(roi_gray, target_tpl.image, min_matches=min_matches)
    
    if res:
        score, (rx, ry, rw, rh) = res
        # 映射回原始帧坐标
        loc = (rx + roi_offset[0] + rw // 2, ry + roi_offset[1] + rh // 2)
        return score, loc, (rw, rh)
        
    return 0.0, (0, 0), (0, 0)


def best_yes_score_and_loc(frame_bgr: np.ndarray, templates: List[Template]) -> Tuple[float, Tuple[int, int]]:
    """ 专门用于识别并定位“是”确认按钮的函数 (已转为 SIFT) """
    # 确认按钮通常在屏幕中央区域
    score, loc, size = detect_state_icon(frame_bgr, templates, CONFIG.yes_template_name, min_matches=CONFIG.sift_min_match_count)
    return score, loc


def detect_hp_bar_color(
    frame_bgr: np.ndarray,
    templates: List[Template],
    valid_targets: List[Tuple[int, int, int]],
    escape_bgr: Tuple[int, int, int],
    tolerance: float,
) -> Tuple[Optional[str], Optional[Tuple[int, int, int]], float, float]:
    """ 全 SIFT 模式：定位 HP 血条并判断战斗类型 """
    fh, fw = frame_bgr.shape[:2]
    roi_x = int(fw * CONFIG.hp_roi_ratio_x)
    roi_y_end = int(fh * CONFIG.hp_roi_ratio_y)
    roi_bgr = frame_bgr[0:roi_y_end, roi_x:]
    roi_gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)

    # 1. 查找 HP 模板
    target_tpl = next((t for t in templates if CONFIG.hp_template_name.lower() in t.name.lower()), None)
    if not target_tpl:
         return None, None, 0.0, 0.0

    # 2. 执行特征匹配
    res = match_features(roi_gray, target_tpl.image, min_matches=CONFIG.sift_min_match_count)
    if res:
        score, (rx, ry, rw, rh) = res
        if score >= CONFIG.sift_match_threshold:
            # 如果开启了调试模式，仍保留截图能力
            if CONFIG.debug_save_images:
                from src.utils import save_debug_image
                full_loc = (rx + roi_x + rw // 2, ry + rh // 2)
                save_debug_image(frame_bgr, "hp_check_sift", score, full_loc, (rw, rh))
            
            bar_bgr = roi_bgr[ry:ry+rh, rx:rx+rw]
            return _analyze_bar_color(bar_bgr, valid_targets, escape_bgr, tolerance, source="SIFT")

    return None, None, 0.0, 0.0


def _analyze_bar_color(
    bar_bgr: np.ndarray,
    valid_targets: List[Tuple[int, int, int]],
    escape_bgr: Tuple[int, int, int],
    tolerance: float,
    source: str = "",
) -> Tuple[Optional[str], Optional[Tuple[int, int, int]], float, float]:
    """ 分析血条区域的中心颜色，支持多个蓄能目标颜色 """
    h, w = bar_bgr.shape[:2]
    margin_y = max(1, h // CONFIG.hp_color_margin_y_ratio)
    margin_x = max(1, w // CONFIG.hp_color_margin_x_ratio)
    center_region = bar_bgr[margin_y:h - margin_y, margin_x:w - margin_x]

    if center_region.size == 0:
        return None, None, 0.0, 0.0

    # 使用中位数 (median)
    avg_color = np.median(center_region, axis=(0, 1))  # BGR
    bgr_tuple = (int(avg_color[0]), int(avg_color[1]), int(avg_color[2]))

    # 计算到所有“蓄能”目标颜色的最小距离
    dist_valid = min([float(np.linalg.norm(avg_color - np.array(t, dtype=np.float64))) for t in valid_targets])
    dist_escape = float(np.linalg.norm(avg_color - np.array(escape_bgr, dtype=np.float64)))

    logging.info(
        "HP bar [%s]: avg_bgr=%s dist_valid=%.1f dist_escape=%.1f",
        source, bgr_tuple, dist_valid, dist_escape,
    )

    action = None
    if dist_valid <= tolerance and dist_valid < dist_escape:
        action = "battle"
    elif dist_escape <= tolerance and dist_escape < dist_valid:
        action = "escape"
    
    return action, bgr_tuple, dist_valid, dist_escape

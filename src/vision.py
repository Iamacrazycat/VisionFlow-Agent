import os
import glob
import logging
from dataclasses import dataclass
from typing import List, Tuple
import cv2
import numpy as np

from config import CONFIG


@dataclass
class Template:
    name: str
    image: np.ndarray


def preprocess(image_bgr: np.ndarray) -> np.ndarray:
    # Always convert to gray
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    
    # If using edge match, perform Canny, otherwise simple blur is enough
    if CONFIG.use_edge_match:
        return cv2.Canny(gray, 100, 200)
    
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return gray


def load_templates() -> List[Template]:
    pattern = os.path.join(CONFIG.template_dir, CONFIG.template_pattern)
    paths = sorted(glob.glob(pattern))
    templates: List[Template] = []

    for path in paths:
        raw = cv2.imread(path)
        if raw is None:
            logging.warning("skip unreadable template: %s", path)
            continue
        # Use simple gray for yes.png if it's a simple button
        if "yes" in path.lower():
             processed = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        else:
             processed = preprocess(raw)
        templates.append(Template(name=os.path.basename(path), image=processed))

    if not templates:
        raise FileNotFoundError(
            "No template images found. Put PNG files into templates/ first."
        )

    logging.info("Loaded %d templates", len(templates))
    return templates


def best_match_score(frame_processed: np.ndarray, templates: List[Template], scale: float = 1.0) -> Tuple[float, str, Tuple[int, int]]:
    best_score = -1.0
    best_name = ""
    best_loc = (0, 0)
    fh, fw = frame_processed.shape[:2]

    for tpl in templates:
        tpl_img = tpl.image
        # If running on non-reference resolution, resize template dynamically
        if abs(scale - 1.0) > 0.01:
            new_w = max(1, int(tpl_img.shape[1] * scale))
            new_h = max(1, int(tpl_img.shape[0] * scale))
            tpl_img = cv2.resize(tpl_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        th, tw = tpl_img.shape[:2]
        if th > fh or tw > fw:
            continue
        result = cv2.matchTemplate(frame_processed, tpl_img, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val > best_score:
            best_score = float(max_val)
            best_name = tpl.name
            # Center of the match
            best_loc = (max_loc[0] + tw // 2, max_loc[1] + th // 2)

    return best_score, best_name, best_loc


def best_yes_score_and_loc(frame_bgr: np.ndarray, templates: List[Template], scale: float) -> Tuple[float, Tuple[int, int]]:
    frame_edge = preprocess(frame_bgr)
    frame_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    fh, fw = frame_gray.shape[:2]

    best_score = -1.0
    best_loc = (0, 0)

    for tpl in templates:
        if "yes" not in tpl.name.lower():
            continue
        t_img = tpl.image
        if abs(scale - 1.0) > 0.01:
            t_img = cv2.resize(
                t_img,
                (max(1, int(t_img.shape[1] * scale)), max(1, int(t_img.shape[0] * scale))),
                interpolation=cv2.INTER_AREA,
            )

        th, tw = t_img.shape[:2]
        if th > fh or tw > fw:
            continue

        res_edge = cv2.matchTemplate(frame_edge, t_img, cv2.TM_CCOEFF_NORMED)
        res_gray = cv2.matchTemplate(frame_gray, t_img, cv2.TM_CCOEFF_NORMED)
        _, max_v_edge, _, max_l_edge = cv2.minMaxLoc(res_edge)
        _, max_v_gray, _, max_l_gray = cv2.minMaxLoc(res_gray)

        cur_v, cur_l = (max_v_edge, max_l_edge) if max_v_edge > max_v_gray else (max_v_gray, max_l_gray)
        if cur_v > best_score:
            best_score = float(cur_v)
            best_loc = (cur_l[0] + tw // 2, cur_l[1] + th // 2)

    return best_score, best_loc


def detect_purple_ratio(frame_bgr: np.ndarray, lower_hsv: Tuple[int, int, int], upper_hsv: Tuple[int, int, int]) -> float:
    """
    计算图像中指定 HSV 颜色范围（通常为紫色）的像素比例。
    """
    total_pixels = frame_bgr.shape[0] * frame_bgr.shape[1]
    if total_pixels == 0:
        return 0.0
        
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    lower = np.array(lower_hsv, dtype=np.uint8)
    upper = np.array(upper_hsv, dtype=np.uint8)
    
    # 找到在设定范围内的颜色
    mask = cv2.inRange(hsv, lower, upper)
    purple_pixels = cv2.countNonZero(mask)
    
    return float(purple_pixels) / float(total_pixels)

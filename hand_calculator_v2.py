#!/usr/bin/env python3
"""
Hand Gesture Calculator
Simple working version
"""

from colors import DIGIT_COLORS, OPERATOR_COLORS, OTHER_COLORS
import cv2
import sys
import numpy as np
import time
import json
import os
import getpass
import ast
import math
import uuid
from collections import deque, Counter


RED_COLOR = (0, 0, 255)
GREEN_COLOR = (0, 255, 0)


def load_mediapipe():
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import vision
        from mediapipe.tasks import python
        return mp, vision, python
    except ImportError as e:
        print(f"ERROR: {e}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)


class Button:
    def __init__(self, x, y, w, h, label):
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.label = label
    
    def draw(self, frame, state="idle", progress=0.0, high_contrast=False):
        if self.label.isdigit():
            base_bg, hover_bg, active_bg, text_idle, text_hover, text_active = DIGIT_COLORS
        elif self.label in {"+", "-", "*", "/", "=", "."}:
            base_bg, hover_bg, active_bg, text_idle, text_hover, text_active = OPERATOR_COLORS
            text_idle = (80, 40, 130)
            text_hover = (100, 30, 160)
            text_active = (255, 255, 255)
        else:
            base_bg, hover_bg, active_bg, text_idle, text_hover, text_active = OTHER_COLORS

        if high_contrast:
            if self.label.isdigit():
                base_bg = (30, 30, 30)
                hover_bg = (0, 110, 255)
                active_bg = (0, 180, 255)
                text_idle = (255, 255, 255)
                text_hover = (255, 255, 255)
                text_active = (0, 0, 0)
            elif self.label in {"+", "-", "*", "/", "=", "."}:
                base_bg = (20, 20, 20)
                hover_bg = (0, 180, 140)
                active_bg = (0, 230, 180)
                text_idle = (230, 255, 245)
                text_hover = (255, 255, 255)
                text_active = (0, 0, 0)
            else:
                base_bg = (35, 35, 35)
                hover_bg = (120, 120, 120)
                active_bg = (220, 220, 220)
                text_idle = (255, 255, 255)
                text_hover = (255, 255, 255)
                text_active = (0, 0, 0)

        bg = base_bg
        text_color = text_idle
        border_color = (110, 110, 110)
        border_thickness = 2

        if state == "hover":
            bg = hover_bg
            text_color = text_hover
            border_color = (40, 120, 210)
            border_thickness = 3
        elif state == "active":
            bg = active_bg
            text_color = text_active
            border_color = (20, 90, 180)
            border_thickness = 4

        cv2.rectangle(frame, (self.x, self.y), (self.x+self.w, self.y+self.h), bg, -1)
        cv2.rectangle(frame, (self.x, self.y), (self.x+self.w, self.y+self.h), border_color, border_thickness)

        if state == "hover":
            pw = int(self.w * max(0.0, min(1.0, progress)))
            cv2.rectangle(
                frame,
                (self.x, self.y + self.h - 8),
                (self.x + pw, self.y + self.h),
                (40, 120, 210),
                -1,
            )

        text_size = cv2.getTextSize(self.label, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)[0]
        tx = self.x + (self.w - text_size[0]) // 2
        ty = self.y + (self.h + text_size[1]) // 2
        cv2.putText(frame, self.label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.2, text_color, 2)
    
    def contains(self, x, y, padding=0):
        return (
            (self.x - padding) < x < (self.x + self.w + padding)
            and (self.y - padding) < y < (self.y + self.h + padding)
        )


class SessionLogger:
    def __init__(self, log_dir="logs"):
        os.makedirs(log_dir, exist_ok=True)
        self.session_id = uuid.uuid4().hex[:12]
        stamp = time.strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(log_dir, f"session_{stamp}_{self.session_id}.jsonl")
        self.fp = open(self.path, "a", encoding="utf-8")

    def log_event(self, event, **data):
        payload = {
            "ts": round(time.time(), 3),
            "session_id": self.session_id,
            "event": event,
        }
        payload.update(data)
        self.fp.write(json.dumps(payload) + "\n")
        self.fp.flush()

    def close(self):
        if not self.fp.closed:
            self.fp.close()


def apply_button(equation, label):
    if label == "DEL":
        return equation[:-1]
    if label == "C":
        return ""
    if label == "=":
        try:
            return str(safe_eval_expression(equation))
        except Exception:
            return "Error"
    return equation + label


ALLOWED_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log10,
    "ln": math.log,
    "abs": abs,
    "round": round,
    "pow": pow,
}

ALLOWED_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def safe_eval_expression(expression):
    expr = (expression or "").strip()
    if not expr:
        return 0

    tree = ast.parse(expr, mode="eval")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constants are allowed")

        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op = node.op
            if isinstance(op, ast.Add):
                return left + right
            if isinstance(op, ast.Sub):
                return left - right
            if isinstance(op, ast.Mult):
                return left * right
            if isinstance(op, ast.Div):
                return left / right
            if isinstance(op, ast.FloorDiv):
                return left // right
            if isinstance(op, ast.Mod):
                return left % right
            if isinstance(op, ast.Pow):
                return left ** right
            raise ValueError("Unsupported binary operator")

        if isinstance(node, ast.UnaryOp):
            value = _eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +value
            if isinstance(node.op, ast.USub):
                return -value
            raise ValueError("Unsupported unary operator")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Unsupported function call")
            fname = node.func.id
            if fname not in ALLOWED_FUNCTIONS:
                raise ValueError(f"Function '{fname}' is not allowed")
            if node.keywords:
                raise ValueError("Keyword arguments are not allowed")
            args = [_eval(arg) for arg in node.args]
            return ALLOWED_FUNCTIONS[fname](*args)

        if isinstance(node, ast.Name):
            if node.id in ALLOWED_CONSTANTS:
                return ALLOWED_CONSTANTS[node.id]
            raise ValueError(f"Name '{node.id}' is not allowed")

        raise ValueError("Unsupported expression")

    return _eval(tree)


def clamp(value, low, high):
    return max(low, min(high, value))


def load_user_config(config_path):
    defaults = {
        "dwell_time": 0.85,
        "cooldown": 0.60,
        "smoothing": 0.30,
        "key_padding": 12,
        "large_keys": False,
        "high_contrast": False,
        "slow_mode": False,
    }
    username = getpass.getuser()

    if not os.path.exists(config_path):
        return username, defaults

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        profile = raw.get("profiles", {}).get(username, {})
        cfg = {
            "dwell_time": float(profile.get("dwell_time", defaults["dwell_time"])),
            "cooldown": float(profile.get("cooldown", defaults["cooldown"])),
            "smoothing": float(profile.get("smoothing", defaults["smoothing"])),
            "key_padding": int(profile.get("key_padding", defaults["key_padding"])),
            "large_keys": bool(profile.get("large_keys", defaults["large_keys"])),
            "high_contrast": bool(profile.get("high_contrast", defaults["high_contrast"])),
            "slow_mode": bool(profile.get("slow_mode", defaults["slow_mode"])),
        }
        return username, cfg
    except Exception:
        return username, defaults


def save_user_config(config_path, username, cfg):
    data = {"profiles": {}}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded
            data.setdefault("profiles", {})
        except Exception:
            data = {"profiles": {}}

    data["profiles"][username] = {
        "dwell_time": round(float(cfg["dwell_time"]), 3),
        "cooldown": round(float(cfg["cooldown"]), 3),
        "smoothing": round(float(cfg["smoothing"]), 3),
        "key_padding": int(cfg["key_padding"]),
        "large_keys": bool(cfg.get("large_keys", False)),
        "high_contrast": bool(cfg.get("high_contrast", False)),
        "slow_mode": bool(cfg.get("slow_mode", False)),
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def run_calibration(cap, initial_cfg, username):
    cfg = dict(initial_cfg)
    start_ts = time.time()
    duration = 30.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)

        now = time.time()
        left = max(0.0, duration - (now - start_ts))

        cv2.rectangle(frame, (70, 60), (1210, 640), (240, 245, 255), -1)
        cv2.rectangle(frame, (70, 60), (1210, 640), (60, 60, 60), 2)
        cv2.putText(frame, "Calibration: Tremor-Friendly Settings", (110, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)
        cv2.putText(frame, f"User: {username}", (110, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (40, 40, 40), 2)
        cv2.putText(frame, f"Time left: {left:0.1f}s", (950, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (30, 60, 180), 2)

        cv2.putText(frame, f"W/S  Dwell Time (s): {cfg['dwell_time']:.2f}", (110, 230),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
        cv2.putText(frame, f"E/D  Cooldown (s):   {cfg['cooldown']:.2f}", (110, 280),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
        cv2.putText(frame, f"R/F  Smoothing:      {cfg['smoothing']:.2f}", (110, 330),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
        cv2.putText(frame, f"T/G  Key Padding:    {cfg['key_padding']}", (110, 380),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)

        cv2.putText(frame, "ENTER = start app now (save settings)", (110, 470),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 120, 0), 2)
        cv2.putText(frame, "Q = quit", (110, 515),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 180), 2)
        cv2.putText(frame, "If you do nothing, app auto-starts after 30 seconds.", (110, 560),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (40, 40, 40), 2)

        cv2.imshow("Hand Calculator", frame)

        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            return None
        elif k == 13 or k == 10:
            return cfg
        elif k == ord('w'):
            cfg["dwell_time"] = clamp(cfg["dwell_time"] + 0.05, 0.30, 2.00)
        elif k == ord('s'):
            cfg["dwell_time"] = clamp(cfg["dwell_time"] - 0.05, 0.30, 2.00)
        elif k == ord('e'):
            cfg["cooldown"] = clamp(cfg["cooldown"] + 0.05, 0.10, 2.00)
        elif k == ord('d'):
            cfg["cooldown"] = clamp(cfg["cooldown"] - 0.05, 0.10, 2.00)
        elif k == ord('r'):
            cfg["smoothing"] = clamp(cfg["smoothing"] + 0.02, 0.05, 0.95)
        elif k == ord('f'):
            cfg["smoothing"] = clamp(cfg["smoothing"] - 0.02, 0.05, 0.95)
        elif k == ord('t'):
            cfg["key_padding"] = int(clamp(cfg["key_padding"] + 1, 0, 60))
        elif k == ord('g'):
            cfg["key_padding"] = int(clamp(cfg["key_padding"] - 1, 0, 60))

        if left <= 0:
            return cfg


def build_buttons(large_keys=False):
    buttons = []
    if large_keys:
        bw, bh, gap = 110, 110, 15
        sy = 90
    else:
        bw, bh, gap = 80, 80, 15
        sy = 170

    sp = bw + gap
    total_w = (4 * bw) + (3 * gap)
    sx = (1280 - total_w) // 2

    labels = [['7','8','9','/'],['4','5','6','*'],['1','2','3','-'],['0','.','=','+']]
    for r in range(4):
        for c in range(4):
            buttons.append(Button(sx + c*sp, sy + r*sp, bw, bh, labels[r][c]))
    buttons.append(Button(sx, sy + 4*sp, bw, bh, "DEL"))
    buttons.append(Button(sx + sp, sy + 4*sp, bw, bh, "C"))
    return buttons


def update_hover_dwell_state(
    voted_button,
    current_button,
    hover_elapsed,
    last_seen_on_key_ts,
    now,
    dt,
    last_press_ts,
    dwell_time_required,
    press_cooldown,
    hover_grace,
):
    pressed_button = None

    if voted_button is not None:
        if current_button is not voted_button:
            current_button = voted_button
            hover_elapsed = 0.0
        hover_elapsed += dt
        last_seen_on_key_ts = now

        can_press = (now - last_press_ts) > press_cooldown
        if hover_elapsed >= dwell_time_required and can_press:
            pressed_button = current_button
            last_press_ts = now
            hover_elapsed = 0.0
    else:
        if current_button is not None and (now - last_seen_on_key_ts) <= hover_grace:
            pass
        else:
            current_button = None
            hover_elapsed = 0.0

    return (
        current_button,
        hover_elapsed,
        last_seen_on_key_ts,
        last_press_ts,
        pressed_button,
    )


def main():
    mp, vision, python = load_mediapipe()
    print("Starting Hand Calculator...")
    
    # Model path
    model_path = "hand_landmarker.task"
    
    # Check if model exists
    if not os.path.exists(model_path):
        print(f"ERROR: Model file not found at {model_path}")
        print("Download it with: curl -L -o hand_landmarker.task https://storage.googleapis.com/mediapipe-assets/hand_landmarker.task")
        sys.exit(1)
    
    print(f"✓ Using model: {model_path}")
    
    # Create hand detector with model
    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(
            model_asset_path=model_path,
            delegate=python.BaseOptions.Delegate.CPU,
        ),
        num_hands=1
    )
    detector = vision.HandLandmarker.create_from_options(options)
    print("✓ Detector ready")
    
    # Camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: No camera!")
        sys.exit(1)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    print("✓ Ready!\n")

    config_path = "config.json"
    username, cfg = load_user_config(config_path)
    calibrated_cfg = run_calibration(cap, cfg, username)
    if calibrated_cfg is None:
        cap.release()
        cv2.destroyAllWindows()
        return
    cfg = calibrated_cfg
    save_user_config(config_path, username, cfg)

    logger = SessionLogger(log_dir="logs")
    logger.log_event(
        "session_start",
        dwell_time=cfg["dwell_time"],
        cooldown=cfg["cooldown"],
        smoothing=cfg["smoothing"],
        key_padding=cfg["key_padding"],
        large_keys=bool(cfg.get("large_keys", False)),
        high_contrast=bool(cfg.get("high_contrast", False)),
        slow_mode=bool(cfg.get("slow_mode", False)),
    )
    
    large_keys = bool(cfg.get("large_keys", False))
    high_contrast = bool(cfg.get("high_contrast", False))
    slow_mode = bool(cfg.get("slow_mode", False))
    buttons = build_buttons(large_keys)
    
    equation = ""

    # Safer interaction for hand tremor:
    # 1) Smooth pointer with exponential moving average
    # 2) Choose key via short voting window (reduces boundary jitter)
    # 3) Dwell on chosen key with grace time and cooldown
    smooth_fx, smooth_fy = None, None
    base_alpha = float(cfg["smoothing"])
    current_button = None
    hover_elapsed = 0.0
    base_dwell = float(cfg["dwell_time"])
    base_cooldown = float(cfg["cooldown"])
    base_key_padding = int(cfg["key_padding"])
    hover_grace = 0.20          # brief off-key gap allowed
    last_seen_on_key_ts = 0.0
    last_press_ts = 0.0
    active_button = None
    active_until = 0.0
    key_votes = deque(maxlen=9)
    last_frame_ts = time.time()
    interaction_state = "READY"
    false_switch_count = 0
    press_success_count = 0
    tracking_confidence = 0.0
    poor_light = False
    hand_partially_visible = False
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(frame_gray))
        poor_light = brightness < 55.0
        hand_partially_visible = False
        
        # Detect
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = detector.detect(img)
        
        fx, fy, hand_ok = -1, -1, False
        now = time.time()
        dt = max(0.0, min(0.1, now - last_frame_ts))
        last_frame_ts = now

        if slow_mode:
            alpha = min(0.95, base_alpha + 0.10)
            dwell_time_required = base_dwell + 0.35
            press_cooldown = base_cooldown + 0.25
            key_padding = base_key_padding + 8
            hover_grace = 0.30
        else:
            alpha = base_alpha
            dwell_time_required = base_dwell
            press_cooldown = base_cooldown
            key_padding = base_key_padding
            hover_grace = 0.20
        
        if result.hand_landmarks:
            hand_ok = True
            hand = result.hand_landmarks[0]
            xs = [lm.x for lm in hand]
            ys = [lm.y for lm in hand]

            visibility_margin = 0.03
            in_view_count = 0
            for lm in hand:
                if visibility_margin <= lm.x <= (1.0 - visibility_margin) and visibility_margin <= lm.y <= (1.0 - visibility_margin):
                    in_view_count += 1

            coverage_score = in_view_count / max(1, len(hand))
            min_margin = min(min(xs), 1.0 - max(xs), min(ys), 1.0 - max(ys))
            edge_score = clamp(min_margin / 0.10, 0.0, 1.0)
            bbox_area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            size_score = clamp((bbox_area - 0.01) / 0.09, 0.0, 1.0)
            raw_tracking_score = 100.0 * (0.55 * coverage_score + 0.25 * edge_score + 0.20 * size_score)
            tracking_confidence = (0.80 * tracking_confidence) + (0.20 * raw_tracking_score)
            hand_partially_visible = (coverage_score < 0.95) or (min_margin < 0.01)
            
            # Draw landmarks
            for lm in hand:
                px, py = int(lm.x*w), int(lm.y*h)
                cv2.circle(frame, (px,py), 4, (0,200,0), -1)
            
            # Draw connections
            connections = [(0,1),(1,2),(2,3),(3,4),(5,6),(6,7),(7,8),(9,10),(10,11),(11,12),
                          (13,14),(14,15),(15,16),(17,18),(18,19),(19,20),(0,5),(5,9),(9,13),(13,17)]
            for c in connections:
                try:
                    p1, p2 = hand[c[0]], hand[c[1]]
                    cv2.line(frame, (int(p1.x*w),int(p1.y*h)), (int(p2.x*w),int(p2.y*h)), (200,100,0), 2)
                except: pass
            
            # Index finger and wrist
            tip = hand[8]
            raw_fx, raw_fy = int(tip.x*w), int(tip.y*h)
            if smooth_fx is None:
                smooth_fx, smooth_fy = raw_fx, raw_fy
            else:
                smooth_fx = int(alpha * raw_fx + (1 - alpha) * smooth_fx)
                smooth_fy = int(alpha * raw_fy + (1 - alpha) * smooth_fy)
            fx, fy = smooth_fx, smooth_fy

            cv2.circle(frame, (fx,fy), 25, (0,255,255), 3)
            cv2.circle(frame, (fx,fy), 30, (0,255,255), 1)

            btn_under = next((btn for btn in buttons if btn.contains(fx, fy, padding=key_padding)), None)
            key_votes.append(btn_under)

            # Vote most frequent key over recent frames to suppress jitter.
            voted_button = None
            non_none_votes = [b for b in key_votes if b is not None]
            if non_none_votes:
                voted_button, vote_count = Counter(non_none_votes).most_common(1)[0]
                if vote_count < 4:
                    voted_button = None

            old_current_button = current_button
            old_hover_elapsed = hover_elapsed
            (
                current_button,
                hover_elapsed,
                last_seen_on_key_ts,
                last_press_ts,
                pressed_button,
            ) = update_hover_dwell_state(
                voted_button=voted_button,
                current_button=current_button,
                hover_elapsed=hover_elapsed,
                last_seen_on_key_ts=last_seen_on_key_ts,
                now=now,
                dt=dt,
                last_press_ts=last_press_ts,
                dwell_time_required=dwell_time_required,
                press_cooldown=press_cooldown,
                hover_grace=hover_grace,
            )

            if old_current_button is None and current_button is not None:
                logger.log_event("selected_key", key=current_button.label, source="acquire")
            elif old_current_button is not None and current_button is None:
                logger.log_event(
                    "hover_duration",
                    key=old_current_button.label,
                    duration_ms=int(max(0.0, old_hover_elapsed) * 1000),
                    reason="lost",
                )
            elif (
                old_current_button is not None
                and current_button is not None
                and old_current_button is not current_button
            ):
                logger.log_event(
                    "hover_duration",
                    key=old_current_button.label,
                    duration_ms=int(max(0.0, old_hover_elapsed) * 1000),
                    reason="switch",
                )
                logger.log_event("selected_key", key=current_button.label, source="switch")
                if old_hover_elapsed >= 0.15:
                    false_switch_count += 1
                    logger.log_event(
                        "false_switch",
                        from_key=old_current_button.label,
                        to_key=current_button.label,
                        hover_ms=int(old_hover_elapsed * 1000),
                    )

            if pressed_button is not None:
                press_success_count += 1
                hover_ms = int(max(dwell_time_required, old_hover_elapsed + dt) * 1000)
                logger.log_event("hover_duration", key=pressed_button.label, duration_ms=hover_ms, reason="press")
                logger.log_event("press_success", key=pressed_button.label, hover_ms=hover_ms)
                equation = apply_button(equation, pressed_button.label)
                active_button = pressed_button
                active_until = now + 0.20
                interaction_state = "PRESSED"
        else:
            tracking_confidence = max(0.0, tracking_confidence * 0.85)
            if current_button is not None:
                logger.log_event(
                    "hover_duration",
                    key=current_button.label,
                    duration_ms=int(max(0.0, hover_elapsed) * 1000),
                    reason="no_hand",
                )
            smooth_fx, smooth_fy = None, None
            current_button = None
            hover_elapsed = 0.0
            key_votes.clear()
            interaction_state = "NO HAND"
        
        panel_bg = (245, 245, 245) if high_contrast else (255, 255, 150)
        panel_border = (20, 20, 20) if high_contrast else (50, 50, 50)
        panel_text = (0, 0, 0) if high_contrast else (0, 0, 0)
        cv2.rectangle(frame, (350,20), (930,92), panel_bg, -1)
        cv2.rectangle(frame, (350,20), (930,92), panel_border, 2)
        cv2.putText(frame, equation[-20:] if equation else "0", (370,68), cv2.FONT_HERSHEY_SIMPLEX, 1.2, panel_text, 2)
        
        for btn in buttons:
            if active_button is btn and now < active_until:
                btn.draw(frame, state="active", high_contrast=high_contrast)
            elif current_button is btn:
                progress = min(1.0, hover_elapsed / dwell_time_required) if dwell_time_required > 0 else 0.0
                btn.draw(frame, state="hover", progress=progress, high_contrast=high_contrast)
            else:
                btn.draw(frame, state="idle", high_contrast=high_contrast)
        
        status = "HAND OK" if hand_ok else "NO HAND"
        color = (0,255,0) if hand_ok else (0,0,255)
        cv2.putText(frame, status, (1060,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        tracking_confidence = clamp(tracking_confidence, 0.0, 100.0)
        tx, ty, tw, th = 1000, 70, 240, 18
        cv2.rectangle(frame, (tx, ty), (tx + tw, ty + th), (230, 230, 230), -1)
        cv2.rectangle(frame, (tx, ty), (tx + tw, ty + th), (60, 60, 60), 2)
        fill_w = int((tracking_confidence / 100.0) * tw)
        bar_color = (0, 180, 0) if tracking_confidence >= 70 else (0, 170, 220) if tracking_confidence >= 40 else (0, 0, 220)
        cv2.rectangle(frame, (tx, ty), (tx + fill_w, ty + th), bar_color, -1)
        cv2.putText(frame, f"Tracking: {tracking_confidence:.0f}%", (1000, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30,30,30), 2)

        warning_lines = []
        if poor_light:
            warning_lines.append("Warning: low lighting")
        if hand_ok and hand_partially_visible:
            warning_lines.append("Warning: keep full hand in frame")
        if not hand_ok:
            warning_lines.append("Warning: show hand clearly")
        for i, msg in enumerate(warning_lines[:2]):
            cv2.putText(frame, msg, (920, 132 + i * 26), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 230), 2)
        
        hover_ms = int(max(0.0, hover_elapsed) * 1000) if current_button else 0
        cooldown_left = max(0.0, press_cooldown - (now - last_press_ts))
        if now < active_until:
            interaction_state = "PRESSED"
        elif current_button is not None:
            if hover_elapsed >= dwell_time_required and cooldown_left <= 0:
                interaction_state = "READY"
            else:
                interaction_state = f"HOVERING {hover_elapsed:.1f}s"
        elif hand_ok:
            interaction_state = "READY"

        state_color = (0, 150, 0) if interaction_state.startswith("READY") else (0, 120, 220)
        if interaction_state == "PRESSED":
            state_color = (0, 180, 0)
        elif interaction_state == "NO HAND":
            state_color = (0, 0, 220)
        cv2.putText(frame, f"State: {interaction_state}", (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.85, state_color, 2)
        cv2.putText(frame, f"Hold: {hover_ms}ms  Cooldown: {cooldown_left:.2f}s", (40, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (90,90,220), 2)
        cv2.putText(frame, f"[L] Large Keys: {'ON' if large_keys else 'OFF'}", (40, 104), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (30,30,30), 2)
        cv2.putText(frame, f"[H] High Contrast: {'ON' if high_contrast else 'OFF'}", (40, 132), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (30,30,30), 2)
        cv2.putText(frame, f"[M] Slow Mode: {'ON' if slow_mode else 'OFF'}", (40, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (30,30,30), 2)
        cv2.putText(frame, f"[[/]] Dwell: {base_dwell:.2f}s", (40, 188), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (30,30,30), 2)
        cv2.putText(frame, f"[-/=] Cooldown: {base_cooldown:.2f}s", (40, 216), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (30,30,30), 2)
        
        cv2.imshow("Hand Calculator", frame)
        
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'): break
        elif k == ord('c'): equation = ""
        elif k == ord('d'): equation = equation[:-1]
        elif k == ord('l'):
            large_keys = not large_keys
            buttons = build_buttons(large_keys)
            current_button = None
            hover_elapsed = 0.0
            key_votes.clear()
            cfg["large_keys"] = large_keys
            save_user_config(config_path, username, cfg)
            logger.log_event("setting_change", name="large_keys", value=large_keys)
        elif k == ord('h'):
            high_contrast = not high_contrast
            cfg["high_contrast"] = high_contrast
            save_user_config(config_path, username, cfg)
            logger.log_event("setting_change", name="high_contrast", value=high_contrast)
        elif k == ord('m'):
            slow_mode = not slow_mode
            current_button = None
            hover_elapsed = 0.0
            key_votes.clear()
            cfg["slow_mode"] = slow_mode
            save_user_config(config_path, username, cfg)
            logger.log_event("setting_change", name="slow_mode", value=slow_mode)
        elif k == ord('['):
            base_dwell = clamp(base_dwell - 0.05, 0.30, 2.00)
            cfg["dwell_time"] = round(base_dwell, 3)
            save_user_config(config_path, username, cfg)
            logger.log_event("setting_change", name="dwell_time", value=cfg["dwell_time"])
            current_button = None
            hover_elapsed = 0.0
            key_votes.clear()
        elif k == ord(']'):
            base_dwell = clamp(base_dwell + 0.05, 0.30, 2.00)
            cfg["dwell_time"] = round(base_dwell, 3)
            save_user_config(config_path, username, cfg)
            logger.log_event("setting_change", name="dwell_time", value=cfg["dwell_time"])
            current_button = None
            hover_elapsed = 0.0
            key_votes.clear()
        elif k == ord('-'):
            base_cooldown = clamp(base_cooldown - 0.05, 0.10, 2.00)
            cfg["cooldown"] = round(base_cooldown, 3)
            save_user_config(config_path, username, cfg)
            logger.log_event("setting_change", name="cooldown", value=cfg["cooldown"])
        elif k == ord('='):
            base_cooldown = clamp(base_cooldown + 0.05, 0.10, 2.00)
            cfg["cooldown"] = round(base_cooldown, 3)
            save_user_config(config_path, username, cfg)
            logger.log_event("setting_change", name="cooldown", value=cfg["cooldown"])

    logger.log_event(
        "session_end",
        false_switch_count=false_switch_count,
        press_success_count=press_success_count,
    )
    logger.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

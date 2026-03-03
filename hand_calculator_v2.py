#!/usr/bin/env python3
"""
Hand Gesture Calculator
Simple working version
"""

import cv2
import sys
import numpy as np
import time
from collections import deque, Counter

# Import MediaPipe
try:
    import mediapipe as mp
    from mediapipe.tasks.python import vision
    from mediapipe.tasks import python
except ImportError as e:
    print(f"ERROR: {e}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)


class Button:
    def __init__(self, x, y, w, h, label):
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.label = label
    
    def draw(self, frame, state="idle", progress=0.0):
        if self.label.isdigit():
            base_bg = (230, 245, 230)
            hover_bg = (180, 220, 180)
            active_bg = (120, 190, 120)
            text_idle = (20, 80, 20)
            text_hover = (0, 120, 0)
            text_active = (255, 255, 255)
        elif self.label in {"+", "-", "*", "/", "=", "."}:
            base_bg = (235, 225, 245)
            hover_bg = (185, 165, 220)
            active_bg = (140, 110, 200)
            text_idle = (80, 40, 130)
            text_hover = (100, 30, 160)
            text_active = (255, 255, 255)
        else:
            base_bg = (235, 235, 235)
            hover_bg = (195, 215, 235)
            active_bg = (130, 165, 205)
            text_idle = (40, 40, 40)
            text_hover = (20, 50, 90)
            text_active = (255, 255, 255)

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


def apply_button(equation, label):
    if label == "DEL":
        return equation[:-1]
    if label == "C":
        return ""
    if label == "=":
        try:
            return str(eval(equation))
        except Exception:
            return "Error"
    return equation + label


def main():
    print("Starting Hand Calculator...")
    import os
    
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
        base_options=python.BaseOptions(model_asset_path=model_path),
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
    
    # Buttons - centered on screen
    buttons = []
    sx, sy, sp, bw, bh = 408, 220, 95, 80, 80
    
    labels = [['7','8','9','/'],['4','5','6','*'],['1','2','3','-'],['0','.','=','+']]
    for r in range(4):
        for c in range(4):
            buttons.append(Button(sx+c*sp, sy+r*sp, bw, bh, labels[r][c]))
    buttons.append(Button(sx, sy+4*sp, bw, bh, "DEL"))
    buttons.append(Button(sx+sp, sy+4*sp, bw, bh, "C"))
    
    equation = ""

    # Safer interaction for hand tremor:
    # 1) Smooth pointer with exponential moving average
    # 2) Choose key via short voting window (reduces boundary jitter)
    # 3) Dwell on chosen key with grace time and cooldown
    smooth_fx, smooth_fy = None, None
    alpha = 0.30
    current_button = None
    hover_elapsed = 0.0
    dwell_time_required = 0.85  # seconds to hold pointer above a key
    hover_grace = 0.20          # brief off-key gap allowed
    last_seen_on_key_ts = 0.0
    last_press_ts = 0.0
    press_cooldown = 0.60       # seconds between accepted presses
    active_button = None
    active_until = 0.0
    key_padding = 12            # larger hit area for tremor users
    key_votes = deque(maxlen=9)
    last_frame_ts = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        # Detect
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = detector.detect(img)
        
        fx, fy, hand_ok = -1, -1, False
        now = time.time()
        dt = max(0.0, min(0.1, now - last_frame_ts))
        last_frame_ts = now
        
        if result.hand_landmarks:
            hand_ok = True
            hand = result.hand_landmarks[0]
            
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

            if voted_button is not None:
                if current_button is not voted_button:
                    current_button = voted_button
                    hover_elapsed = 0.0
                hover_elapsed += dt
                last_seen_on_key_ts = now

                can_press = (now - last_press_ts) > press_cooldown
                if hover_elapsed >= dwell_time_required and can_press:
                    equation = apply_button(equation, current_button.label)
                    last_press_ts = now
                    active_button = current_button
                    active_until = now + 0.20
                    hover_elapsed = 0.0
            else:
                # Keep progress for a short gap when hand jitters off the key.
                if current_button is not None and (now - last_seen_on_key_ts) <= hover_grace:
                    pass
                else:
                    current_button = None
                    hover_elapsed = 0.0
        else:
            smooth_fx, smooth_fy = None, None
            current_button = None
            hover_elapsed = 0.0
            key_votes.clear()
        
        # Display - centered
        cv2.rectangle(frame, (450,80), (830,140), (255,255,150), -1)
        cv2.rectangle(frame, (450,80), (830,140), (50,50,50), 2)
        cv2.putText(frame, equation[-15:] if equation else "0", (470,120), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,0), 2)
        
        for btn in buttons:
            if active_button is btn and now < active_until:
                btn.draw(frame, state="active")
            elif current_button is btn:
                progress = min(1.0, hover_elapsed / dwell_time_required) if dwell_time_required > 0 else 0.0
                btn.draw(frame, state="hover", progress=progress)
            else:
                btn.draw(frame, state="idle")
        
        status = "HAND OK" if hand_ok else "NO HAND"
        color = (0,255,0) if hand_ok else (0,0,255)
        cv2.putText(frame, status, (1100,120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        
        hover_ms = int(max(0.0, hover_elapsed) * 1000) if current_button else 0
        cooldown_left = max(0.0, press_cooldown - (now - last_press_ts))
        cv2.putText(frame, f"Hold: {hover_ms}ms", (1080,150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (90,90,220), 2)
        cv2.putText(frame, f"Cooldown: {cooldown_left:.2f}s", (1020,180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (90,90,220), 2)
        
        cv2.imshow("Hand Calculator", frame)
        
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'): break
        elif k == ord('c'): equation = ""
        elif k == ord('d'): equation = equation[:-1]
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

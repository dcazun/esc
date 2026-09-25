import json
import cv2
import numpy as np
import mediapipe as mp
import random
import time
import threading
import subprocess
import os
import sys
from collections import deque
from pathlib import Path

MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "mediapipe_detector"
    / "face_landmarker.task"
)
debug = "--debug" in sys.argv
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DETECTOR = "mediapipe"
SUPPORTED_DETECTORS = {
    "dlib",
    "mediapipe",
}

MODEL_FILE = os.path.join(
  SCRIPT_DIR,
  "shape_predictor_68_face_landmarks.dat"
)

class DoomscrollModule:
  def __init__(self):
    # choose from OpenCV, dlib, or mediapipe
    if DETECTOR == "dlib":
      self.dlib_setup()
    elif DETECTOR == "mediapipe":
      self.mediapipe_setup()
    else:
      raise ValueError(f"Unsupported detector: {DETECTOR}")
  
          
    # Detection state tracking for stability
    self.doomscroll_count = 0
    self.normal_count = 0
    self.detection_threshold = 1  # Instant response

    # Initialize score window to calculate and return confidence
    self.score_window = deque()

  def dlib_setup(self):
    try:
      import dlib
    except ImportError:
      print("dlib not found")

      install = input("Install dlib now? (y/n) ")
      if install.lower() != "y":
        raise RuntimeError("dlib is required when DETECTOR='dlib'")
            
      subprocess.check_call(
          [sys.executable, "-m", "pip", "install", "dlib"]
        )
      
      import dlib
    self.detector = dlib.get_frontal_face_detector()
    if not os.path.exists(MODEL_FILE):
      download_landmarks()

    self.predictor = dlib.shape_predictor(MODEL_FILE)

    print("Using dlib for face tracking", file=sys.stderr)

  def mediapipe_setup(self):
    try:
      import mediapipe as mp
    except ImportError:
      print("MediaPipe not found")

      install = input("Install mediapipe now? (y/n) ")
      if install.lower() != "y":
          raise RuntimeError("mediapipe is required when DETECTOR='mediapipe'")
      
      subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "mediapipe"]
      )
      import mediapipe as mp

    self.mp =  mp

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"MediaPipe model not found at: {MODEL_PATH}"
        )

    base_options = mp.tasks.BaseOptions(
        model_asset_path=str(MODEL_PATH),
        delegate=mp.tasks.BaseOptions.Delegate.CPU,
    )

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    self.landmarker = (
        mp.tasks.vision.FaceLandmarker.create_from_options(
            options
        )
    )
    
    print("Using MediaPipe for face tracking", file=sys.stderr)

  def dlib_coords(self, gray):
    """Determine coordinates using dlib landmarks"""
    faces = self.detector(gray)

    for face in faces:
      landmarks = self.predictor(gray, face)

      left_eye_corner = (
        landmarks.part(36).x,
        landmarks.part(36).y
      )

      right_eye_corner = (
        landmarks.part(45).x,
        landmarks.part(45).y
      )

      return {
        # Get key pts
        "nose_tip": (
          landmarks.part(30).x, 
          landmarks.part(30).y
        ),
        "chin": (
          landmarks.part(8).x, 
          landmarks.part(8).y
        ),
        # Left eye
        "left_eye_points": [
          (landmarks.part(i).x, landmarks.part(i).y) 
          for i in range(36, 42)
        ],
        # Right eye
        "right_eye_points": [
          (landmarks.part(i).x, landmarks.part(i).y) 
          for i in range(42, 48)
        ],
        "left_eye_corner": left_eye_corner,
        "right_eye_corner": right_eye_corner,
        "eye_center": (
          (left_eye_corner[0] + right_eye_corner[0]) / 2,
          (left_eye_corner[1] + right_eye_corner[1]) / 2
        ),
        # Compute jaw width
        "jaw_left": (
          landmarks.part(0).x,
          landmarks.part(0).y
        ),
        "jaw_right": (
          landmarks.part(16).x,
          landmarks.part(16).y
        ),
        "mouth_center_y": (landmarks.part(48).y + landmarks.part(54).y) / 2
      }
    
    return None

  def mediapipe_coords(self, frame):
    """Determine coords using MediaPipe landmarks"""
    
    # MediaPipe expects RGB, so we convert from OpenCV's BGR
    rgb_frame = cv2.cvtColor(
      frame,
      cv2.COLOR_BGR2RGB,
    )

    # Give image to MediaPipe
    mp_image = self.mp.Image(
      image_format=mp.ImageFormat.SRGB,
      data=rgb_frame,
    )

    # VIDEO mode needs increasing timestamps in milliseconds
    timestamp_ms = time.monotonic_ns() // 1_000_000

    result = self.landmarker.detect_for_video(
      mp_image,
      timestamp_ms,
    )

    if not result.face_landmarks:
      return None
    
    landmarks = result.face_landmarks[0]

    height, width = frame.shape[:2]
    
    def point(index):
      landmark = landmarks[index]

      return (
        int(landmark.x * width),
        int(landmark.y * height)
      )

    left_eye_corner = point(263)

    right_eye_corner = point(33)

    return { 
      # Get key pts
      "nose_tip": point(1),
      "chin": point(152),
      # Left eye
      "left_eye_points": [
        point(i) 
        for i in [263, 249, 390, 373, 374, 380, 381, 382, 362]

      ],
      # Right eye
      "right_eye_points": [
        point(i)
        for i in [33, 7, 163, 144, 145, 153, 154, 155, 133]
      ],
      "left_eye_corner": left_eye_corner,
      "right_eye_corner": right_eye_corner,
      "eye_center": (
        (left_eye_corner[0] + right_eye_corner[0]) / 2,
        (left_eye_corner[1] + right_eye_corner[1]) / 2
      ),
      # Compute jaw width
      "jaw_left": point(234),
      "jaw_right": point(454),
      "mouth_center_y": (point(13)[1] + point(14)[1]) / 2
    }

  def detect_doomscroll(self, frame, gray):
    """Detect doomscrolling using landmarks"""

    """Use assigned detector to deliver proper metrics"""
    if DETECTOR == "dlib":
      coords = self.dlib_coords(gray)
    elif DETECTOR == "mediapipe":
      coords = self.mediapipe_coords(frame)
    
    if coords is None:
      return None, None
    
    """METRIC 1: chin-to-nose / nose-to-eye ratio"""
    nose_tip = coords["nose_tip"]
    chin = coords["chin"]
    left_eye_points = coords["left_eye_points"]
    right_eye_points = coords["right_eye_points"]
    eye_center = coords["eye_center"]

    eye_to_nose = nose_tip[1] - eye_center[1]
    nose_to_chin = chin[1] - nose_tip[1]
    ratio = nose_to_chin / (eye_to_nose + 1e-6)

    """METRIC 2: face aspect ratio"""
    jaw_left = coords["jaw_left"]
    jaw_right = coords["jaw_right"]

    face_width = jaw_right[0] - jaw_left[0]
    face_height = chin[1] - eye_center[1]
    aspect = face_height / face_width

    """METRIC 3: nose position with face"""
    nose_fraction = eye_to_nose / (face_height + 1e-6)

    """METRIC 4: mouth-to-nose ratio"""
    mouth_center_y = coords["mouth_center_y"]

    nose_to_mouth = mouth_center_y - nose_tip[1]
    mouth_ratio = nose_to_mouth / (face_height + 1e-6)

    # Display Measurements:
    h, w = frame.shape[:2]
    x = 10
    y = 80
    dy = 30  # spacing between lines

    cv2.putText(frame, f"RATIO (chin/nose-eye): {ratio:.3f}",
      (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    cv2.putText(frame, f"ASPECT (face H/W): {aspect:.3f}",
      (x, y + dy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    cv2.putText(frame, f"NOSE FRAC: {nose_fraction:.3f}",
      (x, y + 2*dy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    cv2.putText(frame, f"MOUTH RATIO: {mouth_ratio:.3f}",
      (x, y + 3*dy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    # Draw debug points
    cv2.circle(frame, nose_tip, 3, (0, 255, 0), -1)
    cv2.circle(frame, chin, 3, (255, 0, 0), -1)

    for pt in left_eye_points + right_eye_points:
      cv2.circle(frame, pt, 2, (0, 255, 255), -1)

    """EVALUATION"""
    curr_time = time.time()
    score = posture_score(ratio, nose_fraction, mouth_ratio)

    if score <= 1:
      posture = 1
      status = "UPRIGHT"
    elif score <= 3:
      posture = 2
      status = "TRANSITION"
    else:
      posture = 3
      status = "LOOKING DOWN"
      
    # Display posture score
    cv2.putText(
        frame,
        f"POSTURE SCORE: {score}/6",
        (10, 230),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )
    cv2.putText(
        frame,
        f"POSTURE: {posture}",
        (10, 260),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )
    cv2.putText(
        frame,
        status,
        (10, 290),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0) if posture == 1 else
        (0, 255, 255) if posture == 2 else
        (0, 0, 255),
        2
    )

    if posture == 3:
      return curr_time, score
    
    return None, None

  def run(self):
    """ Main camera loop """

    """ CAMERA SETUP """
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
      print("Error: Couldn't open webcam... check permissions?")
      return

    print("Looking for your face...", file = sys.stderr)

    start_time = time.time()
    sample_duration = 5.0

    """ CAMERA LOOP """
    while cap.isOpened():
      success, frame = cap.read()
      if not success:
        continue
      
      # Flip frame horizontally for mirrored view
      frame = cv2.flip(frame, 1)
      gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

      curr_time = time.time()
      elapsed = curr_time - start_time

      # Detect posture
      frame_time, score = self.detect_doomscroll(frame, gray)

      """ DEBUG MODE """
      if debug:
        cv2.imshow("Doomscroll Detector", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
          break
        continue

      """ STORE SCORE """
      if score is not None:
          self.score_window.append((curr_time, score))

      # Once sample window is done, evaluate and exit
      if elapsed >= sample_duration:
          cap.release()
          cv2.destroyAllWindows()

          if len(self.score_window) == 0:
              # No face detected at all during the window
              result = {"distracted": False, "confidence": 0.0}
          else:
              avg_score = (
                  sum(s for _, s in self.score_window)
                  / len(self.score_window)
              )
              confidence = avg_score / 6.0
              result = {
                  "distracted": confidence >= 0.67,
                  "confidence": round(confidence, 3)
              }

          print(json.dumps(result), flush=True)
          sys.exit(0)
          
    cap.release()
    cv2.destroyAllWindows()

def download_landmarks():
  import urllib.request
  import bz2

  url = "https://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"

  output_file = "shape_predictor_68_face_landmarks.dat"
  compressed_file = output_file + ".bz2"

  print("Downloading landmark model...")
  urllib.request.urlretrieve(url, compressed_file)

  print("Extracting...")
  with bz2.BZ2File(compressed_file, "rb") as source:
     with open(output_file, "wb") as dest:
      dest.write(source.read())

  os.remove(compressed_file)

  print("Done!")

def mediapipe_point(self, landmark, frame):
  
    """Convert a MediaPipe landmark to pixel coordinates."""

    height, width = frame.shape[:2]

    x = int(landmark.x * width)
    y = int(landmark.y * height)

    return (x, y)

def posture_score(ratio, nose_frac, mouth_ratio):
  score = 0

  # METRIC 1: chin-to-nose / nose-to-eye ratio (lower = looking down)
  if ratio < 0.90:
    score += 2
  elif ratio < 1.40:
    score += 1

  # METRIC 2: nose position with face ratio (higher = looking down)
  if nose_frac > 0.52:
    score += 2
  elif nose_frac > 0.41:
    score += 1
  
  # METRIC 3: mouth-to-nose ratio (lower = looking down)
  if mouth_ratio < 0.18:
    score += 2
  elif mouth_ratio < 0.24:
    score += 1

  return score

if __name__ == '__main__':
  detector = DoomscrollModule()
  detector.run() 
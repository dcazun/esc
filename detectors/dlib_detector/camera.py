import json
import cv2
import numpy as np
import random
import time
import threading
import subprocess
import os
import sys
from collections import deque

class DoomscrollModule:
  def __init__(self):
    # we will try a series of face landmark detection, but for now, we will just use OpenCV or dlib
    try:
      import dlib
      self.detector = dlib.get_frontal_face_detector()

      # See if landmark file exists:
      model_file = "shape_predictor_68_face_landmarks.dat"
      if not os.path.exists(model_file):
          download_landmarks()
          # Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

      self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
      print("Using dlib for face tracking", file = sys.stderr)
    except ImportError:
      print("dlib not found")

      install = input("Install dlib now? (y/n)")
      if install == 'y':
        subprocess.check_call(
          [sys.executable, "-m", "pip", "install", "dlib"]
        )
        import dlib
        self.detector = dlib.get_frontal_face_detector()
        download_landmarks()
        self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
          
    # Detection state tracking for stability
    self.doomscroll_count = 0
    self.normal_count = 0
    self.detection_threshold = 1  # Instant response

    # Initialize score window to calculate and return confidence
    self.score_window = deque()



  def detect_doomscroll_dlib(self, frame, gray):
    """Detect doomscrolling using dlib landmarks"""
    faces = self.detector(gray)

    for face in faces:
      landmarks = self.predictor(gray, face)

      # Get key pts
      nose_tip = (landmarks.part(30).x, landmarks.part(30).y)
      chin = (landmarks.part(8).x, landmarks.part(8).y)

      """METRIC 1: chin-to-nose / nose-to-eye ratio"""
      # Left eye
      left_eye_points = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)]
      left_eye_corner = landmarks.part(36)
      # Right eye
      right_eye_points = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)]
      right_eye_corner = landmarks.part(45)

      eye_center = (
          (left_eye_corner.x + right_eye_corner.x) / 2,
          (left_eye_corner.y + right_eye_corner.y) / 2
      )

      eye_to_nose = nose_tip[1] - eye_center[1]
      nose_to_chin = chin[1] - nose_tip[1]
      ratio = nose_to_chin / (eye_to_nose + 1e-6)

      """METRIC 2: face aspect ratio"""
      # Compute jaw width
      jaw_left = landmarks.part(0)
      jaw_right = landmarks.part(16)

      face_width = jaw_right.x - jaw_left.x
      face_height = chin[1] - eye_center[1]

      aspect = face_height / face_width

      """METRIC 3: nose position with face"""
      nose_fraction = eye_to_nose / (face_height + 1e-6)

      """METRIC 4: mouth-to-nose ratio"""
      mouth_center_y = (
          landmarks.part(48).y +
          landmarks.part(54).y
      ) / 2

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

      return curr_time, score
    
    return None, None

  def run(self):
    """Main loop"""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
      print("Error: Couldn't open webcam... check permissions?")
      return

    print("Looking for your face...", file = sys.stderr)

    start_time = time.time()
    sample_duration = 5.0

    while cap.isOpened():
      success, frame = cap.read()
      if not success:
        continue
      
      # Flip frame horizontally for mirrored view
      frame = cv2.flip(frame, 1)
      gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

      curr_time = time.time()
      elapsed = curr_time - start_time

      frame_time, score = self.detect_doomscroll_dlib(frame, gray)

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


      """
      # Detect scrolling
      curr_time, score = self.detect_doomscroll_dlib(frame, gray)

      # If no face is detected
      if score is None:
        continue

      # Obtain 3 second sample of face posture
      self.score_window.append((curr_time, score))
      while (self.score_window and curr_time - self.score_window[0][0] > 3):
        self.score_window.popleft()
      
      # Evaluate to JSON
      if len(self.score_window) > 1:
          oldest_time = self.score_window[0][0]
          newest_time = self.score_window[-1][0]

          if newest_time - oldest_time >= 3:
              avg_score = (
                  sum(window_score for _, window_score in self.score_window)
                  / len(self.score_window)
              )

              confidence = avg_score / 6.0

              is_doomscrolling = confidence >= 0.67

              result = {
                "distracted": is_doomscrolling, # returns doomscrolling result
                "confidence": confidence
              }

              print(json.dumps(result), flush=True)
              cap.release()
              cv2.destroyAllWindows()
              sys.exit(0)
        """

def download_landmarks():
  import urllib.request
  import bz2
  import os

  url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"

  compressed_file = "shape_predictor_68_face_landmarks.dat.bz2"
  output_file = "shape_predictor_68_face_landmarks.dat"

  print("Downloading landmark model...")
  urllib.request.urlretrieve(url, compressed_file)

  print("Extracting...")
  with bz2.BZ2File(compressed_file, "rb") as source:
     with open(output_file, "wb") as dest:
      dest.write(source.read())

  os.remove(compressed_file)

  print("Done!")

def posture_score(ratio, nose_frac, mouth_ratio):
  score = 0

  # METRIC 1: chin-to-nose / nose-to-eye ratio (lower = looking down)
  if ratio < 1.81:
    score += 2
  elif ratio < 2.36:
    score += 1

  # METRIC 2: nose position with face ratio (higher = looking down)
  if nose_frac > 0.362:
    score += 2
  elif nose_frac > 0.303:
    score += 1
  
  # METRIC 3: mouth-to-nose ratio (lower = looking down)
  if mouth_ratio < 0.236:
    score += 2
  elif mouth_ratio < 0.306:
    score += 1

  return score

if __name__ == '__main__':
  detector = DoomscrollModule()
  detector.run()
    
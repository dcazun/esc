import cv2
import cv2
import numpy as np
import random
import time
import threading
import subprocess
import os
import sys
print(os.getcwd())

class DoomscrollModule:
  def __init__(self):
    # we will try a series of face landmark detection, but for now, we will just use OpenCV or dlib
    # choice = input("Use dlib for face tracking? (y/n)")
    choice = 'y'
    if choice == 'y':
      try:
        import dlib
        self.use_dlib = True
        self.detector = dlib.get_frontal_face_detector()

        # See if landmark file exists:
        model_file = "shape_predictor_68_face_landmarks.dat"
        if not os.path.exists(model_file):
            download_landmarks()
            # Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

        self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
        print("Using dlib for face tracking")
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
          
          self.use_dlib = True
    else:
      self.use_dlib = False
      self.face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
      )
      self.eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_eye.xml'
      )
      print("Using OpenCV Haar Cascades for face tracking")

    self.talks = [
      "Lock in, pilot.",
      "Try like, 5 minutes of work and see how it goes...",
      "If you need a break, take a walk with some music :)",
      "I'm out of things to say.",
      "Think about how long this scroll sesh has been going on.",
      "The algorithm won this battle, but you can still win the war!",
      "Does your favorite hero scroll? Be like them!",
      "Is this working? Please feel free to give feedback -- it's very much appreciated.",
      "ESCAPE WILL MAKE ME GOD_",
      "I'm not an ai, yet.",
      "The phone can wait. Your future can't.",
      "I'm hungry.",
      "Have you tried a sport? It'll change you.",
      "I miss my cat.",
      "I miss my dog.",
      "Do you have pets?"
    ]
    self.last_talk_time = 0
    self.talk_cooldown = 3  # seconds between roasts
    self.current_talk = ""
    self.prev_eye_ratio = 0.5

    # Detection state tracking for stability
    self.doomscroll_count = 0
    self.normal_count = 0
    self.detection_threshold = 3  # Frames needed to confirm state change

    # Detection state tracking for stability
    self.doomscroll_count = 0
    self.normal_count = 0
    self.detection_threshold = 1  # Instant response


  def dlib_calibration(self, frame, gray):
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

      return (posture == 3)

    return False


  def detect_doomscroll_dlib(self, frame, gray):
    """Detect doomscrolling using dlib landmarks"""
    faces = self.detector(gray)

    for face in faces:
      landmarks = self.predictor(gray, face)

      # Get key pts
      nose_tip = (landmarks.part(30).x, landmarks.part(30).y)
      chin = (landmarks.part(8).x, landmarks.part(8).y)
      forehead_approx = (landmarks.part(27).x, landmarks.part(27).y)

      # Eyes
      # Left eye pts
      left_eye_points = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)]
      # Right eye pts
      right_eye_points = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)]

      # Calculate eye aspect ratio
      left_eye_top = (left_eye_points[1][1] + left_eye_points[2][1]) / 2
      left_eye_bottom = (left_eye_points[4][1] + left_eye_points[5][1]) / 2
      left_eye_center = (left_eye_points[0][1] + left_eye_points[3][1]) / 2

      right_eye_top = (right_eye_points[1][1] + right_eye_points[2][1]) / 2
      right_eye_bottom = (right_eye_points[4][1] + right_eye_points[5][1]) / 2
      right_eye_center = (right_eye_points[0][1] + right_eye_points[3][1]) / 2

      # Vertical eye position ratio
      left_ratio = abs(left_eye_center - left_eye_top) / (abs(left_eye_bottom - left_eye_top) + 1e-6)
      right_ratio = abs(right_eye_center - right_eye_top) / (abs(right_eye_bottom - right_eye_top) + 1e-6)
      eye_ratio = (left_ratio + right_ratio) / 2

      # Head tilt detection
      head_tilt = (chin[1] - nose_tip[1]) / (nose_tip[1] - forehead_approx[1] + 1e-6)

      # Looking down if head tilted forward or eyes positioned low
      is_looking_down = head_tilt > 1.3 or eye_ratio < 0.35

      # Draw debug points
      cv2.circle(frame, nose_tip, 3, (0, 255, 0), -1)
      cv2.circle(frame, chin, 3, (255, 0, 0), -1)
      for pt in left_eye_points + right_eye_points:
        cv2.circle(frame, pt, 2, (0, 255, 255), -1)

      return is_looking_down

    return False

  def detect_doomscroll_opencv(self, frame, gray):
    """Detect doomscrolling via OpenCV Haar Cascades"""
    faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:

      # Draw face rectangle
      cv2.rectangle(
        frame,
        (x, y),
        (x+w, y+h),
        (0, 255, 0),
        2
      )

      # Region of interest for eyes
      roi_gray = gray[y:y+int(h*0.6), x:x+w]
      roi_color = frame[y:y+int(h*0.6), x:x+w]

      eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 5)

      # Detection criteria for better accuracy
      detection_score = 0

      # 1. Calculate face position - if face is in lower half => looking down
      face_center_y = y + h/2
      frame_height = frame.shape[0]
      face_position_ratio = face_center_y / frame_height
      
      if face_position_ratio > 0.58:
        detection_score += 2
      elif face_position_ratio > 0.52:
        detection_score += 1

      # 2. Check face aspect ratio (looking down => face appears shorter/wider)
      aspect_ratio = h / w
      if aspect_ratio < 1.1:
        detection_score += 1
      
      #3. Also check eye positions
      if len(eyes) >= 2:
        eye_y_positions = [y + ey + eh//2 for (ex, ey, ew, eh) in eyes]
        avg_eye_y = sum(eye_y_positions) / len(eye_y_positions)
        eye_position_in_face = (avg_eye_y - y) / h

        # If eyes are in lower part of detected face region = looking down
        if eye_position_in_face > 0.6:
          detection_score += 2
        elif eye_position_in_face > 0.52:
          detection_score += 1

        # Draw eye rectangles
        for (ex, ey, ew, eh) in eyes:
          cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)
      elif len(eyes) < 2:
        # If we can't detect eyes well, might be looking down
        detection_score += 1
      
      # Decision: doomscrolling if scroe >= 3
      is_looking_down = detection_score >= 3

      return is_looking_down

    return False

  def display_talk(self, frame):
    """Display phrases and messages on frame"""
    current_time = time.time()

    if current_time - self.last_talk_time > self.talk_cooldown:
      self.current_talk = random.choice(self.talks)
      self.last_talk_time = current_time

    # Overlay + Background
    overlay = frame.copy()
    h, w = frame.shape[:2]

    cv2.rectangle(overlay, (0, 0), (w, 150), (0, 0, 255), -1)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

    # Text
    cv2.putText(frame, "SCROLLING DETECTED!", (w//2 - 250, 50),
      cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 3)
    cv2.putText(frame, self.current_talk, (w//2 - 300, 100),
      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

  def run(self):
    """Main loop"""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
      print("Error: Couldn't open webcam... check permissions?")
      return

    print("Looking for your face...")
    print("Press 'q' to quit")

    while cap.isOpened():
      success, frame = cap.read()
      if not success:
        print("Failed to grab frame")
        continue
      
      # Flip frame horizontally for mirrored view
      frame = cv2.flip(frame, 1)
      gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

      # Detect scrolling
      # TODO: Change back from calibration to detect_doomscroll_dlib(frame, gray)
      if self.use_dlib:
        raw_detection = self.dlib_calibration(frame, gray)
      else:
        raw_detection = self.detect_doomscroll_opencv(frame, gray)

      # Stabelize detection with frame counting to avoid flickering
      if raw_detection:
        self.doomscroll_count += 1
        self.normal_count = 0
      else:
        self.normal_count += 1
        self.doomscroll_count = 0

      # Trigger if detected consistently for threshold frames
      is_doomscrolling = self.doomscroll_count >= self.detection_threshold
      is_normal = self.normal_count >= self.detection_threshold

      if is_doomscrolling:
        self.display_talk(frame)
      elif is_normal:
        cv2.putText(frame, "Good job! You're doing better than you think!", (10, 30),
          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
      else:
        cv2.putText(frame, "Monitoring...", (10, 30),
          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
      
      # Display frame
      cv2.imshow('Doomscrolling Detector', frame)

      # Exit on 'q'
      if cv2.waitKey(5) & 0xFF == ord('q'):
        break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

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
    
from __future__ import annotations

import time
from pathlib import Path

import cv2
import mediapipe as mp

MODEL_PATH = Path(__file__).resolve().parent / "face_landmarker.task"

def draw_landmarks(frame, face_landmarks) -> None:
    height, width = frame.shape[:2]

    for index, landmark in enumerate(face_landmarks):
        x = int(landmark.x * width)
        y = int(landmark.y * height)

        if 0 <= x < width and 0 <= y < height:
            cv2.circle(
                frame,
                (x, y),
                1,
                (0, 255, 0),
                -1,
            )

            cv2.putText(
                frame,
                str(index),
                (x + 2, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.3,
                (255, 255, 255),
                1,
            )

def main() -> None:
  if not MODEL_PATH.exists():
    raise FileNotFoundError(
      f"MediaPipe model not found at: {MODEL_PATH}"
    )

  base_options = mp.tasks.BaseOptions(
    model_asset_path=str(MODEL_PATH)
  )

  options = mp.tasks.vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_faces=1,
    min_face_detection_confidence=0.5,
    min_face_presence_confidence=0.5,
    min_tracking_confidence=0.5,
  )

  camera = cv2.VideoCapture(0)

  if not camera.isOpened():
    raise RuntimeError("Unable to open webcam.")

  try:
    with mp.tasks.vision.FaceLandmarker.create_from_options(
      options
    ) as landmarker:
      while True:
        success, frame = camera.read()

        if not success:
          print("Failed to read webcam frame.")
          break
        
        rgb_frame = cv2.cvtColor(
          frame,
          cv2.COLOR_BGR2RGB,
        )

        mp_image = mp.Image(
          image_format=mp.ImageFormat.SRGB,
          data=rgb_frame,
        )

        # VIDEO mode requires increasing timestamps in milliseconds.
        timestamp_ms = time.monotonic_ns() // 1_000_000

        result = landmarker.detect_for_video(
          mp_image,
          timestamp_ms,
        )

        if result.face_landmarks:
          face_landmarks = result.face_landmarks[0]
          draw_landmarks(frame, face_landmarks)

          cv2.putText(
            frame,
            "Face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
          )
        else:
          cv2.putText(
            frame,
            "No face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
          )
        
        cv2.imshow(
          "ESC MediaPipe Face Landmarker",
          frame,
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
          break
  finally:
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
  main()

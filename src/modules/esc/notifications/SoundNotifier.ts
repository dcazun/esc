import alertChime from "../../../assets/sounds/alert_chime.mp3";

const postureSound = new Audio(alertChime);

postureSound.volume = 0.35;
postureSound.preload = "auto";

export async function playPostureSound(): Promise<void> {
  try {
    postureSound.currentTime = 0;
    await postureSound.play();
  } catch (error) {
    console.error("Failed to play posture sound:", error);
  }
}
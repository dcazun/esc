use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::State;

// Holds the running detector process, if any.
// Wrapped in a Mutex because Tauri commands can be called from multiple
// threads, and Rust requires explicit locking for shared mutable data.
struct DetectorState(Mutex<Option<Child>>);

// Hardcoded path for now — this will move into config once we have more
// than one detector backend to choose between.
const VENV_PYTHON: &str =
    "/Users/snappy/projects/personal/esc/detectors/dlib_detector/venv/bin/python3";
const CAMERA_SCRIPT: &str =
    "/Users/snappy/projects/personal/esc/detectors/dlib_detector/camera.py";


#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn start_detector(state: State<DetectorState>) -> Result<String, String> {
    let mut guard = state.0.lock().map_err(|e| e.to_string())?;

    if guard.is_some() {
        return Err("Detector is already running.".into());
    }

    // For now, stdout/stderr inherit through to the terminal running
    // `npm run tauri dev` — we'll capture this into the app properly
    // once camera.py outputs structured JSON.
    let child = Command::new(VENV_PYTHON)
        .arg(CAMERA_SCRIPT)
        .spawn()
        .map_err(|e| format!("Failed to start detector: {e}"))?;

    *guard = Some(child);
    Ok("Detector started.".into())
}

#[tauri::command]
fn stop_detector(state: State<DetectorState>) -> Result<String, String> {
    let mut guard = state.0.lock().map_err(|e| e.to_string())?;

    match guard.take() {
        Some(mut child) => {
            child.kill().map_err(|e| format!("Failed to stop detector: {e}"))?;
            Ok("Detector stopped.".into())
        }
        None => Err("Detector is not running.".into()),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(DetectorState(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![greet, start_detector, stop_detector])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
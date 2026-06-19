use std::process::{Child, Command, Stdio};
use std::io::{BufRead, BufReader};
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

// Represents the JSON contract between Python and React
#[derive(serde::Serialize, serde::Deserialize)]
struct DetectionResult {
    distracted: bool,
    confidence: f32,
}

// Spawns camera.py, waits for it to finish, reads the one JSON line it emits,
// perses it, and returns the result to React as a serialized object.
#[tauri::command]
fn start_detector(state: State<DetectorState>) -> Result<DetectionResult, String> {
    let guard = state.0.lock().map_err(|e| e.to_string())?;

    if guard.is_some() {
        return Err("Detector is already running.".into());
    }

    // For now, stdout/stderr inherit through to the terminal running
    // `npm run tauri dev` — we'll capture this into the app properly
    // once camera.py outputs structured JSON.
    let mut child = Command::new(VENV_PYTHON)
        .arg(CAMERA_SCRIPT)
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit()) // debug print still goes to terminal
        .spawn()
        .map_err(|e| format!("Failed to start detector: {e}"))?;
    
    // Read out first line Python prints to stdout
    let stdout = child.stdout.take()
        .ok_or("Failed to capture stdout")?;
    let mut reader = BufReader::new(stdout);
    let mut line = String::new();
    reader.read_line(&mut line)
        .map_err(|e| format!("Failed to read detector output: {e}"))?;
    
    // Wait for process to fully exit
    child.wait().map_err(|e| format!("Detector process error: {e}"))?;

    // Parse the JSON line into DetectionResult
    let result: DetectionResult = serde_json::from_str(line.trim())
        .map_err(|e| format!("Failed to parse detector output: {e}\nRaw: {line}"))?;

    Ok(result)
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
        .invoke_handler(tauri::generate_handler![start_detector, stop_detector])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
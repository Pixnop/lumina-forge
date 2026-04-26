use std::collections::VecDeque;
use std::sync::{Arc, Mutex};

use chrono::Local;
use tauri::{AppHandle, Manager, RunEvent, State, WindowEvent};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

mod save_import;

const LOG_CAPACITY: usize = 200;

/// Holds the Python API sidecar so we can terminate it when the app exits.
struct Sidecar(Mutex<Option<CommandChild>>);

/// Ring buffer of lines captured from the sidecar's stdout/stderr.
#[derive(Default, Clone)]
struct SidecarLogs(Arc<Mutex<VecDeque<String>>>);

impl SidecarLogs {
    fn push(&self, stream: &str, line: &str) {
        let stamped = format!(
            "{} {:<6} {}",
            Local::now().format("%H:%M:%S"),
            stream,
            line.trim_end()
        );
        let mut buf = self.0.lock().unwrap();
        if buf.len() >= LOG_CAPACITY {
            buf.pop_front();
        }
        buf.push_back(stamped);
    }

    fn snapshot(&self) -> Vec<String> {
        self.0.lock().unwrap().iter().cloned().collect()
    }

    fn clear(&self) {
        self.0.lock().unwrap().clear();
    }
}

#[tauri::command]
fn get_sidecar_logs(logs: State<'_, SidecarLogs>) -> Vec<String> {
    logs.snapshot()
}

#[tauri::command]
fn clear_sidecar_logs(logs: State<'_, SidecarLogs>) -> () {
    logs.clear();
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(Sidecar(Mutex::new(None)))
        .manage(SidecarLogs::default())
        .invoke_handler(tauri::generate_handler![
            get_sidecar_logs,
            clear_sidecar_logs,
            save_import::read_save_as_json
        ])
        .setup(|app| {
            spawn_sidecar(app.handle())?;
            Ok(())
        })
        .on_window_event(|window, event| {
            // Cascade kill on the user clicking X — ExitRequested in run()
            // only fires after every window has closed, which can race if
            // the sidecar survives the close a few hundred ms.
            if let WindowEvent::CloseRequested { .. } = event {
                if let Some(child) = window
                    .app_handle()
                    .state::<Sidecar>()
                    .0
                    .lock()
                    .unwrap()
                    .take()
                {
                    let _ = child.kill();
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let RunEvent::ExitRequested { .. } = event {
                if let Some(child) = app_handle.state::<Sidecar>().0.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        });
}

fn spawn_sidecar(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let vault_dir = app
        .path()
        .resource_dir()
        .map(|p| p.join("resources/vault"))
        .ok();

    let mut command = app
        .shell()
        .sidecar("lumina-forge-api")
        .expect("sidecar binary missing — did `build_api_exe.py` run?");

    // Hand the sidecar our PID so it can self-terminate on force-kill.
    let parent_pid = std::process::id().to_string();
    command = command.arg("--parent-pid").arg(parent_pid);

    if let Some(vault) = vault_dir.as_ref() {
        command = command
            .arg("--vault-dir")
            .arg(vault.to_string_lossy().to_string());
    }

    let (mut rx, child) = command.spawn().expect("failed to spawn API sidecar");
    app.state::<Sidecar>().0.lock().unwrap().replace(child);

    let logs: SidecarLogs = (*app.state::<SidecarLogs>()).clone();
    logs.push("sys", "sidecar spawned");

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                    let s = String::from_utf8_lossy(&line).to_string();
                    log::info!("api/out: {}", s);
                    logs.push("out", &s);
                }
                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                    let s = String::from_utf8_lossy(&line).to_string();
                    log::info!("api/err: {}", s);
                    logs.push("err", &s);
                }
                tauri_plugin_shell::process::CommandEvent::Terminated(status) => {
                    let msg = format!("sidecar exited: code={:?} signal={:?}", status.code, status.signal);
                    log::info!("{}", msg);
                    logs.push("sys", &msg);
                    break;
                }
                _ => {}
            }
        }
    });

    Ok(())
}

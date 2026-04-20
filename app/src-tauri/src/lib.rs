use std::sync::Mutex;

use tauri::{Manager, RunEvent, WindowEvent};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

/// Holds the Python API sidecar so we can terminate it when the app exits.
struct Sidecar(Mutex<Option<CommandChild>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .manage(Sidecar(Mutex::new(None)))
        .setup(|app| {
            // Spawn the PyInstaller-bundled API as a sidecar. The binary
            // lives next to the Tauri executable at runtime (Tauri copies
            // `binaries/lumina-forge-api-<triple>.exe` → the resource root).
            //
            // `vault/` is bundled under the OS-specific resource directory;
            // we pass it through via --vault-dir so the sidecar can find it.
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

            // Drain the sidecar's stdout/stderr into our own log so we
            // don't leak file descriptors and can see early failures.
            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                            log::info!("api/out: {}", String::from_utf8_lossy(&line));
                        }
                        tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                            log::info!("api/err: {}", String::from_utf8_lossy(&line));
                        }
                        tauri_plugin_shell::process::CommandEvent::Terminated(status) => {
                            log::info!("api sidecar exited: {:?}", status);
                            break;
                        }
                        _ => {}
                    }
                }
            });

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

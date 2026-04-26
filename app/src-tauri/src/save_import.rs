//! Read an Expedition 33 GVAS save file and surface it to the UI as JSON.
//!
//! The heavy work — turning ~120 KB of Unreal-serialised binary into a
//! navigable property tree — happens here via the `uesave` crate (same one
//! the Infarctus save editor uses). The frontend then walks the JSON to
//! pull out the inventory state and translate Unreal asset names into the
//! kebab-case slugs our vault uses.
use std::fs::File;
use std::path::Path;

use uesave::Save;

/// Parse a `.sav` file and return its contents as a JSON string.
///
/// The frontend is responsible for navigating the resulting structure —
/// keeping the Rust side dumb makes it trivial to iterate on the inventory
/// extraction without rebuilding the Tauri binary.
#[tauri::command]
pub fn read_save_as_json(path: String) -> Result<String, String> {
    let p = Path::new(&path);
    if !p.is_file() {
        return Err(format!("save file not found: {path}"));
    }
    let mut f = File::open(p).map_err(|e| format!("open {path}: {e}"))?;
    let save = Save::read(&mut f).map_err(|e| format!("parse {path}: {e}"))?;
    serde_json::to_string(&save).map_err(|e| format!("serialise: {e}"))
}

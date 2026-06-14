//! Load and verify a .capsule archive (zstd-compressed tar).

use crate::error::ReplayError;
use crate::event::{Event, Manifest, SessionMetadata};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::io::{Cursor, Read};
use std::path::Path;

pub struct CapsuleArchive {
    pub manifest: Manifest,
    pub session: SessionMetadata,
    pub events: Vec<Event>,
    pub cassettes: HashMap<String, serde_json::Value>,
    pub snapshots: HashMap<usize, serde_json::Value>,
}

impl CapsuleArchive {
    pub fn load(path: &Path) -> Result<Self, ReplayError> {
        let compressed = std::fs::read(path)?;
        Self::from_bytes(&compressed)
    }

    pub fn from_bytes(data: &[u8]) -> Result<Self, ReplayError> {
        // Decompress zstd
        let mut decoder =
            zstd::Decoder::new(Cursor::new(data)).map_err(|e| ReplayError::Zstd(e.to_string()))?;
        let mut tar_bytes = Vec::new();
        decoder
            .read_to_end(&mut tar_bytes)
            .map_err(|e| ReplayError::Zstd(e.to_string()))?;

        // Parse tar
        let mut archive = tar::Archive::new(Cursor::new(&tar_bytes));
        let mut files: HashMap<String, Vec<u8>> = HashMap::new();

        for entry in archive.entries()? {
            let mut entry = entry?;
            let name = entry.path()?.to_string_lossy().to_string();
            let mut content = Vec::new();
            entry.read_to_end(&mut content)?;
            files.insert(name, content);
        }

        // Parse manifest
        let manifest_bytes = files
            .get("manifest.json")
            .ok_or(ReplayError::Archive("missing manifest.json".into()))?;
        let manifest: Manifest = serde_json::from_slice(manifest_bytes)?;

        // Version check
        if !manifest.capsule_version.starts_with("1.") {
            return Err(ReplayError::UnsupportedVersion(
                manifest.capsule_version.clone(),
            ));
        }

        // Parse session
        let session_bytes = files
            .get("session.json")
            .ok_or(ReplayError::SessionNotFound)?;
        let session: SessionMetadata = serde_json::from_slice(session_bytes)?;

        // Parse events (sorted by filename)
        let mut event_files: Vec<&String> =
            files.keys().filter(|k| k.starts_with("events/")).collect();
        event_files.sort();

        let mut events = Vec::new();
        let mut event_blobs: Vec<Vec<u8>> = Vec::new();
        for ef in event_files {
            let blob = files[ef].clone();
            let event: Event = serde_json::from_slice(&blob)?;
            events.push(event);
            event_blobs.push(blob);
        }

        // Parse cassettes
        let mut cassettes = HashMap::new();
        let mut cassette_blobs: Vec<Vec<u8>> = Vec::new();
        let mut cassette_files: Vec<&String> = files
            .keys()
            .filter(|k| k.starts_with("cassettes/"))
            .collect();
        cassette_files.sort();
        for cf in cassette_files {
            let blob = files[cf].clone();
            let data: serde_json::Value = serde_json::from_slice(&blob)?;
            let id = cf
                .strip_prefix("cassettes/")
                .unwrap_or(cf)
                .strip_suffix(".json")
                .unwrap_or(cf)
                .to_string();
            cassettes.insert(id, data);
            cassette_blobs.push(blob);
        }

        // Parse snapshots
        let mut snapshots = HashMap::new();
        let mut snapshot_files: Vec<&String> = files
            .keys()
            .filter(|k| k.starts_with("snapshots/"))
            .collect();
        snapshot_files.sort();
        for sf in snapshot_files {
            let data: serde_json::Value = serde_json::from_slice(&files[sf])?;
            let step_str = sf
                .strip_prefix("snapshots/step-")
                .unwrap_or("0")
                .strip_suffix(".json")
                .unwrap_or("0");
            if let Ok(step) = step_str.parse::<usize>() {
                snapshots.insert(step, data);
            }
        }

        // Verify integrity
        let computed_events_hash = sha256_of_blobs(&event_blobs);
        if !manifest.integrity.events_hash.is_empty()
            && computed_events_hash != manifest.integrity.events_hash
        {
            return Err(ReplayError::IntegrityMismatch {
                expected: manifest.integrity.events_hash.clone(),
                actual: computed_events_hash,
            });
        }

        Ok(CapsuleArchive {
            manifest,
            session,
            events,
            cassettes,
            snapshots,
        })
    }
}

fn sha256_of_blobs(blobs: &[Vec<u8>]) -> String {
    let mut hasher = Sha256::new();
    for blob in blobs {
        hasher.update(blob);
    }
    hex::encode(hasher.finalize())
}

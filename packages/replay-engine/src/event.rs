use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub event_id: String,
    pub session_id: String,
    pub step_index: usize,
    pub parent_event_id: Option<String>,
    pub event_type: String,
    pub timestamp: String,
    pub duration_ms: f64,
    pub payload: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionMetadata {
    pub session_id: String,
    pub agent_name: String,
    pub agent_version: Option<String>,
    pub started_at: String,
    pub ended_at: Option<String>,
    pub duration_ms: Option<f64>,
    pub status: String,
    pub step_count: usize,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(default)]
    pub user_metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Manifest {
    pub capsule_version: String,
    pub session_id: String,
    pub integrity: IntegrityBlock,
    pub compression: CompressionBlock,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntegrityBlock {
    pub algorithm: String,
    pub events_hash: String,
    pub cassettes_hash: String,
    pub snapshots_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompressionBlock {
    pub algorithm: String,
    pub level: u32,
}

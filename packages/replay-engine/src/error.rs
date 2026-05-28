use thiserror::Error;

#[derive(Debug, Error)]
pub enum ReplayError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("JSON parse error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("Zstd decompression error: {0}")]
    Zstd(String),

    #[error("Archive error: {0}")]
    Archive(String),

    #[error("Integrity check failed: expected {expected}, got {actual}")]
    IntegrityMismatch { expected: String, actual: String },

    #[error("Session not found in archive")]
    SessionNotFound,

    #[error("Cassette not found for event {event_id}")]
    CassetteNotFound { event_id: String },

    #[error("Step index {0} out of range")]
    StepOutOfRange(usize),

    #[error("Unsupported capsule version: {0}")]
    UnsupportedVersion(String),
}

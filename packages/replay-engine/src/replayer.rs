//! Replayer — core engine for deterministic cassette replay and branching.

use crate::archive::CapsuleArchive;
use crate::cassette::CassetteStore;
use crate::error::ReplayError;
use crate::event::Event;
use crate::session::ReplaySession;
use std::collections::HashMap;
use std::path::Path;

pub struct Replayer {
    archive: CapsuleArchive,
    cassettes: CassetteStore,
}

/// Result of a completed replay.
#[derive(Debug)]
pub struct ReplayResult {
    pub session_id: String,
    pub replayed_events: Vec<Event>,
    pub step_count: usize,
    pub branch_point: Option<usize>,
}

/// Modifications applied at a branch point.
#[derive(Debug, Default, Clone)]
pub struct BranchModifications {
    pub temperature: Option<f64>,
    pub max_tokens: Option<u32>,
    pub seed: Option<i64>,
    pub system_prompt: Option<String>,
    pub tool_response_overrides: HashMap<String, serde_json::Value>,
}

impl Replayer {
    /// Load a .capsule file and prepare for replay.
    pub fn from_file(path: &Path) -> Result<Self, ReplayError> {
        let archive = CapsuleArchive::load(path)?;
        let cassettes = CassetteStore::new(archive.cassettes.clone());
        Ok(Self { archive, cassettes })
    }

    /// Load from in-memory bytes.
    pub fn from_bytes(data: &[u8]) -> Result<Self, ReplayError> {
        let archive = CapsuleArchive::from_bytes(data)?;
        let cassettes = CassetteStore::new(archive.cassettes.clone());
        Ok(Self { archive, cassettes })
    }

    /// Replay the entire session deterministically using cassette responses.
    pub fn replay(&self) -> Result<ReplayResult, ReplayError> {
        let events = self.archive.events.clone();
        let replayed = self.replay_events(&events, None)?;
        Ok(ReplayResult {
            session_id: self.archive.session.session_id.clone(),
            step_count: replayed.len(),
            replayed_events: replayed,
            branch_point: None,
        })
    }

    /// Replay events up to (not including) `branch_step`, then return the
    /// pre-branch context. The caller can inject modifications and continue
    /// from there with live LLM calls.
    pub fn branch_context(&self, branch_step: usize) -> Result<Vec<Event>, ReplayError> {
        if branch_step >= self.archive.events.len() {
            return Err(ReplayError::StepOutOfRange(branch_step));
        }
        let pre_branch = &self.archive.events[..branch_step];
        self.replay_events(pre_branch, None)
    }

    pub fn session_id(&self) -> &str {
        &self.archive.session.session_id
    }

    pub fn step_count(&self) -> usize {
        self.archive.events.len()
    }

    /// Return a summary of events without replaying them.
    pub fn event_summary(&self) -> Vec<serde_json::Value> {
        self.archive
            .events
            .iter()
            .map(|e| {
                serde_json::json!({
                    "step_index": e.step_index,
                    "event_type": e.event_type,
                    "duration_ms": e.duration_ms,
                })
            })
            .collect()
    }

    fn replay_events(
        &self,
        events: &[Event],
        _modifications: Option<&BranchModifications>,
    ) -> Result<Vec<Event>, ReplayError> {
        let mut replayed = Vec::with_capacity(events.len());

        for event in events {
            // For LLM calls, look up the cassette response
            let mut replayed_event = event.clone();

            if event.event_type == "llm_call" {
                if let Some(cassette_ref) =
                    event.payload.get("cassette_ref").and_then(|v| v.as_str())
                {
                    if let Some(cassette_data) = self.cassettes.get(cassette_ref) {
                        // Inject stored response into replayed event
                        if let serde_json::Value::Object(ref mut payload) = replayed_event.payload {
                            payload.insert("replayed_response".to_string(), cassette_data.clone());
                        }
                    }
                }
            }

            replayed.push(replayed_event);
        }

        Ok(replayed)
    }
}

//! Cassette store — maps event IDs to stored API responses for offline replay.

use std::collections::HashMap;

pub struct CassetteStore {
    cassettes: HashMap<String, serde_json::Value>,
}

impl CassetteStore {
    pub fn new(cassettes: HashMap<String, serde_json::Value>) -> Self {
        Self { cassettes }
    }

    /// Retrieve the stored response for a given cassette reference path.
    /// cassette_ref format: "cassettes/llm-0001.json"
    pub fn get(&self, cassette_ref: &str) -> Option<&serde_json::Value> {
        let id = cassette_ref
            .strip_prefix("cassettes/")
            .unwrap_or(cassette_ref)
            .strip_suffix(".json")
            .unwrap_or(cassette_ref);
        self.cassettes.get(id)
    }

    pub fn len(&self) -> usize {
        self.cassettes.len()
    }

    pub fn is_empty(&self) -> bool {
        self.cassettes.is_empty()
    }
}

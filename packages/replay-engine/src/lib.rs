//! Capsule Replay Engine
//!
//! Deterministic replay of AI agent sessions captured in the .capsule format.
//! Exposed as both a Rust library and Python bindings via PyO3.

pub mod archive;
pub mod cassette;
pub mod error;
pub mod event;
pub mod replayer;
pub mod session;

pub use replayer::Replayer;

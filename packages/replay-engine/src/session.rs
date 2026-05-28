//! Session reconstruction from an event log.

use crate::event::Event;

#[derive(Debug)]
pub struct ReplaySession {
    pub session_id: String,
    pub events: Vec<Event>,
    pub current_step: usize,
}

impl ReplaySession {
    pub fn new(session_id: String, events: Vec<Event>) -> Self {
        Self {
            session_id,
            events,
            current_step: 0,
        }
    }

    pub fn step_count(&self) -> usize {
        self.events.len()
    }

    pub fn events_from(&self, step: usize) -> &[Event] {
        if step >= self.events.len() {
            return &[];
        }
        &self.events[step..]
    }

    pub fn events_up_to(&self, step: usize) -> &[Event] {
        let end = step.min(self.events.len());
        &self.events[..end]
    }
}

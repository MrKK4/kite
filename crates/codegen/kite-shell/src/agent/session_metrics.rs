//! Session lifecycle event structs.
//!
//! The structs moved to `kite-telemetry` in the telemetry crate split.
//! This module re-exports them so the existing import path in shell keeps working.

pub(crate) use kite_telemetry::session_metrics::{
    DoomLoopDetected, DoomLoopRecovery, LongReasoningReminderTurn, SessionContextSnapshot,
    SessionStartKind, SessionStarted, TraceUploadAttempted, TraceUploadFailed, TraceUploadSkipped,
    TraceUploadSucceeded, Turn, TurnCompletedLifecycle,
};

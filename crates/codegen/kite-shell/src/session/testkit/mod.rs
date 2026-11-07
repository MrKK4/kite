//! Session synthesis for the load-perf and fork bench tests.
//!
//! This module lives in `kite-shell` (feature `test-support`) rather than `kite-test-support`.
//! Synthesis drives the real `JsonlStorageAdapter`, so the reverse dependency would be circular.

pub mod synth;

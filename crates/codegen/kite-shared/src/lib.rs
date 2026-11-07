//! Shared utilities used by both `kite-shell` and its downstream clients (e.g. `kite-pager-render`).
//! This crate sits upstream of the tools and shell; keep client utilities independent of their runtimes.

#![deny(clippy::indexing_slicing)]

pub mod clipboard;
pub mod placeholder_images;
pub mod session;
pub mod stderr;
pub mod ui_config;

#[cfg(test)]
mod placeholder_image_format_tests;

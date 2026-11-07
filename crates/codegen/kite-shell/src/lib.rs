#![allow(
    unused_imports,
    unused_variables,
    unused_mut,
    unreachable_code,
    dead_code
)]
#![warn(unreachable_pub)]
#![deny(clippy::indexing_slicing)]
#[cfg(all(test, feature = "dhat-heap"))]
#[global_allocator]
static DHAT_ALLOC: dhat::Alloc = dhat::Alloc;
pub(crate) use kite_telemetry::unified_log;
pub use kite_tracing_macros::{teprintln, timed, tprintln};
pub mod agent;
pub mod auth {
    pub use crate::agent::init::run_cli_logout;
    pub use crate::credential_factory::{
        build_bootstrap_otel_credentials, build_storage_client_for_proxy,
    };
    pub use kite_login::*;
}
pub mod builtin;
pub use kite_bundle as bundle;
pub mod claude_import;
pub mod claude_import_state;
pub mod cli_models;
pub mod config;
#[cfg(all(test, feature = "config-docs"))]
pub mod config_docs;
pub mod credential_factory;
pub use kite_shell_base::cpu_profile;
pub use kite_shell_base::env;
pub mod extensions;
pub use kite_foreign_sessions as foreign_sessions;
pub mod heap_profile;
pub use kite_http as http;
pub mod inspect;
pub mod instrumentation;
pub use kite_telemetry::instrumentation_timer;
pub mod leader;
pub use kite_cloud_config::managed_config;
pub mod mcp_doctor;
pub use kite_models as models;
pub mod plugin;
pub mod relay;
pub mod remote;
pub mod sampling;
pub mod session;
pub use kite_shell_terminal as terminal;
#[cfg(test)]
pub(crate) mod test_support;
pub mod tier;
pub mod tools;
pub mod upload;
pub mod util;
#[doc(hidden)]
pub mod waterfall;

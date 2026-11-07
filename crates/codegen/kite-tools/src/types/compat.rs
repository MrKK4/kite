//! Vendor compatibility configuration; `kite-config` owns it.

pub(crate) use kite_config::compat::INSTRUCTION_FILENAMES;
pub use kite_config::compat::{
    COMPAT_CELLS, CompatCell, CompatConfig, CompatConfigToml, CompatRemoteKey, CompatSurface,
    CompatVendor, VendorCompat, VendorCompatToml,
};

# Rust

`wrappers/rust/mostro_cli.rs` — `std::process::Command`, `serde` and `serde_json`. It
deserializes the envelope generically and lets you choose the data type per command
(`serde_json::Value` when you do not care). Compiled and run against mostro-cli 0.17.0.

Notes:

- Decimal strings map naturally to `String`; parse with `str::parse::<i64>()` when needed.
- Deserialize enums you branch on (`status`) and keep codes as `String` so a code added
  within v1 does not break deserialization.
- Check `schema_version` on the untyped `Value` first, so a future `"2"` is reported as
  incompatible instead of as a parse error.

```rust
{{#include ../../wrappers/rust/mostro_cli.rs}}
```

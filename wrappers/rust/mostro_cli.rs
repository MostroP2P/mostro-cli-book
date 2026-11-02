//! Minimal Rust wrapper for the mostro-cli JSON interface (contract "1").
//! Dependencies: serde = { version = "1", features = ["derive"] }, serde_json = "1".

use std::process::{Command, Stdio};

use serde::Deserialize;
use serde_json::Value;

#[derive(Debug, Deserialize, Clone, Copy, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Ok,
    Error,
    Uncertain,
}

#[derive(Debug, Deserialize)]
pub struct ErrorInfo {
    pub code: String,
    pub message: String,
    pub reason: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct Warning {
    pub code: String,
    pub message: String,
}

#[derive(Debug, Deserialize)]
pub struct Meta {
    pub publication: String,
    pub daemon_acceptance: String,
    pub persistence: String,
    pub snapshot: Option<Value>,
}

/// One outcome. `D` is the command's data type; use `Value` when unknown.
#[derive(Debug, Deserialize)]
pub struct Envelope<D> {
    pub schema_version: String,
    pub command: Option<String>,
    pub status: Status,
    pub data: Option<D>,
    pub error: Option<ErrorInfo>,
    pub warnings: Vec<Warning>,
    pub meta: Meta,
}

impl<D> Envelope<D> {
    pub fn code(&self) -> Option<&str> {
        self.error.as_ref().map(|e| e.code.as_str())
    }
    /// A request was or may have been published.
    pub fn node_may_have_acted(&self) -> bool {
        matches!(self.meta.publication.as_str(), "published" | "unknown")
    }
}

#[derive(Debug)]
pub enum RunError {
    /// No envelope (could not start, empty or invalid stdout). For a write,
    /// treat it like `uncertain`.
    Transport { message: String, may_have_acted: bool },
    Incompatible(String),
}

/// `mostro-cli --output json <args>`; `write` marks commands that publish a change.
pub fn run<D: for<'de> Deserialize<'de>>(
    binary: &str,
    args: &[&str],
    write: bool,
) -> Result<(Envelope<D>, i32), RunError> {
    let output = Command::new(binary)
        .args(["--output", "json"])
        .args(args)
        .stdin(Stdio::null())
        .output()
        .map_err(|e| RunError::Transport {
            message: format!("cannot start {binary}: {e}"),
            may_have_acted: false,
        })?;
    let exit = output.status.code().unwrap_or(-1);
    let text = String::from_utf8_lossy(&output.stdout);
    if text.trim().is_empty() {
        return Err(RunError::Transport {
            message: "empty stdout".into(),
            may_have_acted: write && exit == 1,
        });
    }
    // Check the version before the typed parse, so a v2 document is reported as such.
    let value: Value = serde_json::from_str(text.trim()).map_err(|e| RunError::Transport {
        message: format!("stdout is not JSON: {e}"),
        may_have_acted: write,
    })?;
    if value["schema_version"] != "1" {
        return Err(RunError::Incompatible(value["schema_version"].to_string()));
    }
    let envelope = serde_json::from_value(value).map_err(|e| RunError::Transport {
        message: format!("unexpected envelope: {e}"),
        may_have_acted: write,
    })?;
    Ok((envelope, exit))
}

#[derive(Debug, Deserialize)]
pub struct StepData {
    pub node_pubkey: String,
    pub order_id: String,
    pub result: String,
    pub next_step: Option<String>,
    pub trade_pubkey: String,
    pub next_trade_index: Option<String>,
}

fn main() {
    let binary = std::env::var("MOSTRO_CLI").unwrap_or_else(|_| "mostro-cli".into());
    match run::<Value>(&binary, &["order", "list", "--currency", "USD"], false) {
        Ok((out, exit)) => match out.status {
            Status::Ok => {
                let orders = out.data.as_ref().and_then(|d| d["orders"].as_array()).map_or(0, Vec::len);
                println!("{orders} orders (exit {exit})");
            }
            Status::Error | Status::Uncertain => {
                println!("{:?}: {} (exit {exit})", out.status, out.code().unwrap_or("?"))
            }
        },
        Err(e) => eprintln!("{e:?}"),
    }
}

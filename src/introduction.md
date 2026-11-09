# Introduction

`mostro-cli` is a command-line client for [Mostro](https://mostro.network), the peer-to-peer
Lightning ⇄ fiat exchange that runs over Nostr. Besides the human output it has always had,
a growing set of its commands can print **one machine-readable JSON document** per run:

```sh
mostro-cli --output json order list --currency USD
```

```json
{"schema_version":"1","command":"order.list","status":"ok","data":{...},"error":null,"warnings":[],"meta":{...}}
```

This book is for whoever writes the program on the other side of that pipe: a generic
wrapper, a GUI, a bot, an MCP server, or an AI agent. It explains:

- **every command** that supports JSON, with its options and what it does on the network
  and on disk;
- **every field** of every document, every status, error code, warning code and
  execution stage, and how to react to each;
- **many examples**: 153 outcomes, each in its own file with the exact command line, all
  validated against the schemas the CLI generates.

## How this relates to the Mostro protocol book

The [protocol book](https://mostro.network/protocol/) describes the Nostr messages
exchanged between a client and the Mostro daemon (`new-order`, `take-sell`, `add-invoice`,
`fiat-sent`, `release` ...). `mostro-cli` speaks that protocol for you: it holds the keys,
signs and encrypts requests, waits for the correlated reply and stores the order locally.
What you see is the **result**, already decoded, typed and checked.

| Protocol book | This book |
| --- | --- |
| Nostr events, NIP-44 kind-14 messages | Process arguments, stdout, exit code |
| `action` + `payload` of a message | `command` + `data` of an outcome |
| `cant-do` with a reason | `error.code = "node_refused"` + `error.reason` |
| Keys, trade indexes, signatures | Handled by the CLI; only public keys and indexes are reported |

## The contract in five lines

1. Pass `--output json`; write commands also need `--yes`. Stdin is read only for `--invoice -`.
2. Stdout holds exactly one JSON object and a newline. Diagnostics go to stderr.
3. Branch on `status` (`ok`, `error`, `uncertain`), then on `error.code`. Never on `message`.
4. `uncertain` means *the node may have acted*. Do not retry blindly; check first.
5. Every key is always present; empty values are `null` or `[]`, never omitted.

## Versions

| Item | Value |
| --- | --- |
| JSON contract | `schema_version` `"1"` |
| Documented executable | mostro-cli 0.17.0 (release `v0.17.0`, 2026-11-07) |
| Schema dialect | JSON Schema Draft 2020-12 |
| Node protocol | Mostro protocol v2 (NIP-44 kind-14); v1 nodes are refused |

The contract version is independent of the executable version. Within version 1 only
optional additions are allowed (a new command, a new code scoped to a new command). A
renamed command, a changed type or a changed meaning requires `schema_version` `"2"`.
Reject documents whose `schema_version` you do not know.

> mostro-cli 0.17.0 is the first release with the JSON interface; 0.16.3 and earlier have
> none. Check `mostro-cli --output json schema` on your binary.

> After 0.17.0, not yet released: the commands mine the proof of work the node advertises
> (up to 20 bits) instead of failing with `pow_required`, which now carries `error.required`
> and `error.configured` ([Proof of work](errors.md#proof-of-work)). With 0.17.0, set `--pow` /
> `POW` to the node's value yourself.

> After 0.17.0, not yet released: the JSON-capable commands that talk to the node also read
> the node settings from `$MCLI_DIR/config` ([The config file](getting_started.md#the-config-file);
> [mostro-cli#248](https://github.com/MostroP2P/mostro-cli/pull/248)).
> With 0.17.0, pass them as options or environment variables.

> After 0.17.0, not yet released: the human-only commands, except the gRPC operator
> commands, read the config file too, with the same precedence
> ([Human-only commands](commands/legacy.md);
> [mostro-cli#249](https://github.com/MostroP2P/mostro-cli/pull/249)).
> With 0.17.0, pass their settings as options or environment variables.

> After 0.17.0, not yet released: [`config set`](commands/config_set.md) writes one node
> setting to the config file. It brings the error code `configuration_unwritable`, which only
> it emits, and the discovery keyword `x-positional` for its two positional arguments
> ([mostro-cli#250](https://github.com/MostroP2P/mostro-cli/pull/250)).
> With 0.17.0, pass the settings as options or environment variables.

> After 0.17.0, not yet released: [`config show`](commands/config_show.md) reports the config
> file's path and the node settings stored in it, read-only, and the missing-setting messages
> of the human-only commands name `config set` and `config show`
> ([mostro-cli#251](https://github.com/MostroP2P/mostro-cli/pull/251)).
> This completes the config file of
> [mostro-cli#244](https://github.com/MostroP2P/mostro-cli/issues/244).
> With 0.17.0, pass the settings as options or environment variables.

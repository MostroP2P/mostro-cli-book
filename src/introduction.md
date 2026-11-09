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
- **many examples**: 152 outcomes, each in its own file with the exact command line, all
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

> After 0.17.0, not yet released: `order chat --order <id> [--message <text>]` reads the
> peer chat of an order you hold and sends one message without the counterparty's key, also
> in JSON (`order.chat`, `--yes` with `--message`; [`order chat`](commands/order_chat.md);
> [mostro-cli#255](https://github.com/MostroP2P/mostro-cli/pull/255), [mostro-cli#256](https://github.com/MostroP2P/mostro-cli/pull/256)).
> With 0.17.0, pass the counterparty's key to `getdmuser -p` and `dmtouser -p`.

> After 0.17.0, not yet released: `order watch --order <id>` follows an order you hold
> until its trade ends, the node's messages and the peer chat, replayed then live. In JSON
> (`order.watch`) each call returns one document at the first new records, with a cursor for
> `--after` ([`order watch`](commands/order_watch.md);
> [mostro-cli#261](https://github.com/MostroP2P/mostro-cli/pull/261), CLI_PR_order_watch_json).
> With 0.17.0, poll `message list` and `getdmuser`.

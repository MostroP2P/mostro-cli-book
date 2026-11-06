# identity show

| | |
| --- | --- |
| `command` | `identity.show` |
| Kind | Local read |
| Needs | An existing identity. No `MOSTRO_PUBKEY`, `RELAYS`, stdin or `--yes` |
| Publishes | Nothing; contacts no relay or node |
| Local write | None: no file, directory or SQLite sidecar is created or changed |
| Statuses | `ok`, `error` |
| Schemas | `schemas/identity.show.input.json`, `schemas/identity.show.output.json` |

Reports the identity public key of the local store and the last trade index it recorded.
Use it to check that a store exists and which identity it holds.

## Invocation

```text
mostro-cli --output json identity show
```

## Input

None. Any option of its own is `invalid_arguments` (exit 2). Root options such as
`--mostro-pubkey` or `--relays` are accepted and ignored.

## Behavior

Opens the store (`MCLI_DIR`, else `.mcli` in the home directory) read-only and reads the
user row. It creates nothing, even when the store is missing or uses a WAL journal. The
mnemonic and private keys are never shown.

## Success data: `IdentityShowData`

| Field | Type | Meaning |
| --- | --- | --- |
| `identity_pubkey` | hex64 | The identity public key of the store |
| `last_trade_index` | integer, `0`..`2147483647` | The last trade index recorded in the store; `0` before the first order or take. The next order or take uses the one after it |

`last_trade_index` is a **JSON integer**, unlike the decimal-string trade indexes of the
other outcomes. It is bounded to `0`..`2147483647` (the last normal BIP32 index), so every
JSON reader decodes it exactly.

## Outcomes

| Case | status | code | Stages |
| --- | --- | --- | --- |
| Identity read | `ok` | | `not_applicable` ×3 |
| No data directory, no `mcli.db`, or no user row | `error` | `identity_missing` | `not_applicable` ×3 |
| The store cannot be read, holds no usable mnemonic, has a `-wal` file without its `-shm` file, or records an index out of range | `error` | `identity_unreadable` | `not_applicable` ×3 |
| An option was given | `error` | `invalid_arguments` (exit 2) | `not_applicable` ×3 |

## Errors

`invalid_arguments`, `identity_missing`, `identity_unreadable`, `internal_error`.
After `identity_missing`, create a store with [identity init](identity_init.md).

## Warnings

None. The schema's shared `WarningCode` list names `invalid_event_timestamp` and
`cleanup_incomplete`, but this command emits no warning.

## Examples

{{#include ../../generated/identity_show.md}}

## Next

[order mine](order_mine.md) lists the orders of the same store.

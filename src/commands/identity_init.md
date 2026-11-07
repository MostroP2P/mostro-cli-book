# identity init

| | |
| --- | --- |
| `command` | `identity.init` |
| Kind | Local write |
| Needs | `MCLI_DIR` or a home directory. No `MOSTRO_PUBKEY`, `RELAYS`, stdin or `--yes` |
| Publishes | Nothing; contacts no relay or node |
| Local write | Creates the data directory and `mcli.db` with a fresh mnemonic; never changes an existing store |
| Statuses | `ok`, `error` |
| Schemas | `schemas/identity.init.input.json`, `schemas/identity.init.output.json` |

Creates the local identity store that every signing command needs. It is the only JSON
command that creates an identity: the others fail with `identity_missing` when there is
none.

## Invocation

```text
mostro-cli --output json identity init
```

It does what the first run of a legacy command does (the two share one implementation),
without needing the node's configuration or a connection.

## Input

None. Any option of its own is `invalid_arguments` (exit 2). Root options such as
`--mostro-pubkey` or `--relays` are accepted and ignored.

## Behavior

1. Uses `MCLI_DIR`, else `.mcli` in the home directory. Creates that directory owner-only
   (`0700` on Unix, one level deep); an existing directory is tightened to owner-only.
2. If `mcli.db` or one of its SQLite companion files (`mcli.db-journal`, `mcli.db-wal`,
   `mcli.db-shm`) already exists, it changes nothing and fails with `identity_exists`. It
   never deletes or repairs a store: move the old files away first.
3. Creates `mcli.db` owner-only (`0600` on Unix) with the same tables as the legacy first
   run and one user row holding a fresh 12-word mnemonic and no trade index.
4. If the file was created but could not be completed, it is removed again
   (`persistence: failed`).

Two runs at the same time create one store; the other reports `identity_exists`.

The mnemonic and every private key stay in `mcli.db`. No mode, stream or error shows
them, and there is no option to reveal them. Back the file up yourself.

## Success data: `IdentityInitData`

| Field | Type | Meaning |
| --- | --- | --- |
| `identity_pubkey` | hex64 | The identity public key of the new store (index 0 of the new mnemonic) |

## Outcomes

| Case | status | code | Stages (publication / daemon / persistence) |
| --- | --- | --- | --- |
| Store created | `ok` | | not_applicable / not_applicable / applied |
| `mcli.db` or a companion file exists | `error` | `identity_exists` | not_applicable / not_applicable / not_attempted |
| No data directory can be determined, or the directory or file cannot be created | `error` | `store_unwritable` | not_applicable / not_applicable / not_attempted |
| The file was created but not completed (removed again) | `error` | `store_unwritable` | not_applicable / not_applicable / failed |
| An option was given | `error` | `invalid_arguments` (exit 2) | not_applicable ×3 |

## Errors

`invalid_arguments`, `identity_exists`, `store_unwritable`, `internal_error`. Nothing
was published in any case. After `identity_exists`, use [identity show](identity_show.md)
to read the existing identity.

## Warnings

None. The schema's shared `WarningCode` list names `invalid_event_timestamp` and
`cleanup_incomplete`, but this command emits no warning.

## Examples

{{#include ../../generated/identity_init.md}}

## Next

[identity show](identity_show.md) reads the key back; then [order list](order_list.md) and
a first [order new](order_new.md) or take.

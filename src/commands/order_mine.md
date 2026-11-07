# order mine

| | |
| --- | --- |
| `command` | `order.mine` |
| Kind | Local read |
| Needs | An existing identity. No `MOSTRO_PUBKEY`, `RELAYS`, stdin or `--yes` |
| Publishes | Nothing; contacts no relay or node |
| Local write | None |
| Statuses | `ok`, `error` |
| Schemas | `schemas/order.mine.input.json`, `schemas/order.mine.output.json` |

Lists the orders of the local store: the ones you made, took, or adopted with
[order sync](order_sync.md) (range children included), with the trade index and key of
each. It answers "which orders does this store know?" without asking the node.

## Invocation

```text
mostro-cli --output json order mine
```

## Input

None. Any option of its own is `invalid_arguments` (exit 2). Root options such as
`--mostro-pubkey` or `--relays` are accepted and ignored.

## Behavior

1. Opens the store read-only (`MCLI_DIR`, else `.mcli` in the home directory) and reads
   every row of its orders table.
2. The store keeps each order's trade key but not its index. The index is found by
   deriving the keys of the recorded indexes, newest first, as
   [message list](message_list.md) does (**the newest 200**), and matching them.
3. Sorts newest first: by trade index, highest first (each order or take reserves the
   next index). Rows whose index is unknown come after, by creation time, newest first,
   then by id.

`status` is the **local** status, as the store recorded it when this CLI last changed it.
It is not refreshed from the node; ask [order info](order_info.md) for the node's view.

## Success data: `OrderMineData`

| Field | Type | Meaning |
| --- | --- | --- |
| `orders` | array of `MineOrder` | The rows of the store, newest first; empty when there are none |

### MineOrder

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | uuid | Order id |
| `side` | `buy` \| `sell` | Side of the order |
| `status` | status | The local status (see above) |
| `trade_index` | decimal string or null | Index of the order's trade key; `null` when the key is not among the newest 200 derived or the row has no key |
| `trade_pubkey` | hex64 or null | Public key of the order's trade key; `null` when the row has no usable key |

No private key, mnemonic or invoice is included.

## Outcomes

| Case | status | code | Stages |
| --- | --- | --- | --- |
| Rows read (possibly none) | `ok` | | `not_applicable` ×3 |
| No data directory, no `mcli.db`, or no user row | `error` | `identity_missing` | `not_applicable` ×3 |
| The store, or a row's id, side or status, cannot be read | `error` | `store_unreadable` | `not_applicable` ×3 |
| An option was given | `error` | `invalid_arguments` (exit 2) | `not_applicable` ×3 |

## Errors

`invalid_arguments`, `identity_missing`, `store_unreadable`, `internal_error`. Nothing
is created or changed in any case.

## Warnings

`trade_keys_limited` when a row has a key whose index is unknown and older keys than the
newest 200 were not derived. The schema also lists `invalid_event_timestamp` and
`cleanup_incomplete`, which this command does not emit.

## Examples

{{#include ../../generated/order_mine.md}}

## Next

[order info](order_info.md) for the node's current state of these orders;
[message list](message_list.md) for what the node sent to their trade keys.

# Decision table

One table to map any outcome to an action. Evaluate top to bottom; the first match wins.

| # | Condition | Class | Retry? | Action |
| --- | --- | --- | --- | --- |
| 1 | stdout empty or not one JSON object | `transport` | read: yes · write: **no** | Treat a write as uncertain; log stderr |
| 2 | `schema_version != "1"` | `incompatible` | no | Stop; upgrade the wrapper |
| 3 | `status == "ok"` and `warnings == []` | `ok` | — | Use `data` |
| 4 | `status == "ok"` with warnings | `ok_with_warnings` | — | Use `data`; handle warnings (below) |
| 5 | `status == "uncertain"` | `uncertain` | **no** | [Check first](../flows/uncertain.md) |
| 6 | `error.code == "invalid_arguments"` | `caller_bug` | no | Fix the call (missing `--yes`? bad UUID? window range?) |
| 7 | `error.code == "output_not_supported"` | `unsupported` | no | Command is human-only |
| 8 | `configuration_missing`, `configuration_invalid` | `config` | after fixing | Ask for node key / relays. They come from the options, the environment or `$MCLI_DIR/config`; a bad line in that file, or a file that cannot be read, is `configuration_invalid` too, and the stderr `hint:` names the file and the problem. Run `config show` to see what the file holds |
| 9 | `configuration_unwritable` | `config` | after fixing | Only `config set`: the config file or the data directory cannot be written. The old file is intact; make `MCLI_DIR` (else `~/.mcli`) a directory you own on a disk with free space |
| 10 | `identity_missing`, `identity_unreadable` | `identity` | after fixing | Create or restore the identity; check `MCLI_DIR` |
| 11 | `store_unwritable`, `store_unreadable` | `storage` | after fixing | Disk, permissions, locked database |
| 12 | `order_unknown` | `not_local` | after `order sync` | Wrong id, other data directory, or a range child: run `order sync` |
| 13 | `protocol_unsupported` | `node_incompatible` | no | The node runs protocol v1 |
| 14 | `pow_required` | `config` | after setting `--pow` to `error.required` | The node asks for more than the 20 bits the program mines on its own; mining it can take a long time, so let the human decide |
| 15 | `node_refused` | `refused` | depends on `reason` | Show `reason`; `too_many_requests` → back off; status reasons → refresh with `order info` |
| 16 | `relay_connection_failed`, `relay_read_failed`, `read_timeout`, `request_rejected`, `reply_timeout`, `reply_malformed` (as `error`) | `transient` | yes, with backoff | Nothing happened, or it was a read |
| 17 | `read_limit_exceeded` | `too_much` | after narrowing | Smaller `--since`, or `--order` |
| 18 | `order_declined` | `declined` | — | Only from the human prompt |
| 19 | `internal_error` | `bug` | maybe once | Report with the command (without secrets) |

## Warnings

| Warning | Action |
| --- | --- |
| `local_status_stale` | Step succeeded. Do not resend. Local status lags; trust `order info` |
| `orders_not_returned` | Some ids unknown or not yours: see `data.not_returned` |
| `trade_keys_limited` | Old keys skipped; use `message list --order` for old orders |
| `invalid_event_timestamp`, `invalid_order_timestamp` | Display "invalid date"; use `_unix` fields |
| `cleanup_incomplete` | Ignore |

## next_step dispatch

| Source | `next_step` | Action |
| --- | --- | --- |
| `order.new` | `wait_for_taker` | Poll `message list` |
| `order.new`, `order.take-*`, `message.list` | `pay_bond_invoice` | Pay the bond invoice (`data.payment_request` or payload `invoice`) |
| `order.take-buy`, `message.list` | `pay_hold_invoice` | Pay the hold invoice |
| `order.take-sell`, `message.list` | `add_invoice` | `order add-invoice` |
| `order.take-sell` | `wait_for_seller_payment` | Poll |
| `message.list` | `add_bond_invoice` | `bond add-invoice` |
| `order.fiat-sent` | `wait_for_release` | Poll |
| `order.cancel` | `wait_for_peer_cancel` | Poll; the peer must cancel too |
| `order.release` | `sync_child_order` | `order sync` |

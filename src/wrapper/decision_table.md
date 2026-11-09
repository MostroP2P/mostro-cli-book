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
| 8 | `configuration_missing`, `configuration_invalid` | `config` | after fixing | Ask for node key / relays |
| 9 | `identity_missing`, `identity_unreadable` | `identity` | after fixing | Create or restore the identity; check `MCLI_DIR` |
| 10 | `store_unwritable`, `store_unreadable` | `storage` | after fixing | Disk, permissions, locked database |
| 11 | `order_unknown` | `not_local` | after `order sync` | Wrong id, other data directory, or a range child: run `order sync` |
| 12 | `protocol_unsupported` | `node_incompatible` | no | The node runs protocol v1 |
| 13 | `pow_required` | `config` | after setting `--pow` to `error.required` | The node asks for more than the 20 bits the program mines on its own; mining it can take a long time, so let the human decide |
| 14 | `node_refused` | `refused` | depends on `reason` | Show `reason`; `too_many_requests` → back off; status reasons → refresh with `order info` |
| 15 | `relay_connection_failed`, `relay_read_failed`, `read_timeout`, `request_rejected`, `reply_timeout`, `reply_malformed` (as `error`) | `transient` | yes, with backoff | Nothing happened, or it was a read |
| 16 | `read_limit_exceeded` | `too_much` | after narrowing | Smaller `--since`, or `--order` |
| 17 | `order_declined` | `declined` | — | Only from the human prompt |
| 18 | `internal_error` | `bug` | maybe once | Report with the command (without secrets) |
| 19 | `counterparty_unknown` | `not_yet` | after the escrow is locked | `order chat` cannot name the counterparty yet; with its key, `getdmuser -p` / `dmtouser -p` |

## Warnings

| Warning | Action |
| --- | --- |
| `local_status_stale` | Step succeeded. Do not resend. Local status lags; trust `order info` |
| `orders_not_returned` | Some ids unknown or not yours: see `data.not_returned` |
| `trade_keys_limited` | Old keys skipped; use `message list --order` for old orders |
| `invalid_event_timestamp`, `invalid_order_timestamp` | Display "invalid date"; use `_unix` fields |
| `cleanup_incomplete` | Ignore |

## next_step dispatch

For `message.list` and `order.watch`, dispatch on the `next_step` of each entry in `data.messages`.
A record's `next_step` is what its message asked when the node sent it: check `order info`
before acting, and act on each `event_id` once.

| Source | `next_step` | Action |
| --- | --- | --- |
| `order.new` | `wait_for_taker` | `order watch --order <id> --after <cursor>` |
| `order.new`, `order.take-*`, `message.list`, `order.watch` | `pay_bond_invoice` | Pay the bond invoice (`data.payment_request` or payload `invoice`) |
| `order.take-buy`, `message.list`, `order.watch` | `pay_hold_invoice` | Pay the hold invoice |
| `order.take-sell`, `message.list`, `order.watch` | `add_invoice` | `order add-invoice` (in a record also from `payment-failed` with `payment_attempts` `"0"`) |
| `order.take-sell` | `wait_for_seller_payment` | `order watch --order <id> --after <cursor>` |
| `message.list`, `order.watch` | `add_bond_invoice` | `bond add-invoice` |
| `order.fiat-sent` | `wait_for_release` | `order watch --order <id> --after <cursor>` |
| `order.cancel` | `wait_for_peer_cancel` | `order watch --order <id> --after <cursor>`; the peer must cancel too |
| `order.release` | `sync_child_order` | `order sync` |
| `message.list`, `order.watch` | a value you do not know | Treat as `null`: do nothing for it (the enum is open within v1) |
| `message.list`, `order.watch` | `null` on `payment-failed` | Wait: the node retries the payout and sends `add-invoice` only if every attempt fails |

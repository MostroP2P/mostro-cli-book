# Migration from old spellings

The JSON-capable commands replaced older spellings **without aliases**. An old spelling
fails like an unknown command: `invalid_arguments`, exit 2, `command: null`.

| Before | Now |
| --- | --- |
| `--mostropubkey KEY` (root) | `--mostro-pubkey KEY` |
| `listorders --kind buy\|sell ...` | `order list --side buy\|sell [--currency CUR] [--status STATUS]` |
| `ordersinfo -o ID -o ID2` / `--orderids` | `order info --order ID --order ID2` |
| `neworder -k KIND -c CUR -f AMOUNT -m METHOD [-a SATS] [-p PREMIUM] [-i INVOICE] [-e DAYS]` | `order new --side KIND --currency CUR --fiat-amount AMOUNT --payment-method METHOD [--sats SATS] [--premium PREMIUM] [--invoice INVOICE] [--expiration-days DAYS] --yes` |
| `neworder ... -f 100-200` (range) | `order new ... --fiat-amount 100 --fiat-amount-max 200` |
| `takesell -o ID [-i INVOICE] [-a AMOUNT]` | `order take-sell --order ID [--invoice INVOICE] [--amount AMOUNT] --yes` |
| `takebuy -o ID [-a AMOUNT]` | `order take-buy --order ID [--amount AMOUNT] --yes` |
| `addinvoice -o ID -i INVOICE` | `order add-invoice --order ID --invoice INVOICE --yes` |
| `addbondinvoice -o ID -i INVOICE` | `bond add-invoice --order ID --invoice INVOICE --yes` |
| `fiatsent -o ID` | `order fiat-sent --order ID --yes` |
| `release -o ID` | `order release --order ID --yes` |
| `cancel -o ID` | `order cancel --order ID --yes` |
| `getdm ...` | `message list [--since MINUTES] [--order ID]` |
| `dispute -o ID` / `--orderid` | `dispute open --order ID --yes` |
| `rate -o ID -r RATING` | `order rate --order ID --rating RATING --yes` |
| `getdmuser -p KEY -o ID [--since MINUTES]` | `order chat --order ID [--since MINUTES]` (human output for now; `getdmuser` stays, see below) |
| `dmtouser -p KEY -o ID -m TEXT` | `order chat --order ID --message TEXT` (human output for now; `dmtouser` stays, see below) |
| — | `order sync [--since MINUTES]` (new) |
| — | `order mine` (new) |
| — | `identity init`, `identity show` (new) |
| — | `schema` (new) |

Behaviour changes that matter to wrappers:

- JSON commands other than `identity init` **never create an identity**. A command that
  needs one returns `identity_missing` when none exists; `schema` and `order list` need
  none. Create one explicitly with `identity init` (a legacy command run first still
  creates it too).
- `order info` waits for the reply to **its** request (not the first message), and an empty
  answer is a success with `not_returned`.
- Writes require `--yes` in JSON mode; no stdin prompt is ever shown.
- `message list` is read-only and shows only messages authored by the node.
- After 0.17.0, not yet released: `order chat` finds the counterparty's key itself, so for
  an order in the local store it replaces `getdmuser` and `dmtouser`. Its `--since` defaults
  to 10080 minutes instead of 30. Both legacy commands stay, unchanged: like `order chat`
  they need the order's row, and they are the fallback when it cannot find the counterparty
  (`counterparty_unknown`) and you know the key. `order chat` has human output only for now
  (`output_not_supported` in JSON); see
  [Human-only commands](../commands/legacy.md#order-chat).
- `--kind` became `--side`; short option letters of the old commands are gone.
- New options with no old spelling: `order new --expires-in SECONDS`, `--invoice -` (the
  invoice read from standard input) and the global `--reply-timeout SECONDS`; see
  [Invoking the CLI](../invocation.md).

The short root options (`-m`, `-r`, `-p`, `-s`, `-t`, `-v`) still exist.

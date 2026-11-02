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
| — | `order sync [--since MINUTES]` (new) |
| — | `schema` (new) |

Behaviour changes that matter to wrappers:

- JSON commands **never create an identity**; `identity_missing` instead.
- `order info` waits for the reply to **its** request (not the first message), and an empty
  answer is a success with `not_returned`.
- Writes require `--yes` in JSON mode; no stdin prompt is ever shown.
- `message list` is read-only and shows only messages authored by the node.
- `--kind` became `--side`; short option letters of the old commands are gone.

The short root options (`-m`, `-r`, `-p`, `-s`, `-t`, `-v`) still exist.

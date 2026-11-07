# Node actions in messages

`message list` reports each node message's protocol `action` verbatim (kebab-case). The
full list is in the [protocol book](https://mostro.network/protocol/actions.html); these are
the ones this book refers to, with how the CLI presents them.

| `action` | Sent when | `next_step` | Payload `kind` |
| --- | --- | --- | --- |
| `new-order` | An order was created for you; for range orders, the child order announced to your next key | — | `order` |
| `pay-bond-invoice` | A bonded node wants your bond | `pay_bond_invoice` | `payment_request` |
| `pay-invoice` | You are the seller: lock the sats | `pay_hold_invoice` | `payment_request` |
| `add-invoice` | You are the buyer: the node needs your invoice | `add_invoice` | `order` |
| `add-bond-invoice` | A counterparty bond was slashed; send a payout invoice | `add_bond_invoice` | `bond_payout_request` |
| `bond-invoice-accepted` | Your payout invoice was accepted | — | `order` (amount: your share) |
| `bond-payout-completed` | Your share of a slashed bond was paid | — | `order` (amount: your share) |
| `bond-slashed` | A bond was slashed | — | `order` (amount: the slashed bond) |
| `waiting-seller-to-pay` | Your invoice is in; the seller has to pay | — | `none` |
| `hold-invoice-payment-accepted` | The seller locked the sats; the trade is active | — | (varies) |
| `fiat-sent-ok` | The buyer's `fiat-sent` was accepted | — | `peer` |
| `hold-invoice-payment-settled`, `released` | The seller's release went through | — | (varies) |
| `canceled` | The order was canceled | — | `none` |
| `cooperative-cancel-initiated-by-you` | You started a cooperative cancel | — | (varies) |
| `cooperative-cancel-accepted` | The cooperative cancel completed | — | (varies) |
| `invoice-updated` | A replacement buyer invoice was stored | — | (varies) |
| `rate-received` | Your rating was recorded | — | `other` (`rating_user`) |
| `cant-do` | The node refused something | — | `cant_do` |

Only the four `next_step` values ask you to act. Everything else is information; use
`order info` for the authoritative status.

The same action names appear in replies to the write commands, where the CLI maps them to
`result` values (see [order fiat-sent](../commands/order_fiat_sent.md#success-data-stepdata)
and [order add-invoice](../commands/order_add_invoice.md#success-data-orderinvoicedata)).

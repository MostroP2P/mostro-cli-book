# Cancelling

```sh
mostro-cli --output json order cancel --order <id> --yes
```

What happens depends on the order's state and who you are; the node decides and
`data.result` tells you.

| `result` | Situation | Then |
| --- | --- | --- |
| `canceled` | Typically your own order still `pending`, or a trade the node can cancel outright | Done. Local status `canceled` |
| `cancel_requested` | A trade in progress: you asked for a **cooperative** cancel | `next_step: wait_for_peer_cancel`. The counterparty must run `order cancel` too |
| `cancel_accepted` | The counterparty had already requested it | Done. Local status `cooperatively-canceled`; the hold invoice is returned to the seller |

## Cooperative cancel between two programs

```text
A: order cancel --order X  → ok, result cancel_requested, next_step wait_for_peer_cancel
B: (sees a message from the node about the request; order info shows the trade still running)
B: order cancel --order X  → ok, result cancel_accepted
```

If the counterparty does not agree, the trade continues; a dispute
([`dispute open`](../commands/dispute_open.md)) is the escalation path.

## Refusals

`node_refused` with reasons such as `order_already_canceled`, `invalid_order_status` (the
order is in a status where the node does not allow this cancel) or `invalid_peer`.

## Examples

See [order cancel](../commands/order_cancel.md#examples).

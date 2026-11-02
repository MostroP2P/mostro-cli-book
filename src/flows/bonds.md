# Bonds

Some Mostro nodes require **bonds**: a small Lightning payment that a maker and/or taker
locks to discourage abandoning a trade. A bond that is not forfeited is returned; a
**slashed** bond is (partly) paid to the counterparty.

> The JSON commands handle bonded nodes according to the contract, but the CLI's own
> notes say the bonded-node cases were verified against a scripted node and only partly on
> a real one. Test against your node before relying on them.

## Maker bond

```sh
mostro-cli --output json order new ... --yes
```

`data.next_step: "pay_bond_invoice"`, `data.payment_request` holds the bond invoice and the
order is parked (status `pending` or `waiting-maker-bond`). Pay it; the node then publishes
the order. A `message list` record with `next_step: pay_bond_invoice` carries the same
invoice.

## Taker bond

`order take-sell` / `order take-buy` may answer `next_step: "pay_bond_invoice"` with the
invoice in `data.payment_request`. Pay it; the node continues the take (for take-buy, the
hold invoice then arrives as a message with `next_step: pay_hold_invoice`).

## Receiving a slashed bond

When your counterparty's bond is slashed, the node asks you for a payout invoice:

```json
{"action": "add-bond-invoice", "next_step": "add_bond_invoice",
 "payload": {"kind": "bond_payout_request", "order": {...}, "slashed_at": "...", "slashed_at_unix": "..."}}
```

Create an invoice for exactly your share and send it:

```sh
mostro-cli --output json bond add-invoice --order <id> --invoice <bolt11> --yes
```

`data.result: "invoice_accepted"`; `data.counterparty_share_sats` reports the amount when
the node gave it. See [bond add-invoice](../commands/bond_add_invoice.md).

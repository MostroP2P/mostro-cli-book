# Selling as a maker

You publish a **sell** order: you give sats and receive fiat. The node holds your sats in a
Lightning **hold invoice** until you release them.

## How to observe a trade

Two read commands tell you where a trade is:

- [`message list`](../commands/message_list.md) — what the node told you, with `next_step`
  when it asks for something. Poll it; deduplicate by `event_id`. Or wait with
  [`order watch`](../commands/order_watch.md), which returns at the first new message.
- [`order info`](../commands/order_info.md) — the order's current `status`, authoritative.

A robust program drives the trade from **`order info` status** and uses `message list` to
pick up invoices to pay (`payment_request` payloads) and requests (`next_step`).

## Steps

```text
order new --side sell ──► pending ──(buyer takes)──► waiting-payment ──(you pay hold invoice)──►
waiting-buyer-invoice / active ──(buyer: fiat-sent)──► fiat-sent ──(you: release)──► settled-hold-invoice ──► success
```

1. **Create the order.**

   ```sh
   mostro-cli --output json order new --side sell --currency EUR --fiat-amount 100 \
     --payment-method "SEPA" --premium 1 --yes
   ```

   `data.next_step` is `wait_for_taker` (on a bonded node, `pay_bond_invoice` first: pay
   `data.payment_request`). Keep `data.order.id`.

2. **Wait for a taker.** Wait with `order watch --order <id> --after <cursor>`. When a buyer takes the order the
   node sends a message with `next_step: pay_hold_invoice` and a `payment_request` payload:

   ```json
   {"action": "pay-invoice", "next_step": "pay_hold_invoice",
    "payload": {"kind": "payment_request", "invoice": "lnbc...", "amount": "100000", "order": {...}}}
   ```

3. **Lock the sats** by paying `payload.invoice` with your Lightning wallet. The payment
   stays pending (held); it is not lost if the trade is canceled.

4. **Wait for the fiat.** The buyer provides an invoice (if needed) and pays you in fiat
   through the payment method. When they report it, the order status becomes `fiat-sent`
   and you receive a `fiat-sent-ok` message (payload `peer`). Agree on the payment details
   with the buyer in [`order chat`](../commands/order_chat.md).

5. **Check your bank account.** `fiat-sent` is the buyer's claim, not a proof. Only when the
   money is really there:

   ```sh
   mostro-cli --output json order release --order <id> --yes
   ```

   `data.result` is `released`. This is irreversible.

6. **Rate** the buyer: [`order rate`](../commands/order_rate.md).

## If something goes wrong

| Situation | What to do |
| --- | --- |
| Nobody takes the order | `order cancel --order <id> --yes` → `canceled` |
| The buyer does not pay | Cancel cooperatively or open a dispute ([`dispute open`](../commands/dispute_open.md)) |
| `release` returned `uncertain` | `order info --order <id>`; see [Recovering](uncertain.md) |
| It was a range order | After `release`, `next_step: sync_child_order`: see [Range orders](range_orders.md) |

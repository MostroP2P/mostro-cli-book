# Buying as a maker

You publish a **buy** order: you pay fiat and receive sats.

1. **Create the order**, optionally with your invoice or Lightning address:

   ```sh
   mostro-cli --output json order new --side buy --currency USD --fiat-amount 50 \
     --payment-method "Zelle" --invoice you@wallet.example --yes
   ```

   `next_step: wait_for_taker` (or `pay_bond_invoice` on a bonded node).

2. **Wait for a seller.** A seller takes it with `order take-buy` and pays the hold invoice.
   Wait with `order watch --order <id> --after <cursor>`.

3. **Give an invoice if asked.** Without `--invoice` at creation, the node sends a message
   with `next_step: add_invoice` (payload `order`, with the computed `sats_amount`):

   ```sh
   mostro-cli --output json order add-invoice --order <id> --invoice <bolt11 for sats_amount> --yes
   ```

4. **When the order is `active`**, pay the fiat and run
   `order fiat-sent --order <id> --yes` → `wait_for_release`. The node tells you with a
   `hold-invoice-payment-accepted` message that has `next_step: fiat_sent` (after 0.17.0, not yet released; 0.17.0 reports it with `next_step: null`).
   Agree on the payment details with the seller in [`order chat`](../commands/order_chat.md).

5. **Wait for the release** (`settled-hold-invoice`, then `success`). If the payment to
   your invoice fails, a `payment-failed` record (payload
   [`payment_failed`](../commands/message_list.md#payment_failed)) says how many more times the
   node will retry, with `next_step: null`; it asks for a new invoice (`next_step: add_invoice`)
   only if every retry fails, or at once when `payment_attempts` is `"0"`.

6. **Rate** the seller: right after `purchase-completed` the node sends a `rate` message with
   `next_step: rate` (after 0.17.0, not yet released; 0.17.0 reports it with `next_step: null`); run [`order rate`](../commands/order_rate.md).

For a **buy range order**, `fiat-sent` is the step that carries your next trade key; the
child order arrives when the seller releases. See [Range orders](range_orders.md).

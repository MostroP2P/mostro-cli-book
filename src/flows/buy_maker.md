# Buying as a maker

You publish a **buy** order: you pay fiat and receive sats.

1. **Create the order**, optionally with your invoice or Lightning address:

   ```sh
   mostro-cli --output json order new --side buy --currency USD --fiat-amount 50 \
     --payment-method "Zelle" --invoice you@wallet.example --yes
   ```

   `next_step: wait_for_taker` (or `pay_bond_invoice` on a bonded node).

2. **Wait for a seller.** A seller takes it with `order take-buy` and pays the hold invoice.
   Poll `message list --order <id>`.

3. **Give an invoice if asked.** Without `--invoice` at creation, the node sends a message
   with `next_step: add_invoice` (payload `order`, with the computed `sats_amount`):

   ```sh
   mostro-cli --output json order add-invoice --order <id> --invoice <bolt11 for sats_amount> --yes
   ```

4. **When the order is `active`**, pay the fiat and run
   `order fiat-sent --order <id> --yes` → `wait_for_release`.

5. **Wait for the release** (`settled-hold-invoice`, then `success`).

For a **buy range order**, `fiat-sent` is the step that carries your next trade key; the
child order arrives when the seller releases. See [Range orders](range_orders.md).

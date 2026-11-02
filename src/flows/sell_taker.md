# Selling as a taker

You take someone's **buy** order: you lock sats, receive fiat, then release.

1. **Find an order**: `order list --side buy --currency USD`.

2. **Take it**:

   ```sh
   mostro-cli --output json order take-buy --order <id> --yes        # --amount <fiat> for a range
   ```

3. **Follow `data.next_step`:**

   | `next_step` | Do |
   | --- | --- |
   | `pay_hold_invoice` | Pay `data.payment_request` (the hold invoice) with your wallet |
   | `pay_bond_invoice` | Pay `data.payment_request` (taker bond); the hold invoice then comes as a message with `next_step: pay_hold_invoice` |

4. **Wait for the buyer's fiat.** The buyer adds an invoice if needed, pays the fiat and
   runs `fiat-sent`; you see the order go to `fiat-sent` (`order info`) and a `fiat-sent-ok`
   message.

5. **Check that the money arrived**, then release (irreversible):

   ```sh
   mostro-cli --output json order release --order <id> --yes
   ```

## If something goes wrong

| Situation | What to do |
| --- | --- |
| The buyer never sends fiat | Cancel cooperatively (`order cancel`) or open a dispute |
| You did not pay the hold invoice | Nothing of yours is locked; the node will not keep the trade open forever (its timeouts apply). `order info` shows the current status |
| `take-buy` returned `uncertain` with `order_not_saved` | `data.payment_request` is still the hold invoice; the local row is missing. Fix the store, then use `order info`. Commands that need the row fail with `order_unknown` until it exists |

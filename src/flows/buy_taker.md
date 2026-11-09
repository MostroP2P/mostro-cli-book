# Buying as a taker

You take someone's **sell** order: you pay fiat and receive sats on a Lightning invoice.

```text
take-sell ──► waiting-buyer-invoice ──(add-invoice)──► waiting-payment / active
         ──(you pay fiat, fiat-sent)──► fiat-sent ──(seller releases)──► settled-hold-invoice ──► success
```

1. **Find an order.**

   ```sh
   mostro-cli --output json order list --side sell --currency EUR
   ```

   Choose by `fiat_amount` (or `fiat_amount_min`/`max` for a range), `premium_percent`,
   `payment_method`. `sats_amount` `"0"` means the sats are computed at market price when
   you take it.

2. **Take it.** Either with your invoice right away (you must know the sats amount, so this
   suits fixed-sats orders or a Lightning address)...

   ```sh
   mostro-cli --output json order take-sell --order <id> --invoice you@wallet.example --yes
   ```

   ...or without, and let the node compute the amount first:

   ```sh
   mostro-cli --output json order take-sell --order <id> --yes
   ```

   For a range order add `--amount <fiat>`.

3. **Follow `data.next_step`:**

   | `next_step` | Do |
   | --- | --- |
   | `add_invoice` | Create an invoice for `data.order.sats_amount` sats and run `order add-invoice --order <id> --invoice <bolt11> --yes` |
   | `wait_for_seller_payment` | Nothing; the seller must lock the sats |
   | `pay_bond_invoice` | Pay `data.payment_request` (taker bond); the node then continues |

4. **Wait until the order is `active`** (seller paid the hold invoice and your invoice is
   in). `order add-invoice` already tells you with `result: payment_accepted` when the
   seller had paid first; otherwise wait with `order watch --order <id>` and check `order info`.

5. **Pay the fiat** to the seller through the method agreed in
   [`order chat`](../commands/order_chat.md), then:

   ```sh
   mostro-cli --output json order fiat-sent --order <id> --yes
   ```

   `next_step: wait_for_release`.

6. **Wait for the release.** The order goes to `settled-hold-invoice` and then `success`
   when your invoice is paid. If the payment to your invoice fails, the node may ask for a
   new invoice (`next_step: add_invoice` again); `order add-invoice` then answers
   `invoice_updated`.

## If something goes wrong

| Situation | What to do |
| --- | --- |
| `take-sell` refused with `invalid_order_status` | Someone else took it; pick another |
| `take-sell` was `uncertain` | `order info --order <id>`: if the order is no longer `pending`, it may be yours; check `buyer_trade_pubkey` against `data.trade_pubkey` when `order_not_saved` gave you data |
| The seller never pays | Cancel (`order cancel`) |
| The seller does not release after `fiat-sent` | Open a dispute: [`dispute open`](../commands/dispute_open.md) |

"""Example: follow one order with mostro_cli.py, reacting to next_step.

Run:  MOSTRO_PUBKEY=... RELAYS=... python3 example_trade_loop.py <order-id>
It only reads; every write is printed as a suggestion, never executed.
"""

import sys
import time

from mostro_cli import MostroCli, TransportError, message_next_step

TERMINAL = {"success", "canceled", "cooperatively-canceled", "canceled-by-admin",
            "settled-by-admin", "completed-by-admin", "expired"}


def main(order_id: str) -> None:
    cli = MostroCli()
    seen = set()
    rating_suggested = False
    while True:
        try:
            info = cli.order_info(order_id)
            inbox = cli.message_list(since_minutes=60, order=order_id)
        except TransportError as exc:
            print("transport problem, retrying:", exc)
            time.sleep(15)
            continue

        if not info.ok:
            print("order info failed:", info.code, info.reason or "")
            return
        if info.data["not_returned"]:
            print("the node does not return this order")
            return
        status = info.data["orders"][0]["status"]
        print("status:", status)

        if inbox.ok:
            for message in inbox.data["messages"]:
                if message["event_id"] in seen:
                    continue
                step = message_next_step(message)  # an unknown value reads as None
                if (step == "fiat_sent" and status != "active") or (
                        step == "release" and status != "fiat-sent") or (
                        step == "rate" and status not in ("success", "settled-hold-invoice")):
                    continue  # keep it pending: the status may pass on a later poll
                seen.add(message["event_id"])
                payload = message["payload"]
                print(f"  {message['created_at']} {message['action']} next_step={step}")
                if payload["kind"] == "payment_failed":
                    print(f"    payout failed; retries left: {payload['payment_attempts']},"
                          f" every {payload['payment_retries_interval']} s")
                if step in ("pay_hold_invoice", "pay_bond_invoice"):
                    print("    -> pay this invoice with your wallet:", payload["invoice"])
                elif step == "add_invoice":
                    # After add-invoice the "order" payload carries the amount to invoice (the
                    # order's sats minus the Mostro fee). A payment_failed payload carries none,
                    # and order info's sats_amount still includes the fee.
                    if payload["kind"] == "order":
                        invoice = f"<invoice for {payload['order']['sats_amount']} sats>"
                    else:
                        invoice = "<invoice for the order's sats minus the Mostro fee>"
                    print(f"    -> run: order add-invoice --order {order_id} --invoice {invoice} --yes")
                elif step == "add_bond_invoice":
                    print(f"    -> run: bond add-invoice --order {order_id} --invoice <bolt11> --yes")
                elif step == "fiat_sent":
                    print("    -> send the fiat, then run:"
                          f" order fiat-sent --order {order_id} --yes")
                elif step == "release":
                    # Never release on the message alone: it repeats the buyer's claim.
                    print("    -> only once the fiat is in your account, run:"
                          f" order release --order {order_id} --yes")
                elif step == "rate":
                    # The node takes a seller's rating from settled-hold-invoice, a buyer's at success.
                    print(f"    -> run: order rate --order {order_id} --rating <1-5> --yes")
                    rating_suggested = True

        if status in TERMINAL:
            if status == "success" and not rating_suggested:
                # The node sends rate after purchase-completed; it may not be on the relays yet.
                print(f"    -> you can rate the counterparty: order rate --order {order_id} --rating <1-5> --yes")
            return
        time.sleep(20)


if __name__ == "__main__":
    main(sys.argv[1])

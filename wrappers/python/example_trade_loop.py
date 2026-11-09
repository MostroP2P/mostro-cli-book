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
                seen.add(message["event_id"])
                step = message_next_step(message)  # an unknown value reads as None
                payload = message["payload"]
                print(f"  {message['created_at']} {message['action']} next_step={step}")
                if payload["kind"] == "payment_failed":
                    print(f"    payout failed; retries left: {payload['payment_attempts']},"
                          f" every {payload['payment_retries_interval']} s")
                if step in ("pay_hold_invoice", "pay_bond_invoice"):
                    print("    -> pay this invoice with your wallet:", payload["invoice"])
                elif step == "add_invoice":
                    # The payload is "order" after add-invoice, "payment_failed" after a payout
                    # the node will not retry; order info has the amount in both cases.
                    sats = info.data["orders"][0]["sats_amount"]
                    print(f"    -> run: order add-invoice --order {order_id} --invoice <invoice for {sats} sats> --yes")
                elif step == "add_bond_invoice":
                    print(f"    -> run: bond add-invoice --order {order_id} --invoice <bolt11> --yes")

        if status in TERMINAL:
            return
        time.sleep(20)


if __name__ == "__main__":
    main(sys.argv[1])

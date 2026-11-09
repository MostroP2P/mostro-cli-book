"""Minimal, dependency-free Python wrapper for the mostro-cli JSON interface.

    from mostro_cli import MostroCli
    cli = MostroCli(env={"MOSTRO_PUBKEY": "...", "RELAYS": "wss://..."})
    out = cli.order_list(side="sell", currency="USD")
    if out.ok:
        for order in out.data["orders"]:
            print(order["id"], order["fiat_amount"], order["fiat_currency"])

Contract: schema_version "1". Python 3.8+.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

SCHEMA_VERSION = "1"
ARGUMENT_CODES = {"invalid_arguments", "output_not_supported"}
# Commands that publish a request which may change something on the node.
WRITE_COMMANDS = {
    "order.new", "order.take-sell", "order.take-buy", "order.add-invoice",
    "bond.add-invoice", "order.fiat-sent", "order.release", "order.cancel",
}

# next_step values of message records this wrapper knows; the enum is open within v1.
MESSAGE_NEXT_STEPS = {"pay_bond_invoice", "add_invoice", "pay_hold_invoice", "add_bond_invoice"}


def message_next_step(record: Dict[str, Any]) -> Optional[str]:
    """The `next_step` of a message record, or None when it asks nothing this wrapper knows.

    `next_step` is an open enum within contract 1: a value a later binary adds reads as None.
    It is what the message asked when the node sent it; check `order info` before acting.
    """
    step = record.get("next_step")
    return step if step in MESSAGE_NEXT_STEPS else None


class TransportError(Exception):
    """No usable envelope: empty or invalid stdout, timeout, or the process could not start.

    `may_have_acted` is True when the command was a write: treat it like `uncertain`.
    """

    def __init__(self, message: str, *, may_have_acted: bool, stderr: str = "", exit_code: Optional[int] = None):
        super().__init__(message)
        self.may_have_acted = may_have_acted
        self.stderr = stderr
        self.exit_code = exit_code


class IncompatibleError(Exception):
    """The binary speaks another contract version."""


@dataclass
class Outcome:
    """One parsed envelope plus the process exit code and stderr.

    `stderr` is what the process wrote there (for example a config-file `hint:` line);
    it is never parsed.
    """

    raw: Dict[str, Any]
    exit_code: int
    stderr: str = ""
    status: str = field(init=False)
    command: Optional[str] = field(init=False)
    data: Optional[Dict[str, Any]] = field(init=False)
    error: Optional[Dict[str, Any]] = field(init=False)
    warnings: List[Dict[str, str]] = field(init=False)
    meta: Dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        self.status = self.raw["status"]
        self.command = self.raw["command"]
        self.data = self.raw["data"]
        self.error = self.raw["error"]
        self.warnings = self.raw["warnings"]
        self.meta = self.raw["meta"]

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    @property
    def uncertain(self) -> bool:
        return self.status == "uncertain"

    @property
    def code(self) -> Optional[str]:
        return self.error["code"] if self.error else None

    @property
    def reason(self) -> Optional[str]:
        return self.error.get("reason") if self.error else None

    @property
    def warning_codes(self) -> List[str]:
        return [w["code"] for w in self.warnings]

    @property
    def node_may_have_acted(self) -> bool:
        """True when a request was or may have been published."""
        return self.meta["publication"] in ("published", "unknown")

    @property
    def next_step(self) -> Optional[str]:
        return (self.data or {}).get("next_step")


class MostroCli:
    def __init__(self, binary: str = "mostro-cli", env: Optional[Dict[str, str]] = None, timeout: float = 45.0):
        self.binary = binary
        self.env = {**os.environ, **(env or {})}
        self.timeout = timeout

    # ------------------------------------------------------------------ core
    def run(self, args: Sequence[str], *, write: bool = False) -> Outcome:
        """Run `mostro-cli --output json <args>` and return the parsed envelope.

        Never reads or writes stdin. Raises TransportError when there is no
        envelope and IncompatibleError on an unknown schema_version.
        """
        argv = [self.binary, "--output", "json", *args]
        try:
            proc = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                  env=self.env, timeout=self.timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            raise TransportError("timed out", may_have_acted=write,
                                 stderr=(exc.stderr or b"").decode(errors="replace")) from exc
        except OSError as exc:
            raise TransportError(f"cannot start {self.binary}: {exc}", may_have_acted=False) from exc

        stderr = proc.stderr.decode(errors="replace")
        text = proc.stdout.decode("utf-8", errors="strict").strip()
        if not text:
            raise TransportError("empty stdout", may_have_acted=write and proc.returncode == 1,
                                 stderr=stderr, exit_code=proc.returncode)
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise TransportError("stdout is not one JSON document", may_have_acted=write,
                                 stderr=stderr, exit_code=proc.returncode) from exc
        if not isinstance(raw, dict):
            raise TransportError("stdout is not a JSON object", may_have_acted=write,
                                 stderr=stderr, exit_code=proc.returncode)
        if raw.get("schema_version") != SCHEMA_VERSION:
            raise IncompatibleError(f"unsupported schema_version {raw.get('schema_version')!r}")
        outcome = Outcome(raw, proc.returncode, stderr)
        expected = 0 if outcome.ok else (2 if outcome.code in ARGUMENT_CODES else 1)
        if expected != proc.returncode:
            # Should not happen; keep the envelope but make the mismatch visible.
            outcome.raw.setdefault("_wrapper_notes", []).append(
                f"exit code {proc.returncode} does not match status {outcome.status}")
        return outcome

    # --------------------------------------------------------------- helpers
    def schema(self) -> Outcome:
        return self.run(["schema"])

    def order_list(self, side: Optional[str] = None, currency: Optional[str] = None,
                   status: Optional[str] = None) -> Outcome:
        args = ["order", "list"]
        args += _opt("--side", side) + _opt("--currency", currency) + _opt("--status", status)
        return self.run(args)

    def order_info(self, *order_ids: str) -> Outcome:
        if not order_ids:
            raise ValueError("at least one order id")
        args = ["order", "info"]
        for order_id in order_ids:
            args += _opt("--order", order_id)
        return self.run(args)

    def message_list(self, since_minutes: Optional[int] = None, order: Optional[str] = None) -> Outcome:
        return self.run(["message", "list", *_opt("--since", since_minutes), *_opt("--order", order)])

    def order_sync(self, since_minutes: Optional[int] = None) -> Outcome:
        return self.run(["order", "sync", *_opt("--since", since_minutes)])

    # Writes: `confirmed` must reflect the user's consent; it becomes --yes.
    def order_new(self, *, side: str, currency: str, fiat_amount: int, payment_method: str,
                  fiat_amount_max: Optional[int] = None, sats: Optional[int] = None,
                  premium: Optional[int] = None, invoice: Optional[str] = None,
                  expiration_days: Optional[int] = None, confirmed: bool) -> Outcome:
        args = ["order", "new", *_opt("--side", side), *_opt("--currency", currency),
                *_opt("--fiat-amount", fiat_amount), *_opt("--payment-method", payment_method)]
        args += _opt("--fiat-amount-max", fiat_amount_max) + _opt("--sats", sats)
        args += _opt("--premium", premium) + _opt("--invoice", invoice)
        args += _opt("--expiration-days", expiration_days)
        return self._write(args, confirmed)

    def take_sell(self, order: str, *, invoice: Optional[str] = None, amount: Optional[int] = None,
                  confirmed: bool) -> Outcome:
        args = ["order", "take-sell", *_opt("--order", order), *_opt("--invoice", invoice), *_opt("--amount", amount)]
        return self._write(args, confirmed)

    def take_buy(self, order: str, *, amount: Optional[int] = None, confirmed: bool) -> Outcome:
        return self._write(["order", "take-buy", *_opt("--order", order), *_opt("--amount", amount)], confirmed)

    def add_invoice(self, order: str, invoice: str, *, confirmed: bool) -> Outcome:
        return self._write(["order", "add-invoice", *_opt("--order", order), *_opt("--invoice", invoice)], confirmed)

    def bond_add_invoice(self, order: str, invoice: str, *, confirmed: bool) -> Outcome:
        return self._write(["bond", "add-invoice", *_opt("--order", order), *_opt("--invoice", invoice)], confirmed)

    def fiat_sent(self, order: str, *, confirmed: bool) -> Outcome:
        return self._write(["order", "fiat-sent", *_opt("--order", order)], confirmed)

    def release(self, order: str, *, confirmed: bool) -> Outcome:
        return self._write(["order", "release", *_opt("--order", order)], confirmed)

    def cancel(self, order: str, *, confirmed: bool) -> Outcome:
        return self._write(["order", "cancel", *_opt("--order", order)], confirmed)

    def _write(self, args: List[str], confirmed: bool) -> Outcome:
        if not confirmed:
            raise PermissionError("write commands need the user's confirmation (--yes)")
        return self.run([*args, "--yes"], write=True)


def _opt(flag: str, value: Any) -> List[str]:
    """`[flag=value]` when value is not None, else `[]`.

    The attached form keeps a value that starts with `-` (a payment method, say)
    from being parsed as an option. argv items are never shell text.
    """
    return [] if value is None else [f"{flag}={value}"]

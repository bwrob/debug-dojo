"""Interactive demo script for exploring and testing Dojo Debugger (dpdb).

This script provides a realistic order processing flow with nested function calls,
variable transformations, loops, and optional exception triggers for testing:
- Breakpoints (-b function_name or -b line_number)
- Stepping (n: next, s: step into, c: continue, r: return)
- Stack navigation (w: where, u: up, d: down)
- Rich inspections (p: print, pp: pretty-print, vars: local variables)
- Post-mortem debugging (on unhandled exceptions)

Usage:
    # Run from the start
    uv run dojo examples/demo.py

    # Break directly inside process_order
    uv run dojo -b process_order examples/demo.py

    # Trigger post-mortem exception debugging
    TRIGGER_ERROR=1 uv run dojo examples/demo.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

DISCOUNT_THRESHOLD = 100.0


@dataclass(frozen=True, slots=True)
class OrderItem:
    """An individual item in an order."""

    sku: str
    name: str
    price: float
    quantity: int


@dataclass(frozen=True, slots=True)
class OrderSummary:
    """Summary of a processed order."""

    order_id: str
    subtotal: float
    discount: float
    tax: float
    total: float
    item_count: int


def calculate_discount(subtotal: float, *, vip: bool) -> float:
    """Calculate promotional discount based on customer status and subtotal.

    Args:
        subtotal: Order pre-tax amount.
        vip: Whether customer has VIP status.

    Returns:
        Calculated discount amount.

    """
    rate = 0.15 if vip else 0.05
    if subtotal > DISCOUNT_THRESHOLD:
        rate += 0.05
    discount_amount = round(subtotal * rate, 2)
    return discount_amount


def compute_tax(amount: float, tax_rate: float = 0.08) -> float:
    """Compute sales tax for an amount.

    Args:
        amount: Taxable amount.
        tax_rate: Tax rate percentage as decimal.

    Returns:
        Tax amount rounded to two decimals.

    """
    return round(amount * tax_rate, 2)


def process_order(
    order_id: str,
    items: list[OrderItem],
    *,
    vip: bool = False,
) -> OrderSummary:
    """Process an order and return its finalized financial summary.

    Args:
        order_id: Unique order identifier.
        items: List of order line items.
        vip: Whether VIP discount applies.

    Returns:
        Finalized OrderSummary dataclass.

    Raises:
        RuntimeError: When `TRIGGER_ERROR=1` is present in the environment.

    """
    subtotal = sum(item.price * item.quantity for item in items)
    discount = calculate_discount(subtotal, vip=vip)
    taxable = max(0.0, subtotal - discount)
    tax = compute_tax(taxable)
    total = round(taxable + tax, 2)
    total_qty = sum(item.quantity for item in items)

    if os.getenv("TRIGGER_ERROR") == "1":
        msg = f"Simulated failure while committing order {order_id}"
        raise RuntimeError(msg)

    return OrderSummary(
        order_id=order_id,
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        total=total,
        item_count=total_qty,
    )


def main() -> None:
    """Execute sample order pipeline."""
    sample_items = [
        OrderItem(sku="DOJO-001", name="Hattori Hanzo Katana", price=120.0, quantity=1),
        OrderItem(sku="DOJO-002", name="Steel Shuriken Set", price=25.0, quantity=2),
        OrderItem(sku="DOJO-003", name="Silk Shinobi Gi", price=60.0, quantity=1),
    ]

    order_id = "ORD-2026-999"
    is_vip = True

    summary = process_order(order_id, sample_items, vip=is_vip)
    sys.stdout.write(
        f"Order {summary.order_id} processed: total=${summary.total:.2f} "
        f"({summary.item_count} items)\n"
    )


if __name__ == "__main__":
    main()

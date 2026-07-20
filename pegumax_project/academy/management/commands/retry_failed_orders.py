"""Safety-net sweep: retry any paid orders whose Printful submission failed,
escalating to a store credit once the retry window closes.

Prompt retries are normally driven event-by-event through QStash (see
`academy.views._qstash_retry_one`). This command is the once-a-day backstop that
catches anything the QStash chain missed — e.g. an order that failed while QStash
was unreachable. It shares the exact same per-order logic (`_retry_single_order`)
so fulfillment, exhaustion and crediting behave identically on both paths, and an
order can never be charged/manufactured twice.

Usage:  python manage.py retry_failed_orders [--limit N]
"""
from django.core.management.base import BaseCommand

from academy.models import FulfilledOrder
from academy.views import _retry_single_order


class Command(BaseCommand):
    help = "Safety-net sweep of failed Printful orders; credit once retries are exhausted."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0,
                            help="Max orders to process this run (0 = all).")

    def handle(self, *args, **opts):
        failed = FulfilledOrder.objects.filter(
            status=FulfilledOrder.STATUS_PRINTFUL_FAILED).order_by("created_at")
        if opts.get("limit"):
            failed = failed[:opts["limit"]]
        failed = list(failed)
        if not failed:
            self.stdout.write("No failed orders to retry.")
            return

        tally = {"succeeded": 0, "credited": 0, "failed": 0, "skipped": 0, "done": 0}
        for order in failed:
            result = _retry_single_order(order)
            tally[result] = tally.get(result, 0) + 1
            if result == "succeeded":
                self.stdout.write(self.style.SUCCESS(
                    f"  [ok] {order.session_id} fulfilled (printful id={order.printful_order_id})"))
            elif result == "credited":
                self.stdout.write(self.style.WARNING(
                    f"  [!] {order.session_id} exhausted -> credited ${order.amount_total}"))
            elif result == "skipped":
                self.stdout.write(f"  [~] {order.session_id} skipped (attempted moments ago)")
            elif result == "failed":
                self.stdout.write(
                    f"  [..] {order.session_id} attempt {order.attempts} failed: {(order.note or '')[:80]}")

        self.stdout.write(self.style.SUCCESS(
            "\nDone. " + " ".join(f"{k}={v}" for k, v in tally.items())))

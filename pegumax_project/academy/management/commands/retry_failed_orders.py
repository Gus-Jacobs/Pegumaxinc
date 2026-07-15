"""Retry paid orders whose Printful submission failed, and escalate to a store
credit if they can't be fulfilled within the retry window.

Designed to run on a schedule (e.g. a Render Cron every ~5 minutes). It only
touches orders still marked printful_failed, and the moment one succeeds it's
marked processed — so a customer can never be charged/manufactured twice.

Usage:  python manage.py retry_failed_orders
"""
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from academy import emails as academy_emails
from academy.models import FulfilledOrder, StoreCredit
from academy.views import _create_printful_order, _printful_items


class Command(BaseCommand):
    help = "Retry failed Printful orders; grant a store credit when retries are exhausted."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0,
                            help="Max orders to process this run (0 = all). Bounds a "
                                 "web-triggered run's duration.")

    def handle(self, *args, **opts):
        max_attempts = int(getattr(settings, "PRINTFUL_RETRY_MAX_ATTEMPTS", 36))
        window_hours = int(getattr(settings, "PRINTFUL_RETRY_WINDOW_HOURS", 3))
        cutoff = timezone.now() - timedelta(hours=window_hours)
        site = getattr(settings, "PEGUMAX_SITE_URL", "https://pegumax.com").rstrip("/")
        try:
            account_url = site + reverse("main_site:account")
        except Exception:
            account_url = site

        failed = FulfilledOrder.objects.filter(
            status=FulfilledOrder.STATUS_PRINTFUL_FAILED).order_by("created_at")
        if opts.get("limit"):
            failed = failed[:opts["limit"]]
        failed = list(failed)
        if not failed:
            self.stdout.write("No failed orders to retry.")
            return

        retried = succeeded = credited = 0
        for order in failed:
            items = _printful_items(order.pf_items)
            ext = order.payment_intent or f"peg-{order.pk}"
            order_id, err = (None, "missing items or shipping address")
            if items and order.recipient:
                order_id, err = _create_printful_order(items, order.recipient, ext)

            order.attempts = (order.attempts or 0) + 1
            order.last_attempt_at = timezone.now()
            retried += 1

            if order_id:
                order.printful_order_id = str(order_id)
                order.status = FulfilledOrder.STATUS_PROCESSED
                order.note = ""
                order.save(update_fields=["printful_order_id", "status", "note",
                                          "attempts", "last_attempt_at", "updated_at"])
                succeeded += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  [ok] {order.session_id} fulfilled (printful id={order_id})"))
                continue

            order.note = (err or "retry failed")[:255]
            exhausted = order.attempts >= max_attempts or order.created_at <= cutoff

            if exhausted:
                order.status = FulfilledOrder.STATUS_CREDITED
                order.save(update_fields=["status", "note", "attempts",
                                          "last_attempt_at", "updated_at"])
                # Grant exactly one credit per order.
                if order.user and not StoreCredit.objects.filter(source_order=order).exists():
                    StoreCredit.objects.create(
                        user=order.user, amount=order.amount_total, source_order=order,
                        payment_intent=order.payment_intent,
                        note=f"Auto-credit: order {order.session_id} could not be fulfilled.")
                    try:
                        academy_emails.send_free_item_granted(order.email, order.amount_total, account_url)
                    except Exception as e:
                        self.stderr.write(f"  ! credit email failed for {order.session_id}: {e}")
                    credited += 1
                    self.stdout.write(self.style.WARNING(
                        f"  [!] {order.session_id} exhausted -> credited ${order.amount_total}"))
            else:
                order.save(update_fields=["status", "note", "attempts",
                                          "last_attempt_at", "updated_at"])
                self.stdout.write(
                    f"  [..] {order.session_id} attempt {order.attempts}/{max_attempts} failed: {err[:80]}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. retried={retried} succeeded={succeeded} credited={credited}"))

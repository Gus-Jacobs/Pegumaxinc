"""Sync products from Printful into the MerchItem catalogue.

Pulls the store's sync products + their variants from the Printful API and
maps them onto MerchItem (keyed by printful_sync_id), saving the remote main
image URL and a normalized variants JSON (size / color / price).

Usage:
    python manage.py sync_printful
    python manage.py sync_printful --dry-run
    python manage.py sync_printful --deactivate-missing

Requires settings.PRINTFUL_API_KEY (PRINTFUL_API_KEY in .env).
"""
import time
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from academy.models import MerchItem

API_BASE = "https://api.printful.com"

# Derive a product_type from the product name (first match wins).
TYPE_KEYWORDS = [
    ("hoodie", "hoodie"), ("sweatshirt", "sweatshirt"), ("tank", "tank"),
    ("t-shirt", "tee"), ("tee", "tee"), ("shirt", "tee"),
    ("mug", "mug"), ("sticker", "sticker"), ("hat", "hat"), ("cap", "hat"),
    ("tote", "tote"), ("poster", "poster"), ("case", "phone-case"),
]

def _detect_type(name):
    low = name.lower()
    for kw, val in TYPE_KEYWORDS:
        if kw in low:
            return val
    return ""


def _detect_level(name):
    """Parse the required account level from a 'Developer N ...' product name."""
    import re
    m = re.search(r"developer\s+(\d+)", (name or "").lower())
    return int(m.group(1)) if m else 0


class Command(BaseCommand):
    help = "Fetch products from Printful and upsert them into MerchItem."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Fetch and report without writing to the database.")
        parser.add_argument("--keep-missing", action="store_true",
                            help="Do NOT touch items no longer in Printful (default is to deactivate them).")
        parser.add_argument("--delete-missing", action="store_true",
                            help="Hard-delete items no longer in Printful instead of deactivating.")

    def handle(self, *args, **opts):
        api_key = getattr(settings, "PRINTFUL_API_KEY", "")
        if not api_key:
            raise CommandError("PRINTFUL_API_KEY is not set. Add it to your .env.")

        try:
            import requests
        except ImportError:
            raise CommandError("The 'requests' package is required: pip install requests")

        headers = {"Authorization": f"Bearer {api_key}"}
        store_id = getattr(settings, "PRINTFUL_STORE_ID", "")
        if store_id:
            headers["X-PF-Store-Id"] = str(store_id)

        session = requests.Session()
        session.headers.update(headers)

        def get(path):
            resp = session.get(f"{API_BASE}{path}", timeout=30)
            resp.raise_for_status()
            return resp.json().get("result")

        try:
            products = get("/store/products")
        except Exception as e:
            raise CommandError(f"Failed to list Printful products: {e}")

        if not products:
            self.stdout.write(self.style.WARNING("No products returned from Printful."))
            return

        dry = opts["dry_run"]
        seen_ids = []
        created = updated = 0

        for prod in products:
            sync_id = str(prod.get("id"))
            seen_ids.append(sync_id)
            name = prod.get("name") or f"Printful product {sync_id}"
            thumb = prod.get("thumbnail_url") or ""

            # Pull per-product detail for variant data (be gentle on rate limits).
            variants, min_price, any_available = [], None, False
            try:
                detail = get(f"/store/products/{sync_id}")
                time.sleep(0.2)
            except Exception as e:
                self.stderr.write(self.style.WARNING(
                    f"  ! Could not fetch detail for {name} ({sync_id}): {e}"))
                detail = None

            if detail:
                sp = detail.get("sync_product") or {}
                thumb = sp.get("thumbnail_url") or thumb
                for v in (detail.get("sync_variants") or []):
                    try:
                        price = Decimal(str(v.get("retail_price") or "0"))
                    except (InvalidOperation, TypeError):
                        price = Decimal("0")
                    if price > 0 and (min_price is None or price < min_price):
                        min_price = price
                    # Prefer the product MOCKUP (file type "preview"), not the
                    # raw print file ("default"). Fall back to the catalog garment
                    # photo for the variant's colour, then the product thumbnail.
                    files = v.get("files") or []
                    preview = next((f.get("preview_url") for f in files
                                    if f.get("type") == "preview" and f.get("preview_url")), "")
                    if not preview:
                        preview = (v.get("product") or {}).get("image") or ""
                    availability = (v.get("availability_status") or "").lower()
                    # A permanently-discontinued variant is unavailable; anything
                    # else (incl. temporary out-of-stock or unknown) counts as sellable.
                    if availability != "discontinued":
                        any_available = True
                    variants.append({
                        "id": v.get("id"),
                        "variant_id": v.get("variant_id"),
                        "name": v.get("name") or "",
                        "size": v.get("size") or "",
                        "color": v.get("color") or "",
                        "price": str(price),
                        "currency": v.get("currency") or "USD",
                        "image": preview or thumb,
                        "availability": availability,
                    })

            price = min_price if min_price is not None else Decimal("0")
            # Out of stock: a product with variants where every variant is
            # discontinued is hidden from the store (active=False).
            is_active = (not variants) or any_available

            self.stdout.write(
                f"  - {name}  ({len(variants)} variants, from ${price})"
                + ("" if is_active else "  [ALL DISCONTINUED — hiding]"))
            if dry:
                continue

            obj = MerchItem.objects.filter(printful_sync_id=sync_id).first()
            defaults = {
                "name": name,
                "base_image_url": thumb,
                "variants": variants,
                "price": price,
                "active": is_active,
            }
            detected_type = _detect_type(name)
            detected_level = _detect_level(name)
            if obj:
                for k, val in defaults.items():
                    setattr(obj, k, val)
                # Auto-fill type when not curated; always reflect the name's level gate.
                if not obj.product_type and detected_type:
                    obj.product_type = detected_type
                obj.required_level = detected_level
                obj.save()
                updated += 1
            else:
                MerchItem.objects.create(
                    printful_sync_id=sync_id,
                    slug=slugify(name)[:200] or f"printful-{sync_id}",
                    product_type=detected_type,
                    required_level=detected_level,
                    **defaults,
                )
                created += 1

        # Products removed from Printful → remove them from the store. Only
        # affects Printful-synced items (printful_sync_id set); never touches
        # manually-created merch. Default = deactivate; opt-outs available.
        removed = 0
        stale = (MerchItem.objects
                 .exclude(printful_sync_id="")
                 .exclude(printful_sync_id__in=seen_ids))
        if not dry:
            if opts["keep_missing"]:
                pass
            elif opts["delete_missing"]:
                removed = stale.count()
                stale.delete()
            else:
                removed = stale.update(active=False)
        else:
            removed = stale.count()

        if removed:
            verb = "would remove" if dry else ("deleted" if opts.get("delete_missing") else "deactivated")
            self.stdout.write(self.style.WARNING(
                f"  {verb} {removed} item(s) no longer in Printful."))

        if dry:
            self.stdout.write(self.style.SUCCESS(
                f"\nDry run complete — {len(products)} product(s) inspected, nothing written."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nDone. {created} created, {updated} updated, {removed} removed."))

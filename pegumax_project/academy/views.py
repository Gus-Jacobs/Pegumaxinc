"""Academy views: storefront, guarded learning, Stripe checkout/webhook,
quiz evaluation + gamification, certificates, and the learner dashboard.
"""
import json
import logging
import secrets
from datetime import timedelta
from io import StringIO

from django.core.management import call_command

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import cart as cart_utils
from . import emails as academy_emails
from .cart import ACTIVE_PROMO_SESSION_KEY, CART_CODES_SESSION_KEY, PROMO_TARGET_SESSION_KEY
from .context_processors import LEVEL_UP_SESSION_KEY
from .markdown_lite import render_markdown
from .models import (
    Achievement,
    Course,
    CourseModule,
    FulfilledOrder,
    GeneratedPromoCode,
    IssuedCertificate,
    MerchItem,
    StoreCredit,
    UserCourseProgress,
    UserProfile,
    DEFAULT_ATTEMPTS,
    PASS_THRESHOLD,
    PROMO_VALID_DAYS,
    REWARD_DISCOUNT,
    SECOND_CHANCE_DISCOUNT,
)


logger = logging.getLogger("academy")
User = get_user_model()

PRINTFUL_API_BASE = "https://api.printful.com"
# Countries Stripe will collect a shipping address for on merch checkouts.
MERCH_SHIP_COUNTRIES = ["US", "CA", "GB", "AU", "IT", "DE", "FR", "ES", "NL", "IE", "NZ"]


def _fulfillment_items(cart):
    """Compact [{v: sync_variant_id, q: qty}] for Printful, from cart lines."""
    items = []
    for li in cart.values():
        sv = li.get("sync_variant_id")
        if sv:
            items.append({"v": sv, "q": max(1, int(li.get("qty", 1)))})
    return items


# ---------------------------------------------------------------------------
#  Stripe helpers
# ---------------------------------------------------------------------------
def _stripe():
    """Return a configured stripe module, or None if unavailable/unconfigured."""
    key = getattr(settings, "STRIPE_SECRET_KEY", None)
    if not key:
        return None
    try:
        import stripe
    except ImportError:
        return None
    stripe.api_key = key
    return stripe


def _abs(request, name, *args, **kwargs):
    return request.build_absolute_uri(reverse(name, args=args, kwargs=kwargs))


def _as_dict(obj):
    """Coerce a Stripe object (or anything) to a plain, recursively-plain dict.

    Stripe's resource objects change shape between library versions; our helpers
    only ever use dict access, so we normalize at the boundary to stay
    version-proof.
    """
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    for attr in ("to_dict_recursive", "to_dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    try:
        return dict(obj)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
#  Storefront (public browsing; buying/viewing requires auth)
# ---------------------------------------------------------------------------
def _user_store_context(request):
    """Profile + owned course ids for the logged-in user (or empties)."""
    profile, owned = None, set()
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        owned = set(UserCourseProgress.objects
                    .filter(user=request.user, purchased=True)
                    .values_list("course_id", flat=True))
    return profile, owned


def _decorate_merch(items, level):
    """Annotate each merch item with its level-lock state for the template."""
    decorated = []
    for m in items:
        decorated.append({
            "item": m,
            "locked": level < m.unlock_level,
            "unlock_level": m.unlock_level,
        })
    return decorated


def _resolve_promo(code):
    """Return a valid GeneratedPromoCode for the code, or None."""
    if not code:
        return None
    promo = GeneratedPromoCode.objects.filter(code_string=code).first()
    return promo if (promo and promo.is_valid) else None


SIZE_ORDER = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "2XL", "3XL", "4XL", "5XL"]


def _structure_variants(item):
    """Group variants into ordered colors (with a representative image) + sizes,
    and a flat list the front-end uses to resolve a (color,size) selection."""
    variants = item.variants or []
    colors, seen = [], set()
    for v in variants:
        c = (v.get("color") or "").strip()
        if c and c not in seen:
            seen.add(c)
            colors.append({"name": c, "image": v.get("image") or item.base_image_url})
    size_set = {(v.get("size") or "").strip() for v in variants if v.get("size")}
    sizes = [s for s in SIZE_ORDER if s in size_set]
    sizes += sorted(s for s in size_set if s not in SIZE_ORDER)
    return colors, sizes, variants


# ---------------------------------------------------------------------------
#  Store legal pages (separate from the main software Privacy Policy / Terms)
# ---------------------------------------------------------------------------
def store_privacy(request):
    return render(request, "academy/legal/privacy.html", {"active_section": "store"})


def store_terms(request):
    return render(request, "academy/legal/terms.html", {"active_section": "store"})


def store_returns(request):
    return render(request, "academy/legal/returns.html", {"active_section": "store"})


def merch_detail(request, slug):
    item = get_object_or_404(MerchItem, slug=slug, active=True)
    profile, _owned = _user_store_context(request)
    level = profile.current_level if profile else 1
    promo = _resolve_promo((request.GET.get("promo") or "").strip())
    if promo:
        request.session[ACTIVE_PROMO_SESSION_KEY] = promo.code_string

    colors, sizes, variants = _structure_variants(item)
    return render(request, "academy/merch_detail.html", {
        "item": item,
        "description_html": render_markdown(item.description),
        "locked": level < item.unlock_level,
        "unlock_level": item.unlock_level,
        "level": level,
        "active_promo": promo,
        "user_code_count": len(_user_valid_codes(request.user)),
        "colors": colors,
        "sizes": sizes,
        "variants_json": variants,
        "active_section": "store",
    })


def storefront(request):
    type_filter = (request.GET.get("type") or "").strip().lower()
    tag_filter = (request.GET.get("tag") or "").strip().lower()
    promo = _resolve_promo((request.GET.get("promo") or "").strip())
    if promo:
        # Remember it so it can auto-apply at cart checkout too.
        request.session[ACTIVE_PROMO_SESSION_KEY] = promo.code_string

    courses = Course.objects.filter(published=True)

    merch_qs = MerchItem.objects.filter(active=True)
    if tag_filter:
        merch_qs = merch_qs.filter(tags__icontains=tag_filter)
    if type_filter:
        merch_qs = merch_qs.filter(
            Q(product_type__icontains=type_filter) | Q(name__icontains=type_filter))

    profile, owned = _user_store_context(request)
    level = profile.current_level if profile else 1

    all_merch = _decorate_merch(merch_qs, level)

    return render(request, "academy/storefront.html", {
        "courses": courses,
        "all_merch": all_merch,
        "owned_course_ids": owned,
        "profile": profile,
        "level": level,
        "type_filter": type_filter,
        "tag_filter": tag_filter,
        "active_promo": promo,
        "user_code_count": len(_user_valid_codes(request.user)),
        "active_section": "store",
    })


@login_required
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, published=True)
    progress = UserCourseProgress.objects.filter(user=request.user, course=course).first()
    modules = course.modules.all()
    return render(request, "academy/course_detail.html", {
        "course": course,
        "modules": modules,
        "progress": progress,
        "owned": bool(progress and progress.purchased),
        "second_chance_discount": SECOND_CHANCE_DISCOUNT,
        "active_section": "store",
    })


@login_required
def lesson(request, slug, module_number):
    course = get_object_or_404(Course, slug=slug, published=True)
    progress = UserCourseProgress.objects.filter(user=request.user, course=course).first()
    if not (progress and progress.purchased):
        messages.info(request, "Purchase this course to access its lessons.")
        return redirect("academy:course_detail", slug=slug)

    module = get_object_or_404(CourseModule, course=course, module_number=module_number)
    modules = list(course.modules.all())

    # Sequential gating: you may view a module only if you've already answered it
    # or it's the next one in sequence. A wrong answer never blocks progress.
    next_allowed = progress.next_module_number()
    already_answered = progress.has_answered(module.module_number)
    if not already_answered and module.module_number > next_allowed:
        messages.info(request, "Work through the earlier modules first to reach this one.")
        return redirect("academy:lesson", slug=slug, module_number=next_allowed)

    # One-shot course-completion celebration (set when the final eval passes).
    completion = request.session.pop("academy_completed_course", None)
    if completion is not None:
        request.session.modified = True

    return render(request, "academy/lesson.html", {
        "course": course,
        "module": module,
        "modules": modules,
        "progress": progress,
        "content_html": render_markdown(module.markdown_content),
        "quiz": module.quiz or {},
        "already_answered": already_answered,
        "module_result": progress.result_for(module.module_number),
        "is_final": module.module_number == course.final_module_number,
        "completion": completion,
        "active_section": "store",
    })


# ---------------------------------------------------------------------------
#  Phase 4 — Aggregate course grading, XP, level-up, attempts, completion
# ---------------------------------------------------------------------------
@login_required
@require_POST
def submit_quiz(request, slug, module_number):
    """Record a module answer (right or wrong) without halting progress.

    Grading is course-wide: the only place a course can be passed or failed is
    the submission of the final module's quiz, evaluated against the aggregate
    of all module answers this attempt.
    """
    course = get_object_or_404(Course, slug=slug, published=True)
    progress = UserCourseProgress.objects.filter(user=request.user, course=course).first()
    if not (progress and progress.purchased):
        return redirect("academy:course_detail", slug=slug)

    module = get_object_or_404(CourseModule, course=course, module_number=module_number)

    # A locked course (failed every attempt) blocks until re-purchase.
    if progress.is_locked:
        messages.error(request, "This course is locked — you've used all your attempts. "
                                "Re-purchase for a 50% second-chance discount to reset.")
        return redirect("academy:course_detail", slug=slug)

    # One answer per module per attempt keeps the aggregate tally honest.
    if progress.has_answered(module.module_number):
        messages.info(request, "You've already answered this module this attempt.")
        return redirect("academy:lesson", slug=slug, module_number=module_number)

    quiz = module.quiz or {}
    try:
        chosen = int(request.POST.get("answer", -1))
    except (TypeError, ValueError):
        chosen = -1
    correct_idx = int(quiz.get("answer", -1))
    is_correct = chosen == correct_idx and correct_idx >= 0

    _record_answer(request, progress, module, is_correct)

    # The whole-course evaluation happens only on the final module's submission.
    if module.module_number == course.final_module_number:
        _evaluate_course(request, progress, course)

    return redirect("academy:lesson", slug=slug, module_number=module.module_number)


def _award_xp(request, amount):
    """Add XP to the user's profile and arm the global level-up celebration."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    leveled_up, new_level = profile.add_xp(amount)
    if leveled_up:
        request.session[LEVEL_UP_SESSION_KEY] = new_level
        messages.success(request, f"Level up! You reached Level {new_level}. 🎉",
                         extra_tags="level_up")
    return profile


def _record_answer(request, progress, module, is_correct):
    """Log a module answer. Wrong answers are recorded but never block progress."""
    n = module.module_number
    answered = set(progress.answered_modules or [])
    answered.add(n)
    progress.answered_modules = sorted(answered)

    results = dict(progress.module_results or {})
    results[str(n)] = bool(is_correct)
    progress.module_results = results

    if is_correct:
        passed = set(progress.passed_modules or [])
        passed.add(n)
        progress.passed_modules = sorted(passed)

    progress.save(update_fields=["answered_modules", "module_results",
                                 "passed_modules", "updated_at"])

    if is_correct:
        # Small per-correct XP keeps mid-course level-ups firing.
        _award_xp(request, 50)
        messages.success(request, f"Correct! +50 XP — “{module.title}”.")
    else:
        messages.warning(request, f"Not quite — “{module.title}” marked incorrect. "
                                  "Keep going; your final grade is the course average.")


def _evaluate_course(request, progress, course):
    """Aggregate pass/fail evaluation, run only after the final module is answered."""
    total = course.module_count or 1
    score = int(round(100 * progress.correct_count / total))
    progress.final_score = score

    if score >= PASS_THRESHOLD:
        _complete_course(request, progress, course, score)
        return

    # Failed this attempt.
    progress.attempts_remaining = max(0, progress.attempts_remaining - 1)
    if progress.attempts_remaining <= 0:
        progress.save(update_fields=["final_score", "attempts_remaining", "updated_at"])
        messages.error(
            request,
            f"You scored {score}% — below the {PASS_THRESHOLD}% pass mark, and that "
            f"was your last attempt. This course is now locked. Re-purchase for a "
            f"{SECOND_CHANCE_DISCOUNT}% second-chance discount to reset your attempts.",
        )
    else:
        # Reset the attempt so the student can retake the whole course evaluation.
        progress.reset_attempt()
        progress.save(update_fields=["final_score", "attempts_remaining",
                                     "answered_modules", "module_results",
                                     "passed_modules", "updated_at"])
        messages.warning(
            request,
            f"You scored {score}% — below the {PASS_THRESHOLD}% pass mark. "
            f"You have {progress.attempts_remaining} full retake remaining; your "
            f"answers have been reset so you can run the course again.",
        )


def _complete_course(request, progress, course, score):
    progress.completed = True
    progress.final_score = score
    progress.completed_at = timezone.now()
    progress.save(update_fields=["completed", "final_score", "completed_at", "updated_at"])

    # Completion XP bonus, scaled by how far above the pass mark they landed.
    bonus = 150 + 2 * max(0, score - PASS_THRESHOLD)
    _award_xp(request, bonus)

    # Certificate
    cert, _ = IssuedCertificate.objects.get_or_create(
        user=request.user, course=course,
        defaults={"certification_name": course.title},
    )

    # Achievement badge
    Achievement.objects.get_or_create(
        user=request.user, name=f"Completed: {course.title}",
        defaults={"description": f"Passed {course.title} with a {score}% aggregate score."},
    )

    # Phase 5 — reward promo code (50% off, tagged to the course domain, 30-day life)
    promo = _create_completion_promo(request.user, course)

    # Congratulations + reward email (best-effort; never blocks grading).
    academy_emails.send_course_completion(
        request.user.email,
        course.title,
        score,
        _abs(request, "academy:certificate", cert.unique_uuid),
        promo.code_string,
        promo.discount_percentage,
        _abs(request, "academy:storefront") + f"?promo={promo.code_string}",
    )

    messages.success(
        request,
        f"🏆 Course complete at {score}%! Your certificate is ready and you've "
        f"unlocked a {REWARD_DISCOUNT}% reward code: {promo.code_string}",
        extra_tags="course_complete",
    )

    # The completion modal owns the celebration for this turn, so suppress the
    # separate global level-up modal to avoid two pop-ups stacking — the modal
    # fires its own confetti for a single cohesive moment.
    request.session.pop(LEVEL_UP_SESSION_KEY, None)
    request.session["academy_completed_course"] = {
        "title": course.title,
        "cert_uuid": str(cert.unique_uuid),
        "promo": promo.code_string,
        "promo_tag": promo.target_tag,
        "score": score,
    }
    request.session.modified = True


def _create_completion_promo(user, course):
    tag = course.domain_tag or "pegumax"
    code = f"{tag.upper().replace('-', '')[:10]}-{secrets.token_hex(3).upper()}"
    # The 50%-off reward applies to a single unit at cart checkout, computed by
    # us at the line-item level (see _build_line_items). We deliberately do NOT
    # mirror this into a Stripe coupon: a session-level coupon would discount the
    # whole order (e.g. 50% off a $200 cart), which is not what we want.
    promo = GeneratedPromoCode.objects.create(
        user=user,
        code_string=code,
        discount_percentage=REWARD_DISCOUNT,
        target_tag=tag,
        expiration_date=timezone.now() + timedelta(days=PROMO_VALID_DAYS),
        active_status=True,
    )
    return promo


# ---------------------------------------------------------------------------
#  Phase 3 — Stripe checkout + webhook
# ---------------------------------------------------------------------------
def _money(amount):
    """Decimal/float dollars -> integer cents."""
    return int(round(float(amount) * 100))


@login_required
@require_POST
def checkout_course(request, slug):
    course = get_object_or_404(Course, slug=slug, published=True)
    progress, _ = UserCourseProgress.objects.get_or_create(user=request.user, course=course)

    if progress.purchased and not progress.is_locked:
        messages.info(request, "You already own this course.")
        return redirect("academy:course_detail", slug=slug)

    stripe = _stripe()
    if not stripe:
        messages.error(request, "Payments aren't configured on the server yet "
                                "(STRIPE_SECRET_KEY missing).")
        return redirect("academy:course_detail", slug=slug)

    # Phase 4.6 — locked course re-purchase gets the 50% second-chance discount.
    second_chance = progress.is_locked
    unit = _money(course.price)
    if second_chance:
        unit = int(round(unit * (100 - SECOND_CHANCE_DISCOUNT) / 100))

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            allow_promotion_codes=True,
            client_reference_id=str(request.user.id),
            line_items=[{
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "product_data": {
                        "name": (f"{course.title} (Second-chance 50% off)"
                                 if second_chance else course.title),
                        "description": course.summary[:300] if course.summary else "",
                    },
                    "unit_amount": unit,
                },
                "quantity": 1,
            }],
            metadata={
                "kind": "course",
                "course_id": str(course.id),
                "course_slug": course.slug,
                "user_id": str(request.user.id),
                "second_chance": "1" if second_chance else "0",
            },
            success_url=_abs(request, "academy:checkout_success") + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=_abs(request, "academy:checkout_cancel"),
        )
        return redirect(session.url)
    except Exception as e:
        print(f"[academy] course checkout error: {e}")
        messages.error(request, "Could not start checkout. Please try again.")
        return redirect("academy:course_detail", slug=slug)


@login_required
@require_POST
def checkout_merch(request, pk):
    """Direct single-item buy (no reward code — those are applied via the cart)."""
    item = get_object_or_404(MerchItem, pk=pk, active=True)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.current_level < item.unlock_level:
        messages.error(request, f"This item unlocks at Level {item.unlock_level}. "
                                f"You're Level {profile.current_level} — keep earning XP.")
        return redirect("academy:merch_detail", slug=item.slug)

    stripe = _stripe()
    if not stripe:
        messages.error(request, "Payments aren't configured on the server yet.")
        return redirect("academy:merch_detail", slug=item.slug)

    metadata = {"kind": "merch", "merch_id": str(item.id), "user_id": str(request.user.id)}
    # Best-effort fulfillment: a direct buy has no variant picker, so use the
    # first sync variant if the product has them.
    first_variant = (item.variants or [{}])[0]
    if first_variant.get("id"):
        metadata["pf_items"] = json.dumps([{"v": first_variant["id"], "q": 1}])

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            client_reference_id=str(request.user.id),
            line_items=[{
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "product_data": {"name": item.name, "description": item.description[:300]},
                    "unit_amount": _money(item.price),
                },
                "quantity": 1,
            }],
            metadata=metadata,
            shipping_address_collection={"allowed_countries": MERCH_SHIP_COUNTRIES},
            phone_number_collection={"enabled": True},
            success_url=_abs(request, "academy:checkout_success") + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=_abs(request, "academy:checkout_cancel"),
        )
        return redirect(session.url)
    except Exception as e:
        print(f"[academy] merch checkout error: {e}")
        messages.error(request, "Could not start checkout. Please try again.")
        return redirect("academy:merch_detail", slug=item.slug)


def _fulfill_course(metadata):
    """Idempotently grant/refresh course access from session metadata."""
    try:
        course_id = int(metadata.get("course_id"))
        user_id = int(metadata.get("user_id"))
    except (TypeError, ValueError):
        return None
    progress, _ = UserCourseProgress.objects.get_or_create(
        course_id=course_id, user_id=user_id)
    progress.purchased = True
    if metadata.get("second_chance") == "1":
        # Second chance: reset attempts so the learner is unlocked again.
        progress.attempts_remaining = DEFAULT_ATTEMPTS
    progress.save()
    return progress


def _fulfill_session(session):
    """Process a paid Checkout Session (shared by webhook + success return)."""
    if session.get("payment_status") != "paid":
        return
    metadata = session.get("metadata") or {}
    if metadata.get("kind") == "course":
        _fulfill_course(metadata)
    # Merch needs no DB state beyond the payment record itself.

    # Mark any attached reward codes consumed (single-use). Supports one code
    # (promo_code) or several across cart lines (promo_codes, comma-separated).
    codes = []
    if metadata.get("promo_code"):
        codes.append(metadata["promo_code"])
    if metadata.get("promo_codes"):
        codes.extend(c for c in metadata["promo_codes"].split(",") if c)
    for code in set(codes):
        promo = GeneratedPromoCode.objects.filter(code_string=code).first()
        if promo:
            promo.mark_redeemed()


# ---------------------------------------------------------------------------
#  Printful physical fulfillment
# ---------------------------------------------------------------------------
def _extract_recipient(session):
    """Map a Stripe Checkout Session's shipping details to a Printful recipient."""
    shipping = (session.get("shipping_details")
                or (session.get("collected_information") or {}).get("shipping_details")
                or {})
    customer = session.get("customer_details") or {}
    addr = shipping.get("address") or customer.get("address") or {}
    name = shipping.get("name") or customer.get("name") or ""
    phone = customer.get("phone") or shipping.get("phone") or ""

    recipient = {
        "name": name,
        "address1": addr.get("line1") or "",
        "address2": addr.get("line2") or "",
        "city": addr.get("city") or "",
        "state_code": addr.get("state") or "",
        "country_code": addr.get("country") or "",
        "zip": addr.get("postal_code") or "",
        "email": customer.get("email") or "",
    }
    if phone:
        recipient["phone"] = phone
    return recipient


def _recipient_is_complete(r):
    return all([r.get("name"), r.get("address1"), r.get("city"),
                r.get("country_code"), r.get("zip")])


def _session_email(session):
    """Buyer email: prefer the address entered at Stripe, fall back to the User."""
    email = (session.get("customer_details") or {}).get("email")
    if email:
        return email
    uid = (session.get("metadata") or {}).get("user_id")
    if uid:
        u = User.objects.filter(pk=uid).first()
        if u:
            return u.email
    return None


def _stripe_line_descriptions(session):
    """Fetch human-readable purchased lines (description/qty/amount) from Stripe."""
    stripe = _stripe()
    out = []
    if not stripe:
        return out
    try:
        data = _as_dict(stripe.checkout.Session.list_line_items(session.get("id"), limit=50))
        for li in data.get("data", []):
            li = _as_dict(li)
            out.append({
                "description": li.get("description"),
                "quantity": li.get("quantity"),
                "amount": round((li.get("amount_total") or 0) / 100, 2),
            })
    except Exception as e:
        logger.error("Could not fetch line items for session %s: %s", session.get("id"), e)
    return out


def _hash_id(value):
    import hashlib
    return hashlib.sha1((value or "").encode()).hexdigest()[:20]


def _pf_items_raw(raw):
    """Normalize stored/metadata pf_items to a plain list of {v, q} dicts."""
    if isinstance(raw, str):
        try:
            return json.loads(raw) or []
        except (ValueError, TypeError):
            return []
    return raw or []


def _printful_items(pf_items):
    """[{v: sync_variant_id, q: qty}] (or its JSON string) -> Printful items."""
    if isinstance(pf_items, str):
        try:
            pf_items = json.loads(pf_items)
        except (ValueError, TypeError):
            return []
    out = []
    for it in (pf_items or []):
        v = it.get("v") if isinstance(it, dict) else None
        if v:
            out.append({"sync_variant_id": v, "quantity": int(it.get("q", 1) or 1)})
    return out


def _create_printful_order(items, recipient, external_id):
    """Core Printful order creation, callable from the webhook AND the retry job.

    Returns (order_id, error). order_id is set on success; error is a short string
    on failure. Never raises.
    """
    api_key = getattr(settings, "PRINTFUL_API_KEY", "")
    if not api_key:
        return None, "PRINTFUL_API_KEY not configured"
    if not items:
        return None, "no items"
    if not _recipient_is_complete(recipient):
        return None, "incomplete shipping address"

    confirm = bool(getattr(settings, "PRINTFUL_CONFIRM_ORDERS", False))
    payload = {"external_id": (external_id or "")[:40], "recipient": recipient,
               "items": items, "confirm": confirm}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    store_id = getattr(settings, "PRINTFUL_STORE_ID", "")
    if store_id:
        headers["X-PF-Store-Id"] = str(store_id)

    try:
        import requests
        resp = requests.post(f"{PRINTFUL_API_BASE}/orders",
                             json=payload, headers=headers, timeout=20)
        if resp.status_code == 400 and "external" in (resp.text or "").lower():
            payload.pop("external_id", None)
            resp = requests.post(f"{PRINTFUL_API_BASE}/orders",
                                 json=payload, headers=headers, timeout=20)
    except Exception as e:
        return None, f"request failed: {e}"

    if resp.status_code in (200, 201):
        try:
            order_id = (resp.json().get("result") or {}).get("id")
        except ValueError:
            order_id = None
        logger.info("Printful %s order created (id=%s)",
                    "CONFIRMED" if confirm else "DRAFT", order_id)
        return (order_id or "created"), ""

    err = f"HTTP {resp.status_code} — {(resp.text or '')[:300]}"
    logger.error("Printful rejected order: %s", err)
    return None, err


def _process_completed_session(request, session):
    """Fulfil a paid checkout.session.completed exactly once. `session` is a dict.

    Idempotent: a FulfilledOrder row (unique per session) guards against Stripe
    retries / manual resends creating duplicate Printful orders or emails. Every
    step is individually wrapped so nothing can bubble up to a 500.
    """
    session_id = session.get("id")
    metadata = session.get("metadata") or {}
    if session.get("payment_status") != "paid" or not session_id:
        return  # only fulfil confirmed-paid sessions

    kind = metadata.get("kind")
    email = _session_email(session) or ""
    user = None
    uid = metadata.get("user_id")
    if uid:
        user = User.objects.filter(pk=uid).first()
    pf_items = _pf_items_raw(metadata.get("pf_items"))   # stored raw [{v,q}] for retries
    recipient = _extract_recipient(session)
    payment_intent = session.get("payment_intent") if isinstance(session.get("payment_intent"), str) else ""

    # --- Idempotency gate: claim this session; bail if already fulfilled. ---
    try:
        record, created = FulfilledOrder.objects.get_or_create(
            session_id=session_id,
            defaults={
                "kind": kind or "",
                "user": user,
                "email": email,
                "amount_total": round((session.get("amount_total") or 0) / 100, 2),
                "pf_items": pf_items,
                "recipient": recipient,
                "payment_intent": payment_intent,
            },
        )
    except Exception:
        logger.exception("FulfilledOrder gate error for %s", session_id)
        return
    if not created:
        logger.info("Duplicate webhook for %s ignored (already fulfilled).", session_id)
        return

    # Digital fulfillment (course access, promo redemption, cart clear).
    try:
        _fulfill_session(session)
    except Exception:
        logger.exception("DB fulfillment error for session %s", session_id)

    # 1) Course purchase welcome email.
    if kind == "course":
        try:
            course = Course.objects.filter(pk=metadata.get("course_id")).first()
            if course:
                academy_emails.send_course_welcome(
                    email, course.title, _abs(request, "academy:dashboard"))
        except Exception:
            logger.exception("Course welcome email failed for session %s", session_id)

    # 2) Merch order: confirmation email + first Printful attempt. On failure the
    #    order stays queued (STATUS_PRINTFUL_FAILED) for the retry job, and an
    #    admin is alerted. The retry job stops the moment it succeeds.
    if kind in ("cart", "merch"):
        lines = _stripe_line_descriptions(session)
        order_id = None
        if pf_items:
            ext = payment_intent or ("peg-" + _hash_id(session_id))
            err = ""
            try:
                order_id, err = _create_printful_order(_printful_items(pf_items), recipient, ext)
            except Exception as e:
                err = str(e)
                logger.exception("Printful submission crashed for session %s", session_id)
            record.attempts = 1
            record.last_attempt_at = timezone.now()
            if order_id:
                record.printful_order_id = str(order_id)
                record.status = FulfilledOrder.STATUS_PROCESSED
            else:
                record.status = FulfilledOrder.STATUS_PRINTFUL_FAILED
                record.note = (err or "Printful order not created")[:255]
            try:
                record.save(update_fields=["printful_order_id", "status", "note",
                                           "attempts", "last_attempt_at", "updated_at"])
            except Exception:
                logger.exception("FulfilledOrder save failed for session %s", session_id)

        # Customer gets the normal confirmation on success, or an honest "we're on
        # it" note on failure (never a misleading receipt). Admin alerted on fail.
        try:
            if pf_items and not order_id:
                academy_emails.send_merch_issue(email, lines)
                academy_emails.send_admin_fulfillment_alert(
                    session_id, email, record.amount_total,
                    _abs(request, "admin:academy_fulfilledorder_changelist"))
            else:
                academy_emails.send_merch_confirmation(email, lines)
        except Exception:
            logger.exception("Merch email failed for session %s", session_id)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    stripe = _stripe()
    if not stripe:
        return HttpResponse(status=503)

    payload = request.body
    sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    # Verify the signature for security, but read the event from the raw JSON so
    # we operate on plain dicts regardless of the installed stripe version.
    try:
        if secret:
            stripe.Webhook.construct_event(payload, sig, secret)  # raises if invalid
        event = json.loads(payload.decode("utf-8"))
    except Exception as e:  # bad signature / unparseable body
        logger.warning("Stripe webhook verification/parse failed: %s", e)
        return HttpResponseBadRequest("invalid")

    # Never let processing raise — a 500 makes Stripe retry the event forever.
    try:
        if event.get("type") == "checkout.session.completed":
            session = (event.get("data") or {}).get("object") or {}
            _process_completed_session(request, session)
    except Exception:
        logger.exception("Webhook processing error")

    return HttpResponse(status=200)


@login_required
def checkout_success(request):
    """Stripe return URL — renders a thank-you / order-summary page.

    Also fulfils locally so the loop is testable without a configured webhook
    (idempotent with the webhook path). Does NOT send emails or submit Printful;
    those are webhook-only to avoid duplicates.
    """
    session_id = request.GET.get("session_id")
    stripe = _stripe()
    ctx = {
        "active_section": "store", "lines": [], "total": 0, "kind": None,
        "course": None, "email": None, "order_ref": None, "is_merch": False,
        "order_status": None,
    }
    if session_id and stripe:
        try:
            session = _as_dict(stripe.checkout.Session.retrieve(session_id))
            # Fulfil now if the webhook hasn't fired yet. Idempotent (FulfilledOrder
            # gate) so this never duplicates orders or emails.
            try:
                _process_completed_session(request, session)
            except Exception:
                logger.exception("success-path fulfillment error for %s", session_id)

            meta = session.get("metadata") or {}
            kind = meta.get("kind")
            if kind in ("cart", "merch"):
                cart_utils.clear_cart(request.session)
            record = FulfilledOrder.objects.filter(session_id=session_id).first()
            ctx.update({
                "kind": kind,
                "is_merch": kind in ("cart", "merch"),
                "email": (session.get("customer_details") or {}).get("email"),
                "lines": _stripe_line_descriptions(session),
                "total": round((session.get("amount_total") or 0) / 100, 2),
                "currency": (session.get("currency") or "usd").upper(),
                "order_ref": (session_id or "")[-12:],
                "order_status": record.status if record else "pending",
            })
            if kind == "course":
                ctx["course"] = Course.objects.filter(pk=meta.get("course_id")).first()
        except Exception as e:
            logger.error("checkout_success rendering error for %s: %s", session_id, e)
    return render(request, "academy/checkout_success.html", ctx)


@login_required
def checkout_cancel(request):
    messages.info(request, "Checkout cancelled — no charge was made.")
    return redirect("academy:storefront")


# ---------------------------------------------------------------------------
#  Token-protected task runner (a "poor-man's cron" for hosts without cron).
#  Point a free scheduler (cron-job.org, UptimeRobot, GitHub Actions) at:
#      https://<domain>/academy/tasks/retry-orders/?token=<TASK_RUNNER_TOKEN>
# ---------------------------------------------------------------------------
@csrf_exempt
def run_retry_orders(request):
    expected = getattr(settings, "TASK_RUNNER_TOKEN", "")
    token = request.GET.get("token") or request.META.get("HTTP_X_TASK_TOKEN", "")
    if not expected or not secrets.compare_digest(str(token), str(expected)):
        return HttpResponse(status=403)
    out = StringIO()
    try:
        # Small per-ping cap so a slow-Printful run can't exceed the request
        # timeout; the scheduler pings again in a few minutes to work the backlog.
        call_command("retry_failed_orders", limit=8, stdout=out, stderr=out)
    except Exception as e:
        logger.exception("Scheduled retry_failed_orders failed")
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    return JsonResponse({"ok": True, "output": out.getvalue()[-2000:]})


# ---------------------------------------------------------------------------
#  Store credits ("free items") — the worst-case remediation
# ---------------------------------------------------------------------------
def _available_credits(user):
    if not user or not user.is_authenticated:
        return StoreCredit.objects.none()
    return StoreCredit.objects.filter(user=user, status=StoreCredit.STATUS_AVAILABLE)


@login_required
def credits_view(request):
    credits = list(_available_credits(request.user))
    max_value = max((c.amount for c in credits), default=0)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    # Items you can claim: active, within your credit value, and unlocked for your level.
    eligible = [
        m for m in MerchItem.objects.filter(active=True)
        if m.price <= max_value and profile.current_level >= m.unlock_level
    ]
    return render(request, "academy/credits.html", {
        "credits": credits,
        "credit_count": len(credits),
        "max_value": max_value,
        "eligible": eligible,
        "active_section": "store",
    })


@login_required
def claim_free_view(request, slug):
    item = get_object_or_404(MerchItem, slug=slug, active=True)
    credit = _available_credits(request.user).filter(amount__gte=item.price).order_by("amount").first()
    if not credit:
        messages.error(request, "You don't have a credit that covers this item.")
        return redirect("academy:credits")

    colors, sizes, variants = _structure_variants(item)
    # Pre-fill shipping from the address on the original (failed) order, if any.
    prefill = (credit.source_order.recipient if credit.source_order else {}) or {}

    if request.method == "POST":
        recipient = {
            "name": (request.POST.get("name") or "").strip(),
            "address1": (request.POST.get("address1") or "").strip(),
            "address2": (request.POST.get("address2") or "").strip(),
            "city": (request.POST.get("city") or "").strip(),
            "state_code": (request.POST.get("state_code") or "").strip(),
            "country_code": (request.POST.get("country_code") or "").strip().upper(),
            "zip": (request.POST.get("zip") or "").strip(),
            "email": (request.POST.get("email") or credit.user.email or "").strip(),
        }
        phone = (request.POST.get("phone") or "").strip()
        if phone:
            recipient["phone"] = phone
        variant = _variant_from_item(item, (request.POST.get("variant_id") or "").strip())

        if item.variants and not variant:
            messages.error(request, "Please choose your options.")
        elif not _recipient_is_complete(recipient):
            messages.error(request, "Please fill in your full shipping address.")
        else:
            sync_vid = variant.get("id") if variant else None
            items = [{"sync_variant_id": sync_vid, "quantity": 1}] if sync_vid else []
            order_id, err = _create_printful_order(items, recipient, f"credit-{credit.id}")
            if order_id:
                credit.status = StoreCredit.STATUS_USED
                credit.used_at = timezone.now()
                credit.note = f"Claimed {item.name} — Printful order {order_id}"
                credit.save(update_fields=["status", "used_at", "note"])
                messages.success(request, "Your free item is on its way! We'll email tracking when it ships.")
                return redirect("main_site:account")
            else:
                logger.error("Free claim failed for credit %s: %s", credit.id, err)
                try:
                    academy_emails.send_admin_fulfillment_alert(
                        f"credit-{credit.id}", credit.user.email, credit.amount,
                        _abs(request, "admin:academy_storecredit_changelist"))
                except Exception:
                    pass
                messages.error(request, "We couldn't place that order — your credit is safe. "
                                        "Please try again or request a refund.")

    return render(request, "academy/claim_free.html", {
        "item": item, "credit": credit, "colors": colors, "sizes": sizes,
        "variants_json": variants, "prefill": prefill, "active_section": "store",
    })


@login_required
@require_POST
def request_refund_view(request, credit_id):
    credit = get_object_or_404(StoreCredit, pk=credit_id, user=request.user)
    if credit.status not in (StoreCredit.STATUS_AVAILABLE,):
        messages.info(request, "That credit can't be refunded.")
        return redirect("main_site:account")

    credit.status = StoreCredit.STATUS_REFUND_REQUESTED
    credit.save(update_fields=["status"])

    # Best-effort automatic Stripe refund of the original charge.
    refunded = False
    stripe = _stripe()
    if stripe and credit.payment_intent:
        try:
            stripe.Refund.create(payment_intent=credit.payment_intent)
            credit.status = StoreCredit.STATUS_REFUNDED
            credit.save(update_fields=["status"])
            refunded = True
        except Exception as e:
            logger.error("Auto-refund failed for credit %s: %s", credit.id, e)

    # Always let the team know (auto or manual).
    try:
        academy_emails.send_admin_refund_request(
            credit.id, credit.user.email, credit.amount, credit.payment_intent, refunded,
            _abs(request, "admin:academy_storecredit_changelist"))
    except Exception:
        logger.exception("Refund-request admin email failed for credit %s", credit.id)

    if refunded:
        messages.success(request, "Refund issued to your original payment method. "
                                  "It may take a few business days to appear.")
    else:
        messages.success(request, "Refund requested — our team will process it shortly.")
    return redirect("main_site:account")


# ---------------------------------------------------------------------------
#  Cart (session-based)
# ---------------------------------------------------------------------------
def _variant_from_item(item, variant_id):
    for v in (item.variants or []):
        if str(v.get("variant_id")) == str(variant_id) or str(v.get("id")) == str(variant_id):
            return v
    return None


@login_required
@require_POST
def cart_add(request):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    item = MerchItem.objects.filter(pk=request.POST.get("merch_id"), active=True).first()
    if not item:
        return JsonResponse({"ok": False, "error": "Item not found."}, status=404)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.current_level < item.unlock_level:
        msg = f"This unlocks at Level {item.unlock_level}. You're Level {profile.current_level}."
        if is_ajax:
            return JsonResponse({"ok": False, "error": msg}, status=403)
        messages.error(request, msg)
        return redirect("academy:merch_detail", slug=item.slug)

    variant_id = (request.POST.get("variant_id") or "").strip()
    variant = _variant_from_item(item, variant_id) if variant_id else None
    if item.variants and not variant:
        err = "Please choose your options first."
        if is_ajax:
            return JsonResponse({"ok": False, "error": err}, status=400)
        messages.error(request, err)
        return redirect("academy:merch_detail", slug=item.slug)

    try:
        qty = max(1, int(request.POST.get("qty", 1)))
    except (TypeError, ValueError):
        qty = 1

    color = variant.get("color", "") if variant else ""
    size = variant.get("size", "") if variant else ""
    image = (variant.get("image") if variant else "") or item.base_image_url
    unit_price = str(variant.get("price")) if variant else str(item.price)
    vid = variant.get("variant_id") if variant else 0
    # Printful sync variant id (per-store) — needed to fulfill the order.
    sync_vid = variant.get("id") if variant else None

    cart = cart_utils.get_cart(request.session)
    key = cart_utils.line_key(item.id, vid)
    line = cart.get(key) or {
        "merch_id": item.id, "slug": item.slug, "name": item.name, "variant_id": vid,
        "sync_variant_id": sync_vid, "color": color, "size": size,
        "unit_price": unit_price, "qty": 0, "image": image,
    }
    line["qty"] = int(line.get("qty", 0)) + qty
    cart[key] = line
    cart_utils.save_cart(request.session, cart)

    if is_ajax:
        return JsonResponse({
            "ok": True,
            "count": cart_utils.cart_count(cart),
            "total": cart_utils.cart_total(cart),
            "item": {"name": item.name, "color": color, "size": size, "image": image},
        })
    messages.success(request, f"Added {item.name} to your cart.")
    return redirect("academy:cart")


@login_required
@require_POST
def cart_update(request):
    key = request.POST.get("key")
    try:
        qty = int(request.POST.get("qty", 1))
    except (TypeError, ValueError):
        qty = 1
    cart = cart_utils.get_cart(request.session)
    if key in cart:
        if qty <= 0:
            del cart[key]
        else:
            cart[key]["qty"] = qty
        cart_utils.save_cart(request.session, cart)
    return redirect("academy:cart")


@login_required
@require_POST
def cart_remove(request):
    key = request.POST.get("key")
    cart = cart_utils.get_cart(request.session)
    if key in cart:
        del cart[key]
        cart_utils.save_cart(request.session, cart)
    return redirect("academy:cart")


def _user_valid_codes(user):
    """The logged-in user's currently-valid (unredeemed, unexpired) reward codes."""
    if not user or not user.is_authenticated:
        return []
    return [p for p in GeneratedPromoCode.objects.filter(user=user) if p.is_valid]


def _resolve_cart_codes(request, cart):
    """Validated {line_key: GeneratedPromoCode} from the session.

    Enforces: line must be in the cart, code must be the user's & valid, and each
    code may back at most one line (first assignment wins).
    """
    raw = request.session.get(CART_CODES_SESSION_KEY) or {}
    valid = {p.code_string: p for p in _user_valid_codes(request.user)}
    out, used = {}, set()
    for line_key, code in raw.items():
        if line_key in cart and code in valid and code not in used:
            out[line_key] = valid[code]
            used.add(code)
    return out


def _build_line_items(cart, pct_by_line=None):
    """Build Stripe line items, applying each assigned reward to exactly ONE unit
    of that line (split into a discounted qty-1 line + the full-price remainder).

    pct_by_line: {line_key: discount_percentage}. Returns (line_items, discount_cents).
    Discounts are computed here, so Stripe charges the exact total — never a
    whole-order discount.
    """
    pct_by_line = pct_by_line or {}
    items, discount_cents = [], 0

    def line(name, amount_cents, qty, image):
        pd = {"name": name[:250]}
        if image:
            pd["images"] = [image]
        return {"price_data": {"currency": settings.STRIPE_CURRENCY,
                               "product_data": pd, "unit_amount": amount_cents},
                "quantity": qty}

    for key, li in cart.items():
        qty = max(1, int(li.get("qty", 1)))
        unit_c = _money(li.get("unit_price", 0))
        opt = " / ".join(x for x in [li.get("color"), li.get("size")] if x)
        base_name = f"{li.get('name')} ({opt})" if opt else (li.get("name") or "Item")
        image = li.get("image")
        pct = pct_by_line.get(key)

        if pct:
            disc_c = max(0, round(unit_c * (100 - pct) / 100))
            items.append(line(f"{base_name} — {pct}% reward", disc_c, 1, image))
            discount_cents += unit_c - disc_c
            if qty - 1 > 0:
                items.append(line(base_name, unit_c, qty - 1, image))
        else:
            items.append(line(base_name, unit_c, qty, image))

    return items, discount_cents


@login_required
@require_POST
def cart_apply_code(request):
    """Assign (or clear) a reward code on a single cart line."""
    key = request.POST.get("key")
    code = (request.POST.get("code") or "").strip()
    cart = cart_utils.get_cart(request.session)
    raw = dict(request.session.get(CART_CODES_SESSION_KEY) or {})
    raw.pop(key, None)  # clear any existing assignment for this line

    if code:
        valid = {p.code_string for p in _user_valid_codes(request.user)}
        if key in cart and code in valid:
            # A code can only sit on one line — free it from any other line first.
            raw = {k: v for k, v in raw.items() if v != code}
            raw[key] = code
        else:
            messages.error(request, "That reward code can't be applied here.")
    request.session[CART_CODES_SESSION_KEY] = raw
    request.session.modified = True
    return redirect("academy:cart")


@login_required
def cart_view(request):
    cart = cart_utils.get_cart(request.session)
    code_map = _resolve_cart_codes(request, cart)
    # Persist the cleaned map (drops stale/invalid assignments).
    request.session[CART_CODES_SESSION_KEY] = {k: p.code_string for k, p in code_map.items()}
    request.session.modified = True

    user_codes = _user_valid_codes(request.user)
    assigned = {p.code_string for p in code_map.values()}
    pct_by_line = {k: p.discount_percentage for k, p in code_map.items()}
    _, discount_cents = _build_line_items(cart, pct_by_line)

    lines = []
    for li in cart_utils.cart_lines(cart):
        lk = li["key"]
        mine = code_map.get(lk)
        # Codes available to this line = not used elsewhere (its own stays listed).
        li["assigned_code"] = mine.code_string if mine else ""
        li["available_codes"] = [
            c for c in user_codes
            if c.code_string not in assigned or (mine and c.code_string == mine.code_string)
        ]
        if mine:
            unit = float(li.get("unit_price", 0) or 0)
            li["line_discount"] = round(unit * mine.discount_percentage / 100, 2)
            li["discount_pct"] = mine.discount_percentage
        lines.append(li)

    subtotal = cart_utils.cart_total(cart)
    discount = round(discount_cents / 100, 2)
    return render(request, "academy/cart.html", {
        "lines": lines,
        "subtotal": subtotal,
        "discount": discount,
        "total": round(subtotal - discount, 2),
        "has_codes": bool(user_codes),
        "code_count": len(user_codes),
        "active_section": "store",
    })


@login_required
@require_POST
def cart_checkout(request):
    cart = cart_utils.get_cart(request.session)
    if not cart:
        messages.info(request, "Your cart is empty.")
        return redirect("academy:storefront")

    stripe = _stripe()
    if not stripe:
        messages.error(request, "Payments aren't configured on the server yet.")
        return redirect("academy:cart")

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    # Re-enforce level gating for everything in the cart.
    for li in cart.values():
        item = MerchItem.objects.filter(pk=li.get("merch_id"), active=True).first()
        if item and profile.current_level < item.unlock_level:
            messages.error(request, f"{item.name} unlocks at Level {item.unlock_level}. "
                                    "Remove it to check out.")
            return redirect("academy:cart")

    code_map = _resolve_cart_codes(request, cart)
    pct_by_line = {k: p.discount_percentage for k, p in code_map.items()}
    line_items, _discount = _build_line_items(cart, pct_by_line)
    if not line_items:
        messages.info(request, "Your cart is empty.")
        return redirect("academy:storefront")

    metadata = {"kind": "cart", "user_id": str(request.user.id)}
    used_codes = [p.code_string for p in code_map.values()]
    if used_codes:
        metadata["promo_codes"] = ",".join(used_codes)[:480]
    # Items the webhook will submit to Printful for physical fulfillment.
    pf_items = _fulfillment_items(cart)
    if pf_items:
        metadata["pf_items"] = json.dumps(pf_items)[:480]

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            client_reference_id=str(request.user.id),
            line_items=line_items,
            metadata=metadata,
            # Collect a physical mailing address for Printful fulfillment.
            shipping_address_collection={"allowed_countries": MERCH_SHIP_COUNTRIES},
            phone_number_collection={"enabled": True},
            # No Stripe coupon / allow_promotion_codes: the reward is already
            # baked into the line items, so Stripe can't discount the whole order.
            success_url=_abs(request, "academy:checkout_success") + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=_abs(request, "academy:checkout_cancel"),
        )
        return redirect(session.url)
    except Exception as e:
        print(f"[academy] cart checkout error: {e}")
        messages.error(request, "Could not start checkout. Please try again.")
        return redirect("academy:cart")


# ---------------------------------------------------------------------------
#  Phase 5 — Certificate (HTML, A4 landscape, light/dark, print-to-PDF)
# ---------------------------------------------------------------------------
def certificate(request, cert_uuid):
    cert = get_object_or_404(IssuedCertificate, unique_uuid=cert_uuid)
    student = cert.user.get_full_name() or cert.user.username
    return render(request, "academy/certificate.html", {
        "cert": cert,
        "student_name": student.title() if student else "Student",
        "course_title": cert.certification_name,
        "issue_date": cert.date_issued,
        "verify_url": request.build_absolute_uri(
            reverse("academy:certificate", args=[cert.unique_uuid])),
    })


# ---------------------------------------------------------------------------
#  Phase 6 — Learner dashboard
# ---------------------------------------------------------------------------
@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    progresses = (UserCourseProgress.objects
                  .filter(user=request.user, purchased=True)
                  .select_related("course"))
    certificates = IssuedCertificate.objects.filter(user=request.user).select_related("course")
    achievements = Achievement.objects.filter(user=request.user)
    promos = [p for p in GeneratedPromoCode.objects.filter(user=request.user) if p.is_valid]

    # One-shot completion celebration data (set during _complete_course).
    completed = request.session.pop("academy_completed_course", None)
    if completed is not None:
        request.session.modified = True

    return render(request, "academy/dashboard.html", {
        "profile": profile,
        "progresses": progresses,
        "certificates": certificates,
        "achievements": achievements,
        "promo_codes": promos,
        "just_completed": completed,
        "active_section": "store",
    })

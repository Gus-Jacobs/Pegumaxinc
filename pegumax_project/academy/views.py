"""Academy views: storefront, guarded learning, Stripe checkout/webhook,
quiz evaluation + gamification, certificates, and the learner dashboard.
"""
import json
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .context_processors import LEVEL_UP_SESSION_KEY
from .markdown_lite import render_markdown
from .models import (
    Achievement,
    Course,
    CourseModule,
    GeneratedPromoCode,
    IssuedCertificate,
    MerchItem,
    UserCourseProgress,
    UserProfile,
    DEFAULT_ATTEMPTS,
    PROMO_VALID_DAYS,
    REWARD_DISCOUNT,
    SECOND_CHANCE_DISCOUNT,
)


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


# ---------------------------------------------------------------------------
#  Storefront (public browsing; buying/viewing requires auth)
# ---------------------------------------------------------------------------
def storefront(request):
    courses = Course.objects.filter(published=True)
    merch = MerchItem.objects.filter(active=True)
    owned = set()
    if request.user.is_authenticated:
        owned = set(
            UserCourseProgress.objects
            .filter(user=request.user, purchased=True)
            .values_list("course_id", flat=True)
        )
    return render(request, "academy/storefront.html", {
        "courses": courses,
        "merch_items": merch,
        "owned_course_ids": owned,
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

    # Sequential gating: you may view a module only if it's passed already or it
    # is the next one you're allowed to attempt.
    next_allowed = progress.next_module_number()
    already_passed = progress.has_passed(module.module_number)
    if not already_passed and module.module_number > next_allowed:
        messages.info(request, "Finish the earlier modules first to unlock this one.")
        return redirect("academy:lesson", slug=slug, module_number=next_allowed)

    return render(request, "academy/lesson.html", {
        "course": course,
        "module": module,
        "modules": modules,
        "progress": progress,
        "content_html": render_markdown(module.markdown_content),
        "quiz": module.quiz or {},
        "already_passed": already_passed,
        "is_final": module.module_number == course.final_module_number,
        "active_section": "store",
    })


# ---------------------------------------------------------------------------
#  Phase 4 — Quiz evaluation, XP, level-up, attempts, completion
# ---------------------------------------------------------------------------
@login_required
@require_POST
def submit_quiz(request, slug, module_number):
    course = get_object_or_404(Course, slug=slug, published=True)
    progress = UserCourseProgress.objects.filter(user=request.user, course=course).first()
    if not (progress and progress.purchased):
        return redirect("academy:course_detail", slug=slug)

    module = get_object_or_404(CourseModule, course=course, module_number=module_number)

    if progress.is_locked:
        messages.error(request, "This course is locked — retakes exhausted. "
                                "Re-purchase for a 50% second-chance discount.")
        return redirect("academy:course_detail", slug=slug)

    if progress.has_passed(module.module_number):
        messages.info(request, "You've already passed this module.")
        return redirect("academy:lesson", slug=slug, module_number=module_number)

    quiz = module.quiz or {}
    try:
        chosen = int(request.POST.get("answer", -1))
    except (TypeError, ValueError):
        chosen = -1
    correct_idx = int(quiz.get("answer", -1))

    if chosen == correct_idx and correct_idx >= 0:
        _handle_pass(request, progress, module, course)
    else:
        _handle_fail(request, progress, course)

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


def _handle_pass(request, progress, module, course):
    # Margin of success: cleaner runs (more retakes still in the tank) earn more.
    xp = 50 + 25 * max(0, progress.attempts_remaining)
    passed = list(progress.passed_modules or [])
    if module.module_number not in passed:
        passed.append(module.module_number)
    progress.passed_modules = sorted(passed)
    progress.save(update_fields=["passed_modules", "updated_at"])
    _award_xp(request, xp)
    messages.success(request, f"Correct! +{xp} XP for clearing “{module.title}”.")

    all_passed = progress.passed_count >= course.module_count
    is_final = module.module_number == course.final_module_number
    if is_final and all_passed and not progress.completed:
        _complete_course(request, progress, course)


def _handle_fail(request, progress, course):
    progress.attempts_remaining = max(0, progress.attempts_remaining - 1)
    progress.save(update_fields=["attempts_remaining", "updated_at"])
    if progress.attempts_remaining <= 0:
        messages.error(request, "Incorrect — and that was your last attempt. "
                                "This course is now locked. Re-purchase for a 50% "
                                "second-chance discount to reset your attempts.")
    else:
        messages.warning(request, f"Incorrect. {progress.attempts_remaining} "
                                  f"attempt(s) remaining before the course locks.")


def _complete_course(request, progress, course):
    total = course.module_count or 1
    progress.completed = True
    progress.final_score = int(round(100 * progress.passed_count / total))
    progress.completed_at = timezone.now()
    progress.save(update_fields=["completed", "final_score", "completed_at", "updated_at"])

    # Completion XP bonus (may itself trigger a level-up).
    _award_xp(request, 200)

    # Certificate
    cert, created = IssuedCertificate.objects.get_or_create(
        user=request.user, course=course,
        defaults={"certification_name": course.title},
    )

    # Achievement badge
    Achievement.objects.get_or_create(
        user=request.user, name=f"Completed: {course.title}",
        defaults={"description": f"Finished all {total} modules of {course.title}."},
    )

    # Phase 5 — reward promo code (50% off, tagged to the course domain, 30-day life)
    promo = _create_completion_promo(request.user, course)

    messages.success(
        request,
        f"🏆 Course complete! Your certificate is ready and you've unlocked a "
        f"{REWARD_DISCOUNT}% reward code: {promo.code_string}",
        extra_tags="course_complete",
    )
    request.session["academy_completed_course"] = {
        "title": course.title,
        "cert_uuid": str(cert.unique_uuid),
        "promo": promo.code_string,
    }
    request.session.modified = True


def _create_completion_promo(user, course):
    tag = course.domain_tag or "pegumax"
    code = f"{tag.upper().replace('-', '')[:10]}-{secrets.token_hex(3).upper()}"
    promo = GeneratedPromoCode.objects.create(
        user=user,
        code_string=code,
        discount_percentage=REWARD_DISCOUNT,
        target_tag=tag,
        expiration_date=timezone.now() + timedelta(days=PROMO_VALID_DAYS),
        active_status=True,
    )
    # Best-effort: mirror into Stripe so allow_promotion_codes accepts it natively.
    stripe = _stripe()
    if stripe:
        try:
            coupon = stripe.Coupon.create(
                percent_off=REWARD_DISCOUNT, duration="once",
                name=f"{course.title} reward",
            )
            pc = stripe.PromotionCode.create(
                coupon=coupon.id, code=code,
                expires_at=int((timezone.now() + timedelta(days=PROMO_VALID_DAYS)).timestamp()),
            )
            promo.stripe_promotion_code_id = pc.id
            promo.save(update_fields=["stripe_promotion_code_id"])
        except Exception as e:  # pragma: no cover - network/best effort
            print(f"[academy] Stripe promo creation skipped: {e}")
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
    item = get_object_or_404(MerchItem, pk=pk, active=True)
    stripe = _stripe()
    if not stripe:
        messages.error(request, "Payments aren't configured on the server yet.")
        return redirect("academy:storefront")
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            allow_promotion_codes=True,
            client_reference_id=str(request.user.id),
            line_items=[{
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "product_data": {"name": item.name, "description": item.description[:300]},
                    "unit_amount": _money(item.price),
                },
                "quantity": 1,
            }],
            metadata={"kind": "merch", "merch_id": str(item.id), "user_id": str(request.user.id)},
            success_url=_abs(request, "academy:checkout_success") + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=_abs(request, "academy:checkout_cancel"),
        )
        return redirect(session.url)
    except Exception as e:
        print(f"[academy] merch checkout error: {e}")
        messages.error(request, "Could not start checkout. Please try again.")
        return redirect("academy:storefront")


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


@csrf_exempt
@require_POST
def stripe_webhook(request):
    stripe = _stripe()
    if not stripe:
        return HttpResponse(status=503)

    payload = request.body
    sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    try:
        if secret:
            event = stripe.Webhook.construct_event(payload, sig, secret)
        else:
            # Dev fallback: trust the body when no signing secret is set.
            event = json.loads(payload.decode("utf-8"))
    except (ValueError, Exception) as e:  # invalid payload / signature
        print(f"[academy] webhook verify failed: {e}")
        return HttpResponseBadRequest("invalid")

    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        try:
            _fulfill_session(session)
        except Exception as e:
            print(f"[academy] fulfillment error: {e}")
            return HttpResponse(status=500)

    return HttpResponse(status=200)


@login_required
def checkout_success(request):
    """Stripe return URL. Also fulfils locally so the loop is testable without
    a configured webhook (idempotent with the webhook path)."""
    session_id = request.GET.get("session_id")
    stripe = _stripe()
    redirect_to = "academy:storefront"
    if session_id and stripe:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            _fulfill_session(session)
            meta = session.get("metadata") or {}
            if meta.get("kind") == "course" and meta.get("course_slug"):
                messages.success(request, "Payment received — your course is unlocked!")
                return redirect("academy:course_detail", slug=meta["course_slug"])
        except Exception as e:
            print(f"[academy] success fulfillment error: {e}")
    messages.success(request, "Thanks for your purchase!")
    return redirect(redirect_to)


@login_required
def checkout_cancel(request):
    messages.info(request, "Checkout cancelled — no charge was made.")
    return redirect("academy:storefront")


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

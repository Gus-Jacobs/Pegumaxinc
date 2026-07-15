"""Transactional emails for the academy app.

Uses Django's globally-configured EMAIL_BACKEND via send_mail, with HTML +
plain-text bodies rendered from templates in academy/templates/academy/emails/.
Every send is best-effort: rendering is wrapped in try/except and send_mail uses
fail_silently=True, so an email problem can never crash checkout or grading.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger("academy")


def _send(subject, template_base, context, to_email):
    if not to_email:
        return
    try:
        text_body = render_to_string(f"academy/emails/{template_base}.txt", context)
        html_body = render_to_string(f"academy/emails/{template_base}.html", context)
        send_mail(
            subject,
            text_body,
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
            [to_email],
            html_message=html_body,
            fail_silently=True,
        )
        logger.info("Sent '%s' email to %s", template_base, to_email)
    except Exception as e:  # rendering / unexpected errors must not bubble up
        logger.error("Email '%s' to %s failed: %s", template_base, to_email, e)


def send_course_welcome(to_email, course_title, dashboard_url):
    _send(
        f"Welcome to {course_title}!",
        "course_welcome",
        {"course_title": course_title, "dashboard_url": dashboard_url},
        to_email,
    )


def send_merch_confirmation(to_email, items):
    _send(
        "Your Pegumax order is confirmed 🎉",
        "merch_confirmation",
        {"items": items},
        to_email,
    )


def send_admin_fulfillment_alert(session_id, customer_email, amount, admin_url):
    """Alert the team that a PAID order failed to reach Printful and needs a
    manual fix. Sent to CONTACT_RECIPIENT_EMAIL. Best-effort / fail-silent."""
    to = getattr(settings, "CONTACT_RECIPIENT_EMAIL", None) \
        or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if not to:
        return
    subject = "⚠️ Pegumax order needs manual fulfillment"
    body = (
        "A customer paid but the Printful order was NOT created automatically.\n\n"
        f"Stripe session: {session_id}\n"
        f"Customer email: {customer_email or 'unknown'}\n"
        f"Amount: ${amount}\n\n"
        "The payment succeeded, so please create the order in Printful manually "
        "(or refund/credit the customer).\n"
        f"Details: {admin_url}\n"
    )
    try:
        send_mail(subject, body, getattr(settings, "DEFAULT_FROM_EMAIL", None),
                  [to], fail_silently=True)
        logger.info("Sent admin fulfillment alert for %s", session_id)
    except Exception as e:
        logger.error("Admin fulfillment alert failed for %s: %s", session_id, e)


def send_merch_issue(to_email, items):
    """Honest 'we hit a snag but we're on it' email — sent instead of the normal
    confirmation when the Printful order fails on first attempt."""
    _send(
        "We're finalizing your Pegumax order",
        "merch_issue",
        {"items": items},
        to_email,
    )


def send_free_item_granted(to_email, amount, account_url):
    """Told the customer we couldn't fulfil and credited them a free item."""
    _send(
        "About your Pegumax order — we've made it right",
        "free_item_granted",
        {"amount": amount, "account_url": account_url},
        to_email,
    )


def send_admin_refund_request(credit_id, customer_email, amount, payment_intent,
                              auto_refunded, admin_url):
    """Tell the team a customer requested a refund of a store credit."""
    to = getattr(settings, "CONTACT_RECIPIENT_EMAIL", None) \
        or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if not to:
        return
    subject = ("✅ Refund auto-issued" if auto_refunded else "⚠️ Refund requested — action needed")
    body = (
        f"Store credit #{credit_id} refund {'was auto-issued via Stripe' if auto_refunded else 'was REQUESTED'}.\n\n"
        f"Customer: {customer_email or 'unknown'}\n"
        f"Amount: ${amount}\n"
        f"Stripe payment_intent: {payment_intent or 'unknown'}\n\n"
        + ("No action needed.\n" if auto_refunded else
           "Please issue the refund in Stripe (search the payment_intent above).\n")
        + f"Details: {admin_url}\n"
    )
    try:
        send_mail(subject, body, getattr(settings, "DEFAULT_FROM_EMAIL", None),
                  [to], fail_silently=True)
    except Exception as e:
        logger.error("Refund-request admin email failed for credit %s: %s", credit_id, e)


def send_course_completion(to_email, course_title, score, certificate_url,
                           promo_code, discount, store_url):
    _send(
        f"You passed {course_title}! 🎓",
        "course_completion",
        {
            "course_title": course_title,
            "score": score,
            "certificate_url": certificate_url,
            "promo_code": promo_code,
            "discount": discount,
            "store_url": store_url,
        },
        to_email,
    )

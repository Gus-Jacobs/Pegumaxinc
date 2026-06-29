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

from django.urls import path

from . import views

app_name = "academy"

urlpatterns = [
    path("", views.storefront, name="storefront"),

    # Store legal pages (store/academy only — distinct from the main site policy)
    path("privacy/", views.store_privacy, name="privacy"),
    path("terms/", views.store_terms, name="terms"),
    path("returns/", views.store_returns, name="returns"),

    # Merch product detail
    path("merch/<slug:slug>/", views.merch_detail, name="merch_detail"),

    # Learning
    path("course/<slug:slug>/", views.course_detail, name="course_detail"),
    path("course/<slug:slug>/module/<int:module_number>/", views.lesson, name="lesson"),
    path("course/<slug:slug>/module/<int:module_number>/quiz/", views.submit_quiz, name="submit_quiz"),

    # Checkout
    path("checkout/course/<slug:slug>/", views.checkout_course, name="checkout_course"),
    path("checkout/merch/<int:pk>/", views.checkout_merch, name="checkout_merch"),
    path("checkout/success/", views.checkout_success, name="checkout_success"),
    path("checkout/cancel/", views.checkout_cancel, name="checkout_cancel"),
    path("webhook/stripe/", views.stripe_webhook, name="stripe_webhook"),

    # Cart
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/remove/", views.cart_remove, name="cart_remove"),
    path("cart/apply-code/", views.cart_apply_code, name="cart_apply_code"),
    path("cart/checkout/", views.cart_checkout, name="cart_checkout"),

    # Staff: refresh Printful products from the site's own admin/account screen
    path("admin/sync-printful/", views.admin_sync_printful, name="admin_sync_printful"),

    # Token-protected task runner (external free scheduler pings this)
    path("tasks/retry-orders/", views.run_retry_orders, name="run_retry_orders"),

    # Store credits ("free items") — worst-case remediation
    path("credits/", views.credits_view, name="credits"),
    path("credits/claim/<slug:slug>/", views.claim_free_view, name="claim_free"),
    path("credits/refund/<int:credit_id>/", views.request_refund_view, name="request_refund"),

    # Certificate + verification + dashboard
    path("certificate/<uuid:cert_uuid>/", views.certificate, name="certificate"),
    # Public verification path (used by the LinkedIn "Add to Profile" certUrl).
    path("verify/<uuid:cert_uuid>/", views.certificate, name="verify"),
    path("dashboard/", views.dashboard, name="dashboard"),
]

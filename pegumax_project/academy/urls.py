from django.urls import path

from . import views

app_name = "academy"

urlpatterns = [
    path("", views.storefront, name="storefront"),

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

    # Certificate + dashboard
    path("certificate/<uuid:cert_uuid>/", views.certificate, name="certificate"),
    path("dashboard/", views.dashboard, name="dashboard"),
]

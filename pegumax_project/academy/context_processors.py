"""Site-wide gamification context.

Exposes the logged-in user's academy profile and a one-shot ``level_up`` flag
(popped from the session) so the base template can fire the global level-up
modal + confetti on whatever page the user happens to be viewing.
"""
from . import cart as cart_utils
from .models import StoreCredit, UserProfile

LEVEL_UP_SESSION_KEY = "academy_level_up"


def gamification(request):
    profile = None
    level_up = None
    free_items = 0
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        profile = UserProfile.objects.filter(user=user).first()
        # Pop so the celebration fires exactly once.
        level_up = request.session.pop(LEVEL_UP_SESSION_KEY, None)
        if level_up is not None:
            request.session.modified = True
        # "Free items" indicator — only meaningful when > 0.
        free_items = StoreCredit.objects.filter(
            user=user, status=StoreCredit.STATUS_AVAILABLE).count()

    cart = cart_utils.get_cart(request.session)
    return {
        "academy_profile": profile,
        "academy_level_up": level_up,
        "cart_count": cart_utils.cart_count(cart),
        "cart_total": cart_utils.cart_total(cart),
        "free_items_count": free_items,
    }

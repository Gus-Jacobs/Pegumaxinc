"""Site-wide gamification context.

Exposes the logged-in user's academy profile and a one-shot ``level_up`` flag
(popped from the session) so the base template can fire the global level-up
modal + confetti on whatever page the user happens to be viewing.
"""
from . import cart as cart_utils
from .models import StoreCredit, UserProfile

LEVEL_UP_SESSION_KEY = "academy_level_up"


def gamification(request):
    """Runs on every page — must NEVER raise, or it takes the whole page (and the
    error page) down with it. All DB/session access is guarded."""
    profile = None
    level_up = None
    free_items = 0
    cart = {}
    session = getattr(request, "session", None)
    user = getattr(request, "user", None)

    try:
        if user is not None and user.is_authenticated:
            profile = UserProfile.objects.filter(user=user).first()
            if session is not None:
                level_up = session.pop(LEVEL_UP_SESSION_KEY, None)  # fire once
                if level_up is not None:
                    session.modified = True
            free_items = StoreCredit.objects.filter(
                user=user, status=StoreCredit.STATUS_AVAILABLE).count()
    except Exception:
        pass  # never break the page over the gamification badge

    try:
        if session is not None:
            cart = cart_utils.get_cart(session)
    except Exception:
        cart = {}

    return {
        "academy_profile": profile,
        "academy_level_up": level_up,
        "cart_count": cart_utils.cart_count(cart),
        "cart_total": cart_utils.cart_total(cart),
        "free_items_count": free_items,
    }

"""Site-wide gamification context.

Exposes the logged-in user's academy profile and a one-shot ``level_up`` flag
(popped from the session) so the base template can fire the global level-up
modal + confetti on whatever page the user happens to be viewing.
"""
from .models import UserProfile

LEVEL_UP_SESSION_KEY = "academy_level_up"


def gamification(request):
    profile = None
    level_up = None
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        profile = UserProfile.objects.filter(user=user).first()
        # Pop so the celebration fires exactly once.
        level_up = request.session.pop(LEVEL_UP_SESSION_KEY, None)
        if level_up is not None:
            request.session.modified = True
    return {"academy_profile": profile, "academy_level_up": level_up}

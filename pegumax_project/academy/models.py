"""Academy data layer.

Holds the e-commerce catalogue (courses + merch), the automated course
content (modules + quizzes), purchase/progress tracking, certification, promo
rewards, and the gamification layer (XP / levels / achievements).

Tags are stored as a simple comma-separated CharField rather than a Postgres
ArrayField so the schema stays portable across the SQLite used for local dev
and the Neon PostgreSQL used in production.
"""
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
#  Gamification tuning knobs (kept here so views/commands share one source).
# ---------------------------------------------------------------------------
DEFAULT_ATTEMPTS = 2          # 1 initial attempt + 1 retake per the spec.
SECOND_CHANCE_DISCOUNT = 50   # % off a re-purchase of a locked course.
REWARD_DISCOUNT = 50          # % off the completion promo code.
PROMO_VALID_DAYS = 30


def level_for_xp(total_xp: int) -> int:
    """Return the level for a given XP total.

    Uses a gently rising triangular curve: level N is reached at
    100 * (N-1) * N / 2 XP  ->  L2@100, L3@300, L4@600, L5@1000 ...
    """
    level = 1
    while total_xp >= 100 * level * (level + 1) // 2:
        level += 1
    return level


def xp_for_level(level: int) -> int:
    """Cumulative XP required to *reach* the given level."""
    if level <= 1:
        return 0
    n = level - 1
    return 100 * n * (n + 1) // 2


# ---------------------------------------------------------------------------
#  Catalogue
# ---------------------------------------------------------------------------
class MerchItem(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    base_image_url = models.URLField(blank=True)
    # Comma-separated domain tags mapping merch to course domains.
    tags = models.CharField(
        max_length=255, blank=True,
        help_text="Comma-separated domain tags, e.g. 'flutter,cybersecurity'.",
    )
    # Optional pre-created Stripe price; falls back to inline price_data.
    price_id = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    summary = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=49)
    # Stripe product/price mapping (optional — inline price_data is the fallback).
    price_id = models.CharField(max_length=120, blank=True)
    # Domain tag used for merch mapping + completion promo codes.
    domain_tag = models.CharField(max_length=60, blank=True)
    image_url = models.URLField(blank=True)
    source_file = models.CharField(max_length=200, blank=True)
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def module_count(self):
        return self.modules.count()

    @property
    def final_module_number(self):
        agg = self.modules.aggregate(m=models.Max("module_number"))
        return agg["m"] or 0


class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    module_number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    markdown_content = models.TextField(blank=True)
    # {"question": str, "options": [str, ...], "answer": int}
    quiz = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["course", "module_number"]
        unique_together = ("course", "module_number")

    def __str__(self):
        return f"{self.course.title} · M{self.module_number}: {self.title}"


# ---------------------------------------------------------------------------
#  Purchases & progress
# ---------------------------------------------------------------------------
class UserCourseProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="course_progress")
    course = models.ForeignKey(Course, on_delete=models.CASCADE,
                               related_name="progress_records")
    purchased = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    final_score = models.PositiveIntegerField(default=0)
    attempts_remaining = models.IntegerField(default=DEFAULT_ATTEMPTS)
    # Module numbers the user has already passed (drives sequential unlock + score).
    passed_modules = models.JSONField(default=list, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-updated_at"]
        verbose_name_plural = "User course progress"

    def __str__(self):
        return f"{self.user.username} · {self.course.title}"

    @property
    def is_locked(self):
        """A course locks once retakes are exhausted and it isn't finished."""
        return self.attempts_remaining <= 0 and not self.completed

    @property
    def passed_count(self):
        return len(self.passed_modules or [])

    @property
    def progress_percent(self):
        total = self.course.module_count or 1
        return int(round(100 * self.passed_count / total))

    def has_passed(self, module_number: int) -> bool:
        return module_number in (self.passed_modules or [])

    def next_module_number(self):
        """Lowest module number the user is allowed to attempt next."""
        passed = set(self.passed_modules or [])
        for m in self.course.modules.values_list("module_number", flat=True):
            if m not in passed:
                return m
        return self.course.final_module_number


class IssuedCertificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="certificates")
    unique_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    certification_name = models.CharField(max_length=255)
    date_issued = models.DateTimeField(auto_now_add=True)
    verify_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-date_issued"]

    def __str__(self):
        return f"{self.certification_name} · {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.verify_hash:
            import hashlib
            raw = f"{self.unique_uuid}:{self.user_id}:{self.certification_name}"
            self.verify_hash = hashlib.sha256(raw.encode()).hexdigest()[:32]
        super().save(*args, **kwargs)


class GeneratedPromoCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             null=True, blank=True, related_name="promo_codes")
    code_string = models.CharField(max_length=40, unique=True)
    discount_percentage = models.PositiveIntegerField(default=REWARD_DISCOUNT)
    target_tag = models.CharField(max_length=60, blank=True)
    expiration_date = models.DateTimeField()
    active_status = models.BooleanField(default=True)
    # Best-effort link to the matching Stripe promotion code, if created.
    stripe_promotion_code_id = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code_string} ({self.discount_percentage}% off {self.target_tag})"

    def save(self, *args, **kwargs):
        if not self.expiration_date:
            self.expiration_date = timezone.now() + timedelta(days=PROMO_VALID_DAYS)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return self.active_status and self.expiration_date > timezone.now()


# ---------------------------------------------------------------------------
#  Gamification
# ---------------------------------------------------------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="academy_profile")
    total_xp = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} · L{self.current_level} ({self.total_xp} XP)"

    def add_xp(self, amount: int):
        """Add XP and recompute level. Returns (leveled_up: bool, new_level: int)."""
        self.total_xp = max(0, self.total_xp + int(amount))
        new_level = level_for_xp(self.total_xp)
        leveled_up = new_level > self.current_level
        self.current_level = new_level
        self.save(update_fields=["total_xp", "current_level"])
        return leveled_up, new_level

    @property
    def xp_into_level(self):
        return self.total_xp - xp_for_level(self.current_level)

    @property
    def xp_to_next_level(self):
        return xp_for_level(self.current_level + 1) - xp_for_level(self.current_level)

    @property
    def level_progress_percent(self):
        span = self.xp_to_next_level or 1
        return max(0, min(100, int(round(100 * self.xp_into_level / span))))


class Achievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="achievements")
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    date_earned = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_earned"]

    def __str__(self):
        return f"{self.name} · {self.user.username}"

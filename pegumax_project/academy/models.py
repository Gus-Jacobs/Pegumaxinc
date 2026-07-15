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
PASS_THRESHOLD = 70           # Aggregate course score (%) required to pass.
COURSE_PRICE = 12             # Flat course price (USD) — drives the bundle play.

# Gamified "Developer Tier" → minimum level required to reach that tier.
# Dev 1: levels 1-4, Dev 2: levels 5-9, Dev 3: level 10+.
TIER_MIN_LEVELS = {1: 1, 2: 5, 3: 10}
MAX_DEV_TIER = max(TIER_MIN_LEVELS)


def dev_tier_for_level(level: int) -> int:
    """Map a level to its Developer Tier (highest tier whose floor it meets)."""
    tier = 1
    for t, min_level in sorted(TIER_MIN_LEVELS.items()):
        if level >= min_level:
            tier = t
    return tier


def min_level_for_tier(tier: int) -> int:
    """Lowest level that unlocks the given Developer Tier."""
    return TIER_MIN_LEVELS.get(int(tier), 1)


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
    slug = models.SlugField(max_length=220, unique=True, null=True, blank=True)
    # Description may contain Markdown/HTML (rendered on the product page).
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    base_image_url = models.URLField(blank=True, max_length=500)
    # Comma-separated domain tags mapping merch to course domains.
    tags = models.CharField(
        max_length=255, blank=True,
        help_text="Comma-separated domain tags, e.g. 'flutter,cybersecurity'.",
    )
    # Free-text product type used by the ?type= storefront filter (e.g. 'hoodie').
    product_type = models.CharField(max_length=60, blank=True)
    # Gamification: minimum Developer Tier required to purchase.
    required_dev_tier = models.PositiveIntegerField(default=1)
    # Minimum account level required to purchase. Auto-derived from a
    # "Developer N ..." naming convention by sync_printful; 0 = no level gate.
    required_level = models.PositiveIntegerField(default=0)
    # --- Printful sync ---
    printful_sync_id = models.CharField(max_length=120, blank=True, db_index=True)
    # [{ "id", "name", "size", "color", "price", "image" }, ...]
    variants = models.JSONField(default=list, blank=True)
    # Optional pre-created Stripe price; falls back to inline price_data.
    price_id = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.name)[:200] or "item"
            slug = base
            i = 2
            while MerchItem.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
            # update_or_create() passes update_fields on the update path; make
            # sure the freshly-generated slug is actually persisted.
            uf = kwargs.get("update_fields")
            if uf is not None and "slug" not in uf:
                kwargs["update_fields"] = list(uf) + ["slug"]
        super().save(*args, **kwargs)

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def name_level(self):
        """Parse a required level from a 'Developer N ...' product name (0 = none)."""
        import re
        m = re.search(r"developer\s+(\d+)", (self.name or "").lower())
        return int(m.group(1)) if m else 0

    @property
    def unlock_level(self):
        """Account level required to buy this item (always >= 1).

        Highest of: the explicit required_level, the level parsed from the name,
        and the floor of any required Developer Tier.
        """
        candidates = [self.required_level or 0, self.name_level]
        if self.required_dev_tier and self.required_dev_tier > 1:
            candidates.append(min_level_for_tier(self.required_dev_tier))
        return max(candidates) or 1

    # Back-compat alias used by older templates/views.
    @property
    def min_level_required(self):
        return self.unlock_level

    def is_unlocked_for_level(self, level: int) -> bool:
        return int(level or 1) >= self.unlock_level

    def is_unlocked_for(self, profile) -> bool:
        """True if the given UserProfile's level meets the unlock level."""
        level = profile.current_level if profile else 1
        return self.is_unlocked_for_level(level)


class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    summary = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=COURSE_PRICE)
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
    # Module numbers answered correctly this attempt (the running correct tally).
    passed_modules = models.JSONField(default=list, blank=True)
    # Every module the student has submitted an answer for this attempt — drives
    # sequential progress regardless of whether the answer was right or wrong.
    answered_modules = models.JSONField(default=list, blank=True)
    # Per-module correctness this attempt: {"<module_number>": true/false}.
    module_results = models.JSONField(default=dict, blank=True)
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
        """Number of modules answered correctly this attempt (the correct tally)."""
        return len(self.passed_modules or [])

    @property
    def answered_count(self):
        return len(self.answered_modules or [])

    @property
    def correct_count(self):
        """Alias for the running correct tally used in aggregate grading."""
        return self.passed_count

    @property
    def current_score(self):
        """Aggregate score so far: correct / total modules * 100."""
        total = self.course.module_count or 1
        return int(round(100 * self.passed_count / total))

    @property
    def progress_percent(self):
        """How far through the course the student is (answered, not correct)."""
        total = self.course.module_count or 1
        return int(round(100 * self.answered_count / total))

    def has_passed(self, module_number: int) -> bool:
        return module_number in (self.passed_modules or [])

    def has_answered(self, module_number: int) -> bool:
        return module_number in (self.answered_modules or [])

    def result_for(self, module_number: int):
        """True/False if answered, else None."""
        return (self.module_results or {}).get(str(module_number))

    def reset_attempt(self):
        """Clear per-attempt answers so the student can retake the whole course."""
        self.passed_modules = []
        self.answered_modules = []
        self.module_results = {}

    def next_module_number(self):
        """Lowest module number the student hasn't answered yet this attempt."""
        answered = set(self.answered_modules or [])
        for m in self.course.modules.values_list("module_number", flat=True):
            if m not in answered:
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
    # Single-use redemption tracking (mirrors Stripe max_redemptions=1).
    redeemed = models.BooleanField(default=False)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    # Best-effort link to the matching Stripe promotion code, if created.
    stripe_promotion_code_id = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        state = " [redeemed]" if self.redeemed else ""
        return f"{self.code_string} ({self.discount_percentage}% off {self.target_tag}){state}"

    def save(self, *args, **kwargs):
        if not self.expiration_date:
            self.expiration_date = timezone.now() + timedelta(days=PROMO_VALID_DAYS)
        super().save(*args, **kwargs)

    def mark_redeemed(self):
        if not self.redeemed:
            self.redeemed = True
            self.redeemed_at = timezone.now()
            self.save(update_fields=["redeemed", "redeemed_at"])

    @property
    def is_valid(self):
        """Valid = active, not yet redeemed (single-use), and unexpired."""
        return (self.active_status and not self.redeemed
                and self.expiration_date > timezone.now())


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

    @property
    def dev_tier(self):
        """Gamified Developer Tier derived from the current level."""
        return dev_tier_for_level(self.current_level)

    @property
    def dev_tier_label(self):
        return f"Dev {self.dev_tier}"


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


class FulfilledOrder(models.Model):
    """One row per Stripe Checkout Session we've fulfilled.

    Guarantees the webhook fulfils each session exactly once (idempotency) and
    carries the data a background job needs to retry a failed Printful order
    without the original web request.
    """
    STATUS_PROCESSED = "processed"            # done (digital, or Printful order placed)
    STATUS_PRINTFUL_FAILED = "printful_failed"  # paid but Printful rejected — retry queue
    STATUS_CREDITED = "credited"              # retries exhausted → store credit granted

    session_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name="fulfilled_orders")
    kind = models.CharField(max_length=20, blank=True)          # course | cart | merch
    printful_order_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=30, default=STATUS_PROCESSED)
    email = models.EmailField(blank=True)
    amount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Data needed to retry a physical order out-of-band (no web request).
    pf_items = models.JSONField(default=list, blank=True)       # [{"v": sync_variant_id, "q": qty}]
    recipient = models.JSONField(default=dict, blank=True)      # Printful recipient block
    payment_intent = models.CharField(max_length=120, blank=True)  # for refunds / external_id
    attempts = models.PositiveIntegerField(default=0)           # Printful submission attempts
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.session_id} · {self.status}"


class StoreCredit(models.Model):
    """A 'free item' credit granted when an order can't be fulfilled after retries.

    Worth what the customer paid; redeemable for any item at or below that value
    (all items in a category share a price, so this maps cleanly to 'a free tee').
    """
    STATUS_AVAILABLE = "available"
    STATUS_USED = "used"
    STATUS_REFUND_REQUESTED = "refund_requested"
    STATUS_REFUNDED = "refunded"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="store_credits")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default=STATUS_AVAILABLE)
    source_order = models.ForeignKey(FulfilledOrder, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="credits")
    payment_intent = models.CharField(max_length=120, blank=True)  # to refund the original charge
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"${self.amount} credit · {self.user} · {self.status}"

    @property
    def is_available(self):
        return self.status == self.STATUS_AVAILABLE

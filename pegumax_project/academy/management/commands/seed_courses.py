"""Seed the Course / CourseModule tables from the syllabus blueprints.

Loops every ``*_syllabus.md`` file in the ``Courses/`` directory, generates
the full 10-module lesson content (per ``Courses/schema.md``) and writes it
into the database. Idempotent: re-running updates existing courses in place.

Usage:
    python manage.py seed_courses
    python manage.py seed_courses --fresh   # wipe academy course data first
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from academy import course_content as cc
from academy.models import Course, CourseModule, MerchItem, COURSE_PRICE


def _courses_dir() -> Path:
    return Path(settings.BASE_DIR) / "Courses"


# A small starter merch catalogue mapped to course domains, with Developer
# Tier gating to demonstrate the gamified unlock (Printful sync replaces these).
SEED_MERCH = [
    {"name": "Hacker Sticker Pack", "price": 9, "product_type": "sticker",
     "description": "Vinyl sticker set for laptops and water bottles.",
     "tags": "pentest,cybersecurity,unix", "required_dev_tier": 1, "base_image_url": ""},
    {"name": "Prompt Engineer Mug", "price": 16, "product_type": "mug",
     "description": "Ceramic mug for the AI-leverage maximalists.",
     "tags": "ai-coding,python-ai,local-ai,machine-learning", "required_dev_tier": 1, "base_image_url": ""},
    {"name": "Pegumax Builder Tee", "price": 28, "product_type": "tee",
     "description": "Soft cotton tee for the build-it-yourself crowd.",
     "tags": "flutter,electron,csharp", "required_dev_tier": 2, "base_image_url": ""},
    {"name": "Local-First Hoodie", "price": 54, "product_type": "hoodie",
     "description": "Heavyweight hoodie — own your stack, own your software. Dev Tier 3 flex.",
     "tags": "django,system-design,sql", "required_dev_tier": 3, "base_image_url": ""},
]


class Command(BaseCommand):
    help = "Generate and seed all courses + modules from the Courses/ syllabi."

    def add_arguments(self, parser):
        parser.add_argument("--fresh", action="store_true",
                            help="Delete existing academy course data before seeding.")
        parser.add_argument("--demo-merch", action="store_true",
                            help="Also seed placeholder demo merch (off by default; "
                                 "real merch comes from `sync_printful`).")

    @transaction.atomic
    def handle(self, *args, **opts):
        cdir = _courses_dir()
        if not cdir.exists():
            self.stderr.write(self.style.ERROR(f"Courses directory not found: {cdir}"))
            return

        if opts["fresh"]:
            CourseModule.objects.all().delete()
            Course.objects.all().delete()
            self.stdout.write(self.style.WARNING("Wiped existing Course / CourseModule rows."))

        syllabi = sorted(cdir.glob("*_syllabus.md"))
        if not syllabi:
            self.stderr.write(self.style.ERROR("No *_syllabus.md files found."))
            return

        total_modules = 0
        for path in syllabi:
            stem = path.stem
            meta = cc.meta_for(stem)
            parsed = cc.parse_syllabus(path)
            slug = slugify(parsed["title"])[:200] or slugify(stem)

            course, _ = Course.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": parsed["title"],
                    "summary": parsed["subtitle"] or f"A practical, ship-first course: {parsed['title']}.",
                    # Flat $12 across the catalogue — the bundle play: buy a course,
                    # earn 50% off matching merch.
                    "price": COURSE_PRICE,
                    "domain_tag": meta["tag"],
                    "source_file": path.name,
                    "published": True,
                },
            )

            modules = parsed["modules"]
            kept_numbers = []
            for module in modules:
                md = cc.build_module_markdown(module, meta["lang"])
                quiz = cc.build_quiz(module, modules)
                CourseModule.objects.update_or_create(
                    course=course,
                    module_number=module["number"],
                    defaults={"title": module["title"], "markdown_content": md, "quiz": quiz},
                )
                kept_numbers.append(module["number"])
                total_modules += 1

            # Drop any stale modules no longer in the syllabus.
            course.modules.exclude(module_number__in=kept_numbers).delete()
            self.stdout.write(self.style.SUCCESS(
                f"  [ok] {course.title}  [{meta['tag']}]  - {len(kept_numbers)} modules"))

        if opts["demo_merch"]:
            for item in SEED_MERCH:
                MerchItem.objects.update_or_create(
                    name=item["name"],
                    defaults={
                        "description": item["description"],
                        "price": item["price"],
                        "tags": item["tags"],
                        "product_type": item.get("product_type", ""),
                        "required_dev_tier": item.get("required_dev_tier", 1),
                        "base_image_url": item["base_image_url"],
                        "active": True,
                    },
                )
            self.stdout.write(self.style.SUCCESS(f"  [ok] Seeded {len(SEED_MERCH)} merch items"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {len(syllabi)} courses, {total_modules} modules seeded."))

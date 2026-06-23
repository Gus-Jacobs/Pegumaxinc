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
from academy.models import Course, CourseModule, MerchItem


def _courses_dir() -> Path:
    return Path(settings.BASE_DIR) / "Courses"


# A small starter merch catalogue mapped to course domains.
SEED_MERCH = [
    {"name": "Pegumax Builder Tee", "price": 28,
     "description": "Soft cotton tee for the build-it-yourself crowd.",
     "tags": "flutter,electron,csharp", "base_image_url": ""},
    {"name": "Local-First Hoodie", "price": 54,
     "description": "Heavyweight hoodie — own your stack, own your software.",
     "tags": "django,system-design,sql", "base_image_url": ""},
    {"name": "Hacker Sticker Pack", "price": 9,
     "description": "Vinyl sticker set for laptops and water bottles.",
     "tags": "pentest,cybersecurity,unix", "base_image_url": ""},
    {"name": "Prompt Engineer Mug", "price": 16,
     "description": "Ceramic mug for the AI-leverage maximalists.",
     "tags": "ai-coding,python-ai,local-ai,machine-learning", "base_image_url": ""},
]


class Command(BaseCommand):
    help = "Generate and seed all courses + modules from the Courses/ syllabi."

    def add_arguments(self, parser):
        parser.add_argument("--fresh", action="store_true",
                            help="Delete existing academy course data before seeding.")
        parser.add_argument("--no-merch", action="store_true",
                            help="Skip seeding the starter merch catalogue.")

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
                    "price": meta["price"],
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

        if not opts["no_merch"]:
            for item in SEED_MERCH:
                MerchItem.objects.update_or_create(
                    name=item["name"],
                    defaults={
                        "description": item["description"],
                        "price": item["price"],
                        "tags": item["tags"],
                        "base_image_url": item["base_image_url"],
                        "active": True,
                    },
                )
            self.stdout.write(self.style.SUCCESS(f"  [ok] Seeded {len(SEED_MERCH)} merch items"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {len(syllabi)} courses, {total_modules} modules seeded."))

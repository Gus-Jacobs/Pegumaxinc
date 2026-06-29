from django.contrib import admin, messages
from django.core.management import call_command
from django.shortcuts import redirect
from django.urls import path
from io import StringIO

from .models import (
    Achievement,
    Course,
    CourseModule,
    GeneratedPromoCode,
    IssuedCertificate,
    MerchItem,
    UserCourseProgress,
    UserProfile,
)


class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 0
    fields = ("module_number", "title")
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "domain_tag", "price", "module_count", "published")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "slug", "domain_tag")
    inlines = [CourseModuleInline]


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ("course", "module_number", "title")
    list_filter = ("course",)
    search_fields = ("title",)


@admin.register(MerchItem)
class MerchItemAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "product_type", "required_level", "active",
                    "printful_sync_id")
    list_filter = ("active", "product_type", "required_level")
    search_fields = ("name", "tags", "printful_sync_id")
    change_list_template = "admin/academy/merchitem/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [path("sync-printful/", self.admin_site.admin_view(self.sync_printful_view),
                       name="academy_merchitem_sync_printful")]
        return custom + urls

    def sync_printful_view(self, request):
        """Run the sync_printful management command from the admin."""
        out = StringIO()
        try:
            call_command("sync_printful", stdout=out, stderr=out)
            summary = out.getvalue().strip().splitlines()[-1] if out.getvalue().strip() else "Done."
            self.message_user(request, f"Printful sync complete. {summary}", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Printful sync failed: {e}", messages.ERROR)
        return redirect("admin:academy_merchitem_changelist")


@admin.register(UserCourseProgress)
class UserCourseProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "purchased", "completed", "final_score",
                    "attempts_remaining", "is_locked")
    list_filter = ("purchased", "completed")
    search_fields = ("user__username", "course__title")


@admin.register(IssuedCertificate)
class IssuedCertificateAdmin(admin.ModelAdmin):
    list_display = ("certification_name", "user", "date_issued", "unique_uuid")
    search_fields = ("user__username", "certification_name", "unique_uuid")


@admin.register(GeneratedPromoCode)
class GeneratedPromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code_string", "discount_percentage", "target_tag",
                    "expiration_date", "active_status")
    list_filter = ("active_status", "target_tag")
    search_fields = ("code_string",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "current_level", "total_xp")
    search_fields = ("user__username",)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "date_earned")
    search_fields = ("user__username", "name")

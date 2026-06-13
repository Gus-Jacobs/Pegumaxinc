from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return [
            "main_site:home", "main_site:software_center", "main_site:about",
            "main_site:community", "main_site:store", "main_site:policy",
            "main_site:contact", "main_site:apex_studio", "main_site:lucidcut",
            "main_site:game_portal", "main_site:student_suite_launch",
            "main_site:scribe", "main_site:contour", "main_site:inference",
        ]

    def location(self, item):
        return reverse(item)

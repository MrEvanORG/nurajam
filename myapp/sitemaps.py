from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class ImStaticViewSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        return ['index']

    def location(self, item):
        return reverse(item)
    
class StaticViewSitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return ['register-index']

    def location(self, item):
        return reverse(item)
from django.contrib import admin

from .models import *

admin.site.register(Category)
admin.site.register(MyCategory)
admin.site.register(Topic)
admin.site.register(Tag)
admin.site.register(MyTag)
admin.site.register(News)
admin.site.register(MyNews)
admin.site.register(Save)
admin.site.register(Vote)
admin.site.register(Quote)

admin.site.register(Profile)

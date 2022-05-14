from django.contrib import admin

from .models import *

admin.site.register(Customer)
admin.site.register(Plan)
admin.site.register(Tag)
admin.site.register(Order)
admin.site.register(FailedLoginAttempt)

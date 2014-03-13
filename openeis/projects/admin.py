
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Organization


class MembershipInline(admin.TabularInline):
    model = Organization.members.through


class OrganizationAdmin(admin.ModelAdmin):
    inlines = (MembershipInline,)
    excludes = ('members',)


class OrganizationInline(admin.TabularInline):
    model = Organization.members.through
    extra = 0


# Add organization information to User admin.
class UserAdmin(UserAdmin):
    inlines = (OrganizationInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Organization, OrganizationAdmin)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from . import models


class MembershipInline(admin.TabularInline):
    model = models.Organization.members.through


class OrganizationAdmin(admin.ModelAdmin):
    inlines = (MembershipInline,)
    excludes = ('members',)


class OrganizationInline(admin.TabularInline):
    model = models.Organization.members.through
    extra = 0


# Add organization information to User admin.
class UserAdmin(UserAdmin):
    inlines = (OrganizationInline,)


class DataFileAdmin(admin.TabularInline):
    model = models.DataFile
    extra = 0


class ProjectAdmin(admin.ModelAdmin):
    inlines = (DataFileAdmin,)
    list_display = ('name', 'owner')
    search_fields = ('name', 'owner__username', 'owner__last_name',
                     'owner__first_name')


class AccountVerificationAdmin(admin.ModelAdmin):
    model = models.AccountVerification
    list_display = ('account', 'initiated', 'what')
    list_filter = ('initiated', 'what')


class SensorMapDefAdmin(admin.ModelAdmin):
    model = models.SensorMapDefinition
    list_display = ('name', 'project', 'owner')
    list_filter = ('project', 'project__owner')
    search_fields = ('name', 'project__name', 'project__owner__user',
                     'project__owner__last_name', 'project__owner__first_name')

    def owner(self, definition):
        return definition.project.owner

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(models.Organization, OrganizationAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.AccountVerification, AccountVerificationAdmin)
admin.site.register(models.SensorMapDefinition, SensorMapDefAdmin)

# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2014, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# or favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#
#}}}

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

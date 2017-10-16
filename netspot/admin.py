from __future__ import unicode_literals

from django.contrib import admin

from django.shortcuts import redirect

from .models import Category, ConfigurationTemplate, Variable

from .models import Playbook, PlaybookVariable, PlaybookPermission

# Playbboks

class PlaybookPermissionAdmin(admin.ModelAdmin):
  """Admin for playbook permission."""

  list_display = ['name', 'users']

admin.site.register(PlaybookPermission, PlaybookPermissionAdmin)

class PlaybookVariableInline(admin.TabularInline):
  """Variables for Playbooks."""

  model = PlaybookVariable
  extra = 3

class PlaybookAdmin(admin.ModelAdmin):
  """Playbook configuration."""

  list_display = ['name', 'description']

  search_fields = ['name', 'description']

  inlines = [PlaybookVariableInline]

admin.site.register(Playbook, PlaybookAdmin)

# Templates / Templify

class CategoryAdmin(admin.ModelAdmin):
  """Admin for categories."""

  list_display = ['name', 'description']

admin.site.register(Category, CategoryAdmin)

class VariableInline(admin.TabularInline):
  """Variables for ConfigurationTemplate."""

  model = Variable
  extra = 3

class ConfigurationTemplateAdmin(admin.ModelAdmin):
  """Configuration templates."""

  list_display = ['name', 'description', 'category']
  list_filter = ['name', 'description']
  search_fields = ['name', 'description']

  inlines = [VariableInline]

  def response_add(self, request, obj, post_url_continue=None):
    return redirect('/templify/')

  def response_change(self, request, obj):
    return redirect('/templify/')

admin.site.register(ConfigurationTemplate, ConfigurationTemplateAdmin)

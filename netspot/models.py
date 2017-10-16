from __future__ import unicode_literals

from django.db import models

from django.core.exceptions import ValidationError

# Playbook configuration

class PlaybookPermission(models.Model):
  """Permissions for playbooks."""

  name = models.CharField(max_length=50)
  users = models.CharField(max_length=500)

  def __str__(self):
    return self.name

class Playbook(models.Model):
  """Playbook configuration."""

  name = models.CharField(max_length=30)
  playbook_file = models.CharField(max_length=40)
  description = models.CharField(max_length=100)
  user_auth = models.BooleanField(help_text="Ask user for username/password?")
  template_input = models.BooleanField(help_text="Accept template?")
  asset_filter = models.CharField(max_length=30, help_text="'*' for ALL devices")
  permissions = models.ForeignKey(PlaybookPermission, on_delete=models.CASCADE)

  def __str__(self):
    return self.name

class PlaybookVariable(models.Model):
  """Variable for Playbook."""

  playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE)
  name = models.CharField(max_length=30)
  regex = models.CharField(max_length=30)
  example = models.CharField(max_length=200)

  def __str__(self):
    return self.name

# Templates / Templify

def validate_hyphen(value):
  """Make sure '-' is not in value."""
  if '-' in value:
    raise ValidationError(('%(value)s cannot contain "-"'), params={'value': value},)

class Category(models.Model):
  """Categories for ConfigurationTemplate."""

  name = models.CharField(max_length=30)
  description = models.CharField(max_length=200)

  def __str__(self):
    return self.name

class ConfigurationTemplate(models.Model):
  """Configuration templates."""

  name = models.CharField(max_length=100)
  description = models.CharField(max_length=200)
  template = models.TextField(null=True)

  category = models.ForeignKey(Category)

  # Default playbook to be used with this template
  playbook = models.ForeignKey(Playbook, null=True, blank=True, help_text="Default playbook. Leave blank if none.")

  def __str__(self):
    return self.name

class Variable(models.Model):
  """Variables for ConfigurationTemplate."""

  template = models.ForeignKey(ConfigurationTemplate, on_delete=models.CASCADE)
  variable = models.CharField(max_length=50, validators=[validate_hyphen])
  description = models.CharField(max_length=100)
  regex = models.CharField(max_length=100, blank=True)
  example = models.CharField(max_length=100, blank=True)

  def __str__(self):
    return self.variable

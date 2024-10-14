# score_management/templatetags/custom_tags.py
from django import template
from urllib.parse import quote

register = template.Library()

@register.filter
def urlencode(value):
    return quote(value)

# admin_self/templatetags/analytics_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(key, '')

@register.filter
def replace(value, arg):
    """Replace characters in string"""
    old, new = arg.split(',')
    return value.replace(old, new)

@register.filter
def add(value, arg):
    """Add two values"""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        try:
            return float(value) + float(arg)
        except (ValueError, TypeError):
            return value
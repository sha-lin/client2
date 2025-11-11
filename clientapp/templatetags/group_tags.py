from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """Return True if user belongs to group `group_name`."""
    try:
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        return user.groups.filter(name=group_name).exists()
    except Exception:
        return False
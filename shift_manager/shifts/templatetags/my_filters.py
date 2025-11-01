from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """テンプレート上で辞書の値を取得するフィルタ"""
    return dictionary.get(key, '')

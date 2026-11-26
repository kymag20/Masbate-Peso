# Compatibility fix for Python 3.14/3.15 and Django 5.x template context copy
try:
    from django.template import context as django_context
    def _patched_base_context_copy(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate
    django_context.BaseContext.__copy__ = _patched_base_context_copy
except Exception:
    pass

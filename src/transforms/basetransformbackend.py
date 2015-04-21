
from django.utils.six import with_metaclass

from apps.genapi.utils.log.logmeta import LogMeta


from apps.genapi.src.utils import tobool

class BaseTransformBackend(with_metaclass(LogMeta)):
    """
    A base class from which all filter backend classes should inherit.
    """

    def transform_page(self, request, page, view):
        """
        Return a filtered queryset.
        """
        return page

    def prm(self, val):
        return tobool(val)

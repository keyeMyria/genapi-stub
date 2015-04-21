
from django.utils.six import with_metaclass

from apps.genapi.utils.log.logmeta import LogMeta


from apps.genapi.src.utils import tobool

class BaseBiz(with_metaclass(LogMeta)):
    pass

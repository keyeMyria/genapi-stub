

from .basetransformbackend import BaseTransformBackend

class SimpleTransformBackend(BaseTransformBackend):

    def transform_page(self, request, page, view):
        """
        Return a filtered page.
        """
        return page



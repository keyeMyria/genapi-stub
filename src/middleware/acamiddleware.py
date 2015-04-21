from django.conf import settings


class AcaMiddleware(object):

    def process_response(self, request, response):
        origin = request.META.get('HTTP_ORIGIN', None)

        if(origin):
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Methods"] = "HEAD, PUT, POST, GET, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type"
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Max-Age"] = "86400"

        return response

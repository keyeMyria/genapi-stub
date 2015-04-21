CHARSETSTR  = "; charset=utf-8"
HEADER      = "Content-Type"

class Utf8Middleware(object):

    def process_response(self, request, response):
        _find = response.get(HEADER, None)
        if(_find == None):
            return response

        if(_find.find(CHARSETSTR) < 0):
            response[HEADER] += CHARSETSTR

        return response

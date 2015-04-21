from django.conf import settings

import johnny.cache


class NoCacheMiddleware(object):
	pass

    #def process_request(self, request):
        #self.nocache = request.GET.get("nocache")
        #if(self.nocache):
            #johnny.cache.disable()

    #def process_response(self, request, response):
        #response["X-No-Cache"] = False
        #if(self.nocache):
            #johnny.cache.enable()
            #response["X-No-Cache"] = True
        #return response

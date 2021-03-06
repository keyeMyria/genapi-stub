import thread
import os
import time

from django.conf import settings


class ProfileMiddleware(object):

    time = time.time()

    def process_request(self, request):
        self.time = time.time()

    def process_response(self, request, response):

        response["X-Time-Delta"] = time.time() - self.time
        response["X-PID"] = os.getpid()
        response["X-TID"] = thread.get_ident()

        return response

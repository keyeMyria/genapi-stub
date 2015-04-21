import re
import time

from django.utils.text import compress_sequence, compress_string
from django.utils.cache import patch_vary_headers

re_accepts_gzip = re.compile(r'\bgzip\b')


class GZipMiddleware(object):
    """
    This middleware compresses content if the browser allows gzip compression.
    It sets the Vary header accordingly, so that caches will base their storage
    on the Accept-Encoding header.
    """
    def process_response(self, request, response):
        response['X-Gzip-Delta'] = 0
        self.time = time.time()

        # It's not worth attempting to compress really short responses.
        if not response.streaming and len(response.content) < 200:
            return response

        ##Avoid gzipping if we've already got a content-encoding.
        #if response.has_header('Content-Encoding'):
            ##return response
             #del response['Content-Encoding']

        patch_vary_headers(response, ('Accept-Encoding',))

        ae = request.META.get('HTTP_ACCEPT_ENCODING', '')
        if not re_accepts_gzip.search(ae):
            return response

        if response.streaming:
            # Delete the `Content-Length` header for streaming content, because
            # we won't know the compressed size until we stream it.
            response.streaming_content = compress_sequence(response.streaming_content)
            del response['Content-Length']
        else:
            # Return the compressed content only if it's actually shorter.

            compressed_content = compress_string(response.content)
            len_compressed_content = len(compressed_content)
            len_response_content = len(response.content)

            #gzip_factor = 1.0 * len_response_content / len_compressed_content
            #response['X-Gzip-Factor'] = gzip_factor
            #
            gzip_delta = len_response_content - len_compressed_content
            response['X-Gzip-Delta'] = gzip_delta
            if gzip_delta < 0:
                return response
            response.content = compressed_content
            response['Content-Length'] = str(len(response.content))

        if response.has_header('ETag'):
            response['ETag'] = re.sub('"$', ';gzip"', response['ETag'])
        response['Content-Encoding'] = 'gzip'


        return response

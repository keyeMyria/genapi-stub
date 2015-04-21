#from __future__ import unicode_literals

import csv
import codecs
import io
import six

from django.conf import settings
from rest_framework.parsers import BaseParser
from rest_framework.exceptions import ParseError


class OrderedRows(list):
    """
    Maintains original header/field ordering.
    """
    def __init__(self, header):
        self.header = [c.strip() for c in header] if (header is not None) else None




def preprocess_stream(stream, charset):
    if six.PY2:
        # csv.py doesn't do Unicode; encode temporarily:
        return (chunk.encode(charset) for chunk in stream)
    else:
        return stream

def postprocess_row(row, charset):
    print "row = ", row
    if six.PY2:
        # decode back to Unicode, cell by cell:
        return [cell.decode(charset) for cell in row]
    else:
        return row

def unicode_csv_reader(csv_data, dialect='excel-tab', charset='utf-8', **kwargs):
    csv_data = preprocess_stream(csv_data, charset)
    csv_reader = csv.reader(csv_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield postprocess_row(row, charset)

def universal_newlines(stream, encoding):
    for intermediate_line in stream.readlines():
        # It's possible that the stream was not opened in universal
        # newline mode. If not, we may have a single "row" that has a
        # bunch of carriage return (\r) characters that should act as
        # newlines. For that case, lets call splitlines on the row. If
        # it doesn't have any newlines, it will return a list of just
        # the row itself.
        intermediate_line = intermediate_line.decode(encoding)

        for line in intermediate_line.splitlines():
            for semiline in line.split(';'):
                yield semiline


from apps.genapi.utils import toint, tolong, tofloat

class CSVParser(BaseParser):
    """
    Parses CSV serialized data.

    The parser assumes the first line contains the column names.
    """

    media_type = 'text/csv'

    def parse(self, stream, media_type=None, parser_context=None):


        parser_context = parser_context or {}
        delimiter = parser_context.get('delimiter', '\t')

        #try:
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)
        rows = unicode_csv_reader(
            universal_newlines(stream, encoding),
            delimiter=delimiter,
            charset=encoding
        )

        data = OrderedRows(next(rows))
        for row in rows:
            row_data = dict(zip(data.header, row))
            for key, value in row_data.items():
                if((value) == u''):
                    row_data[key] = None
            data.append(row_data)
        return data
        #except Exception as exc:
            #raise ParseError('CSV parse error - %s' % str(exc))

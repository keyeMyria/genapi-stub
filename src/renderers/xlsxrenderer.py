from __future__ import unicode_literals
import csv
import xlsxwriter
from collections import defaultdict
from rest_framework.renderers import *
from six import StringIO, text_type
import operator
from django.utils.datastructures import SortedDict

class OrderedRows(list):
    """
    Maintains original header/field ordering.
    """
    def __init__(self, header):
        self.header = [c.strip() for c in header] if (header is not None) else None


# six versions 1.3.0 and previous don't have PY2
try:
    from six import PY2
except ImportError:
    import sys
    PY2 = sys.version_info[0] == 2

class XLSXRenderer(BaseRenderer):
    """
        Renderer which serializes to XLSX
    """

    # media_type = 'application/octet-stream'
    media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    format = 'xlsx'
    level_sep = '.'
    headers = None

    def render(self, input_data, media_type=None, renderer_context=None):
        """
        Renders serialized *data* into XLSX. For a dictionary:
        """
        if input_data is None:
            return ''

        data = input_data
        if not isinstance(data, list):
            data = input_data.get('results', [input_data])

        table = self.tablize(data)


        xlsx_buffer = StringIO()
        workbook = xlsxwriter.Workbook(xlsx_buffer, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        bold = workbook.add_format({'bold': True})
        bold.set_font_color('red')


        width_dict = {}
        for ri, row in enumerate(table):
            for ci, elem in enumerate(row):
                new_width = len(unicode(elem)) * 1
                cur_width = width_dict.get(ci, 0)
                if(new_width > cur_width):
                    width_dict[ci] = new_width
                worksheet.set_column(ci, ci, width_dict[ci])
                if(ri == 0):
                    worksheet.write(ri, ci, elem, bold)
                else:
                    worksheet.write(ri, ci, elem)

        workbook.close()


        return xlsx_buffer.getvalue()


    def tablize(self, data):

        table = self._tablize(data)

        return table


    def _tablize(self, data):
        """
        Convert a list of data into a table.
        """
        if data:

            # First, flatten the data (i.e., convert it to a list of
            # dictionaries that are each exactly one level deep).  The key for
            # each item designates the name of the column that the item will
            # fall into.
            data = self.flatten_data(data)
            data.header = data.header or self.headers

            # Get the set of all unique headers, and sort them (unless already provided).
            if not data.header:
                headers = SortedDict()
                m = -1
                for item in data:
                    l = len(item.keys())
                    if(l > m):
                        headers = item
                        l = m
                data.header = list(headers)
            # Create a row for each dictionary, filling in columns for which the
            # item has no data with None values.
            rows = []
            for item in data:
                row = []
                for key in data.header:
                    row.append(item.get(key, None))
                rows.append(row)

            # Return your "table", with the headers as the first row.
            return [data.header] + rows

        else:
            return []

    def flatten_data(self, data):
        """
        Convert the given data collection to a list of dictionaries that are
        each exactly one level deep. The key for each value in the dictionaries
        designates the name of the column that the value will fall into.
        """
        flat_data = OrderedRows(data.header if hasattr(data, 'header') else None)
        for item in data:
            flat_item = self.flatten_item(item)
            flat_data.append(flat_item)

        return flat_data

    def flatten_item(self, item):

        if isinstance(item, list):
            flat_item = self.flatten_list(item)
        elif isinstance(item, dict):
            flat_item = self.flatten_dict(item)
        else:
            flat_item = SortedDict({'': item})

        return flat_item

    def nest_flat_item(self, flat_item, prefix):
        """
        Given a "flat item" (a dictionary exactly one level deep), nest all of
        the column headers in a namespace designated by prefix.  For example:

         header... | with prefix... | becomes...
        -----------|----------------|----------------
         'lat'     | 'location'     | 'location.lat'
         ''        | '0'            | '0'
         'votes.1' | 'user'         | 'user.votes.1'

        """
        nested_item = SortedDict()
        for header, val in flat_item.items():
            nested_header = self.level_sep.join([prefix, header]) if header else prefix
            nested_item[nested_header] = val
        return nested_item

    def flatten_list(self, l):
        flat_list = SortedDict()
        for index, item in enumerate(l):
            index = text_type(index)
            flat_item = self.flatten_item(item)
            nested_item = self.nest_flat_item(flat_item, index)
            flat_list.update(nested_item)
        return flat_list

    def flatten_dict(self, d):
        flat_dict = SortedDict()
        for key, item in d.items():
            key = text_type(key)
            flat_item = self.flatten_item(item)
            nested_item = self.nest_flat_item(flat_item, key)
            flat_dict.update(nested_item)
        return flat_dict


class XLSXRendererWithUnderscores (XLSXRenderer):
    level_sep = '_'

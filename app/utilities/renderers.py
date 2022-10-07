from rest_framework import renderers
import json
import math


class NormalRenderer(renderers.JSONRenderer):
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = ''
        if 'ErrorDetail' in str(data):
            response = json.dumps(data)
        else:
            response = json.dumps({
                'success': True,
                'data': data
            })
        return response


class PagingRenderer(renderers.JSONRenderer):
    charset = 'utf-8'

    # accepted_media_type=None, renderer_context=None
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = ''
        if 'ErrorDetail' in str(data):
            response = json.dumps(data)
        else:
            response = json.dumps({
                'success': True,
                **data,
                'totalPages': math.ceil(data['totalItems'] / data['take']),
                'data': data['data'],
            })
        return response


class BinaryRenderer(renderers.BaseRenderer):
    media_type = 'image/png'
    format = 'png'
    charset = None
    render_style = 'binary'

    def __init__(self, media_type, format, charset):
        super().__init__()
        self.media_type = media_type
        self.format = format
        self.charset = charset

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

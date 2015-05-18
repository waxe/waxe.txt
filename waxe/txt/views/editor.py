from pyramid.view import view_config
import pyramid.httpexceptions as exc
import pyramid_logging
from waxe.core import browser, events
from waxe.core.views.base import BaseUserView
import waxe.txt

log = pyramid_logging.getLogger(__name__)


ROUTE_PREFIX = waxe.txt.ROUTE_PREFIX
EXTENSIONS = waxe.txt.EXTENSIONS


class EditorView(BaseUserView):

    @view_config(route_name='txt_edit_json')
    def edit(self):
        filename = self.req_get.get('path')
        if not filename:
            raise exc.HTTPClientError('No filename given')
        absfilename = browser.absolute_path(filename, self.root_path)
        try:
            content = open(absfilename, 'r').read()
            content = content.decode('utf-8')
        except Exception, e:
            log.exception(e, request=self.request)
            raise exc.HTTPInternalServerError(str(e))

        return content

    @view_config(route_name='txt_update_json')
    def update(self):
        filecontent = self.req_post.get('filecontent')
        filename = self.req_post.get('path')
        if filecontent is None or not filename:
            raise exc.HTTPClientError('Missing parameters!')

        res = events.trigger('before_update.txt',
                             view=self,
                             path=filename,
                             filecontent=filecontent)
        if res:
            filecontent = res[2]

        absfilename = browser.absolute_path(filename, self.root_path)
        with open(absfilename, 'w') as f:
            f.write(filecontent)

        if self.req_post.get('conflicted'):
            events.trigger('updated_conflicted.txt',
                           view=self,
                           path=filename)

        events.trigger('updated.txt',
                       view=self,
                       path=filename)
        return 'File updated'


def includeme(config):
    config.add_route('txt_edit_json', '/edit.json')
    config.add_route('txt_update_json', '/update.json')
    config.scan(__name__)

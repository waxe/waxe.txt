from pyramid.view import view_config
import pyramid.httpexceptions as exc
import pyramid_logging
from waxe.core import browser, events
from waxe.core.views.base import BaseUserView
import waxe.txt
import xmltool

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

    def _update(self, path, filecontent):
        view, path, filecontent = events.trigger(
            'before_update.txt',
            view=self,
            path=path,
            filecontent=filecontent)

        absfilename = browser.absolute_path(path, self.root_path)
        with open(absfilename, 'w') as f:
            f.write(filecontent.encode('utf-8'))

        # conflicted=true is passed in the posted data when there is a conflict
        if self.req_post.get('conflicted'):
            events.trigger('updated_conflicted.txt',
                           view=self,
                           path=path)

        events.trigger('updated.txt',
                       view=self,
                       path=path)

    @view_config(route_name='txt_update_json')
    def update(self):
        filecontent = self.req_post.get('filecontent')
        filename = self.req_post.get('path')
        if filecontent is None or not filename:
            raise exc.HTTPClientError('Missing parameters!')
        self._update(filename, filecontent)
        return 'File updated'

    @view_config(route_name='txt_updates_json')
    def update_texts(self):
        params = xmltool.utils.unflatten_params(self.req_post)
        if 'data' not in params or not params['data']:
            raise exc.HTTPClientError('Missing parameters!')

        error_msgs = []
        for dic in params['data']:
            filecontent = dic['filecontent']
            filename = dic['filename']
            try:
                self._update(filename, filecontent)
            except Exception, e:
                error_msgs += ['%s: %s' % (filename, str(e))]

        if error_msgs:
            raise exc.HTTPClientError('<br />'.join(error_msgs))

        return 'Files updated'


def includeme(config):
    config.add_route('txt_edit_json', '/edit.json')
    config.add_route('txt_update_json', '/update.json')
    config.add_route('txt_updates_json', '/updates.json')
    config.scan(__name__)

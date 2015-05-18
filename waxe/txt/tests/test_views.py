import os
from pyramid import testing
import pyramid.httpexceptions as exc
from waxe.core.tests.testing import WaxeTestCase, login_user, LoggedBobTestCase, SETTINGS
from waxe.core import events
from waxe.txt.views.editor import EditorView


class TestEditorView(LoggedBobTestCase):

    def setUp(self):
        super(TestEditorView, self).setUp()
        self.config.include('waxe.txt.views.editor',
                            route_prefix='/account/{login}')

    def test_edit(self):
        path = os.path.join(os.getcwd(), 'waxe/txt/tests/')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest()
        try:
            EditorView(request).edit()
            assert(False)
        except exc.HTTPClientError, e:
            expected = 'No filename given'
            self.assertEqual(str(e), expected)

        request = testing.DummyRequest(params={
            'path': 'file1.txt',
            'filecontent': 'Hello world',
        })
        EditorView(request).update()

        request = testing.DummyRequest(params={'path': 'file1.txt'})
        res = EditorView(request).edit()
        self.assertEqual(res, 'Hello world')
        filename = os.path.join(path, 'file1.txt')
        os.remove(filename)

    def test_update(self):
        path = os.path.join(os.getcwd(), 'waxe/txt/tests/')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest(params={'path': 'file1.txt'})
        try:
            EditorView(request).update()
            assert(False)
        except exc.HTTPClientError, e:
            expected = 'Missing parameters!'
            self.assertEqual(str(e), expected)

        request = testing.DummyRequest(params={
            'path': 'file1.txt',
            'filecontent': '',
        })
        res = EditorView(request).update()
        self.assertEqual(res, 'File updated')
        filename = os.path.join(path, 'file1.txt')
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    def test_update_events(self):
        lis = []

        def on_before_update(view, path, filecontent):
            lis.append(1)
            filecontent += 'Hello world'
            return view, path, filecontent

        def on_event(*args, **kw):
            lis.append(1)

        events.on('before_update.txt', on_before_update)
        events.on('updated.txt', on_event)
        events.on('updated_conflicted.txt', on_event)

        path = os.path.join(os.getcwd(), 'waxe/txt/tests/')
        self.user_bob.config.root_path = path

        request = testing.DummyRequest(params={
            'path': 'file1.txt',
            'filecontent': '',
        })
        res = EditorView(request).update()
        self.assertEqual(res, 'File updated')
        filename = os.path.join(path, 'file1.txt')
        self.assertTrue(os.path.exists(filename))
        s = open(filename, 'r').read()
        self.assertEqual(s, 'Hello world')
        os.remove(filename)
        self.assertEqual(len(lis), 2)

        request = testing.DummyRequest(params={
            'path': 'file1.txt',
            'filecontent': '',
            'conflicted': True,
        })
        res = EditorView(request).update()
        self.assertEqual(res, 'File updated')
        filename = os.path.join(path, 'file1.txt')
        self.assertTrue(os.path.exists(filename))
        s = open(filename, 'r').read()
        self.assertEqual(s, 'Hello world')
        os.remove(filename)
        self.assertEqual(len(lis), 5)


class FunctionalTestEditorView(WaxeTestCase):

    def setUp(self):
        self.settings = SETTINGS.copy()
        self.settings['waxe.editors'] = 'waxe.txt.views.editor'
        super(FunctionalTestEditorView, self).setUp()

    def test_forbidden(self):

        for url in [
            '/api/1/account/Bob/txt/edit.json',
            '/api/1/account/Bob/txt/update.json',
        ]:
            self.testapp.get(url, status=401)

    @login_user('Bob')
    def test_edit(self):
        res = self.testapp.get('/api/1/account/Bob/txt/edit.json', status=400)
        self.assertEqual(res.body,  '"No filename given"')

    @login_user('Bob')
    def test_update(self):
        res = self.testapp.post('/api/1/account/Bob/txt/update.json', status=400)
        self.assertEqual(res.body,  '"Missing parameters!"')

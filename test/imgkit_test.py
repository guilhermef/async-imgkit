# -*- coding: utf-8 -*-
import os
import io
import sys
import codecs
import unittest
import tempfile

import aiounittest

import async_imgkit.async_imgkit
import async_imgkit.api
import async_imgkit.config


class TestIMGKitInitialization(aiounittest.AsyncTestCase):
    """Test init"""

    async def test_html_source(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('<h1>Oh hai</h1>', 'string')
        self.assertTrue(r.source.isString())

    async def test_url_source(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('http://ya.ru', 'url')
        self.assertTrue(r.source.isUrl())

    async def test_file_source(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('fixtures/example.html', 'file')
        self.assertTrue(r.source.isFile())

    async def test_file_object_source(self):
        with open('fixtures/example.html') as fl:
            r = await async_imgkit.async_imgkit.AsyncIMGKit.create(fl, 'file')
            self.assertTrue(r.source.isFileObj())

    async def test_file_source_with_path(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('test', 'string')
        with io.open('fixtures/example.css') as f:
            self.assertTrue(r.source.isFile(path=f))
        with codecs.open('fixtures/example.css', encoding='UTF-8') as f:
            self.assertTrue(r.source.isFile(path=f))

    async def test_options_parsing(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options={'format': 'jpg'})
        test_command = r.command('test')
        idx = test_command.index('--format')  # Raise exception in case of not found
        self.assertTrue(test_command[idx + 1] == 'jpg')

    async def test_options_parsing_with_dashes(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options={'--format': 'jpg'})

        test_command = r.command('test')
        idx = test_command.index('--format')  # Raise exception in case of not found
        self.assertTrue(test_command[idx + 1] == 'jpg')

    async def test_options_parsing_with_tuple(self):
        options = {
            '--custom-header': [
                ('Accept-Encoding', 'gzip')
            ]
        }
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options=options)
        command = r.command()
        idx1 = command.index('--custom-header')  # Raise exception in case of not found
        self.assertTrue(command[idx1 + 1] == 'Accept-Encoding')
        self.assertTrue(command[idx1 + 2] == 'gzip')

    async def test_options_parsing_with_tuple_no_dashes(self):
        options = {
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ]
        }
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options=options)
        command = r.command()
        idx1 = command.index('--custom-header')  # Raise exception in case of not found
        self.assertTrue(command[idx1 + 1] == 'Accept-Encoding')
        self.assertTrue(command[idx1 + 2] == 'gzip')

    async def test_repeatable_options(self):
        roptions = {
            '--format': 'jpg',
            'cookies': [
                ('test_cookie1', 'cookie_value1'),
                ('test_cookie2', 'cookie_value2'),
            ]
        }

        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options=roptions)

        test_command = r.command('test')

        idx1 = test_command.index('--format')  # Raise exception in case of not found
        self.assertTrue(test_command[idx1 + 1] == 'jpg')

        self.assertTrue(test_command.count('--cookies') == 2)

        idx2 = test_command.index('--cookies')
        self.assertTrue(test_command[idx2 + 1] == 'test_cookie1')
        self.assertTrue(test_command[idx2 + 2] == 'cookie_value1')

        idx3 = test_command.index('--cookies', idx2 + 2)
        self.assertTrue(test_command[idx3 + 1] == 'test_cookie2')
        self.assertTrue(test_command[idx3 + 2] == 'cookie_value2')

    async def test_custom_config(self):
        conf = async_imgkit.api.config()
        self.assertEqual('imgkit-', conf.meta_tag_prefix)
        conf = async_imgkit.api.config(meta_tag_prefix='prefix-')
        self.assertEqual('prefix-', conf.meta_tag_prefix)
        with self.assertRaises(IOError):
            async_imgkit.api.config(wkhtmltoimage='wrongpath')


class TestIMGKitCommandGeneration(aiounittest.AsyncTestCase):
    """Test command() method"""

    async def test_command_construction(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options={'format': 'jpg', 'toc-l1-font-size': 12})
        command = r.command()
        self.assertEqual(command[0], r.wkhtmltoimage)
        self.assertEqual(command[command.index('--format') + 1], 'jpg')
        self.assertEqual(command[command.index('--toc-l1-font-size') + 1], '12')

    async def test_lists_of_input_args(self):
        urls = ['http://ya.ru', 'http://google.com']
        paths = ['fixtures/example.html', 'fixtures/example.html']
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create(urls, 'url')
        r2 = await async_imgkit.async_imgkit.AsyncIMGKit.create(paths, 'file')
        cmd = r.command()
        cmd2 = r2.command()
        self.assertEqual(cmd[-3:], ['http://ya.ru', 'http://google.com', '-'])
        self.assertEqual(cmd2[-3:], ['fixtures/example.html', 'fixtures/example.html', '-'])

    async def test_read_source_from_stdin(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string')
        self.assertEqual(r.command()[-2:], ['-', '-'])

    async def test_url_in_command(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('http://ya.ru', 'url')
        self.assertEqual(r.command()[-2:], ['http://ya.ru', '-'])

    async def test_file_path_in_command(self):
        path = 'fixtures/example.html'
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create(path, 'file')
        self.assertEqual(r.command()[-2:], [path, '-'])

    async def test_output_path(self):
        out = '/test/test2/out.jpg'
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string')
        self.assertEqual(r.command(out)[-1:], ['/test/test2/out.jpg'])

    async def test_imgkit_meta_tags(self):
        body = """
        <html>
          <head>
            <meta name="imgkit-format" content="jpg"/>
            <meta name="imgkit-orientation" content="Landscape"/>
          </head>
        """

        r = await async_imgkit.async_imgkit.AsyncIMGKit.create(body, 'string')
        command = r.command()
        self.assertEqual(command[command.index('--format') + 1], 'jpg')
        self.assertEqual(command[command.index('--orientation') + 1], 'Landscape')

    async def test_imgkit_meta_tags_in_bad_markup(self):
        body = """
        <html>
          <head>
            <meta name="imgkit-format" content="jpg"/>
            <meta name="imgkit-orientation" content="Landscape"/>
          </head>
          <br>
        </html>
        """

        r = await async_imgkit.async_imgkit.AsyncIMGKit.create(body, 'string')
        command = r.command()
        self.assertEqual(command[command.index('--format') + 1], 'jpg')
        self.assertEqual(command[command.index('--orientation') + 1], 'Landscape')

    async def test_skip_nonimgkit_tags(self):
        body = """
        <html>
          <head>
            <meta name="test-page-size" content="Legal"/>
            <meta name="imgkit-orientation" content="Landscape"/>
          </head>
          <br>
        </html>
        """

        r = await async_imgkit.async_imgkit.AsyncIMGKit.create(body, 'string')
        command = r.command()
        self.assertEqual(command[command.index('--orientation') + 1], 'Landscape')

    async def test_toc_handling_without_options(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('hmtl', 'string', toc={'xsl-style-sheet': 'test.xsl'})
        self.assertEqual(r.command()[1], 'toc')
        self.assertEqual(r.command()[2], '--xsl-style-sheet')

    async def test_toc_with_options(self):
        options = {
            'format': 'jpg',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8"
        }
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options=options, toc={'xsl-style-sheet': 'test.xsl'})

        command = r.command()

        self.assertEqual(command[1 + len(options) * 2], 'toc')
        self.assertEqual(command[1 + len(options) * 2 + 1], '--xsl-style-sheet')

    async def test_cover_without_options(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', cover='test.html')

        command = r.command()

        self.assertEqual(command[1], 'cover')
        self.assertEqual(command[2], 'test.html')

    async def test_cover_with_options(self):
        options = {
            'format': 'jpg',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8"
        }
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options=options, cover='test.html')

        command = r.command()

        self.assertEqual(command[1 + len(options) * 2], 'cover')
        self.assertEqual(command[1 + len(options) * 2 + 1], 'test.html')

    async def test_cover_and_toc(self):
        options = {
            'format': 'jpg',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8"
        }
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options=options, toc={'xsl-style-sheet': 'test.xsl'}, cover='test.html')
        command = r.command()
        self.assertEqual(command[-7:], ['toc', '--xsl-style-sheet', 'test.xsl', 'cover', 'test.html', '-', '-'])

    async def test_cover_and_toc_cover_first(self):
        options = {
            'format': 'jpg',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8"
        }
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options=options, toc={'xsl-style-sheet': 'test.xsl'}, cover='test.html',
                          cover_first=True)
        command = r.command()
        self.assertEqual(command[-7:], ['cover', 'test.html', 'toc', '--xsl-style-sheet', 'test.xsl', '-', '-'])

    async def test_outline_options(self):
        options = {
            'outline': None,
            'outline-depth': 1
        }

        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('ya.ru', 'url', options=options)
        cmd = r.command()
        # self.assertEqual(cmd[1:], ['--outline', '--outline-depth', '1', 'ya.ru', '-'])
        self.assertIn('--outline', cmd)
        self.assertEqual(cmd[cmd.index('--outline-depth') + 1], '1')

    async def test_filter_empty_and_none_values_in_opts(self):
        options = {
            'outline': '',
            'footer-line': None,
            'quiet': False
        }

        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options=options)
        cmd = r.command()
        self.assertEqual(len(cmd), 6)


class TestIMGKitGeneration(aiounittest.AsyncTestCase):
    """Test to_img() method"""

    def setUp(self):
        self.file_path = tempfile.NamedTemporaryFile(suffix=".jpg").name

    async def test_img_generation(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options={'format': 'jpg'})
        pic = await r.to_img(self.file_path)
        self.assertTrue(pic)

    @unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux")
    async def test_img_generation_xvfb(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('html', 'string', options={'format': 'jpg', 'xvfb': ''})
        pic = await r.to_img(self.file_path)
        self.assertTrue(pic)

    async def test_raise_error_with_invalid_url(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('wrongurl', 'url')
        with self.assertRaises(IOError):
            await r.to_img(self.file_path)

    async def test_raise_error_with_invalid_file_path(self):
        paths = ['frongpath.html', 'wrongpath2.html']
        with self.assertRaises(IOError):
            await async_imgkit.async_imgkit.AsyncIMGKit.create('wrongpath.html', 'file')
        with self.assertRaises(IOError):
            await async_imgkit.async_imgkit.AsyncIMGKit.create(paths, 'file')

    async def test_stylesheet_adding_to_the_head(self):
        # TODO rewrite this part of pdfkit.py
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('<html><head></head><body>Hai!</body></html>', 'string',
                          css='fixtures/example.css')

        with open('fixtures/example.css') as f:
            css = f.read()

        r._prepend_css('fixtures/example.css')
        self.assertIn('<style>%s</style>' % css, r.source.to_s())

    async def test_stylesheet_adding_without_head_tag(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('<html><body>Hai!</body></html>', 'string',
                          options={'quiet': None}, css='fixtures/example.css')

        with open('fixtures/example.css') as f:
            css = f.read()

        r._prepend_css('fixtures/example.css')
        self.assertIn('<style>%s</style><html>' % css, r.source.to_s())

    async def test_multiple_stylesheets_adding_to_the_head(self):
        # TODO rewrite this part of pdfkit.py
        css_files = ['fixtures/example.css', 'fixtures/example2.css']
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('<html><head></head><body>Hai!</body></html>', 'string',
                          css=css_files)

        css = []
        for css_file in css_files:
            with open(css_file) as f:
                css.append(f.read())

        r._prepend_css(css_files)
        self.assertIn('<style>%s</style>' % "\n".join(css), r.source.to_s())

    async def test_multiple_stylesheet_adding_without_head_tag(self):
        css_files = ['fixtures/example.css', 'fixtures/example2.css']
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('<html><body>Hai!</body></html>', 'string',
                          options={'quiet': None}, css=css_files)

        css = []
        for css_file in css_files:
            with open(css_file) as f:
                css.append(f.read())

        r._prepend_css(css_files)
        self.assertIn('<style>%s</style><html>' % "\n".join(css), r.source.to_s())

    async def test_stylesheet_throw_error_when_url(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('http://ya.ru', 'url', css='fixtures/example.css')

        with self.assertRaises(r.SourceError):
            await r.to_img()

    async def test_stylesheet_adding_to_file_with_option(self):
        css = 'fixtures/example.css'
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('fixtures/example.html', 'file', css=css)
        self.assertEqual(r.css, css)
        r._prepend_css(css)
        self.assertIn('font-size', r.source.to_s())

    async def test_wkhtmltoimage_error_handling(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('clearlywrongurl.asdf', 'url')
        with self.assertRaises(IOError):
            await r.to_img()

    async def test_pdf_generation_from_file_like(self):
        with open('fixtures/example.html', 'r') as f:
            r = await async_imgkit.async_imgkit.AsyncIMGKit.create(f, 'file')
            output = await r.to_img()
        self.assertEqual(output[:4], b'\xff\xd8\xff\xe0')  # TODO img

    async def test_raise_error_with_wrong_css_path(self):
        css = 'fixtures/wrongpath.css'
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('fixtures/example.html', 'file', css=css)
        with self.assertRaises(IOError):
            await r.to_img()

    async def test_raise_error_if_bad_wkhtmltoimage_option(self):
        r = await async_imgkit.async_imgkit.AsyncIMGKit.create('<html><body>Hai!</body></html>', 'string',
                          options={'bad-option': None})
        with self.assertRaises(IOError) as cm:
            await r.to_img()

        raised_exception = cm.exception
        self.assertRegex(str(raised_exception),
                                 '^wkhtmltoimage exited with non-zero code 1. error:\nUnknown long argument '
                                 '--bad-option\r?\n')


class TestIMGKitAPI(aiounittest.AsyncTestCase):
    """Test API"""

    def setUp(self):
        self.file_path = tempfile.NamedTemporaryFile(suffix=".jpg").name

    async def test_from_string(self):
        pic = await async_imgkit.api.from_string('hello imgkit!', self.file_path)
        self.assertTrue(pic)

    async def test_from_url(self):
        pic = await async_imgkit.api.from_url('https://github.com', self.file_path)
        self.assertTrue(pic)

    async def test_from_file(self):
        pic = await async_imgkit.api.from_file('fixtures/example.html', self.file_path)
        self.assertTrue(pic)


if __name__ == "__main__":
    unittest.main()

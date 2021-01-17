# -*- coding: utf-8 -*-
import asyncio
import re
import subprocess
import sys
from imgkit.source import Source
from async_imgkit.config import Config
from imgkit import IMGKit
import io
import codecs


class AsyncIMGKit(IMGKit):
    """

    """

    def __init__(self):
        return None

    @classmethod
    async def create(cls, url_or_file, source_type, options=None, toc=None, cover=None,
                 css=None, config=None, cover_first=None):
        imgkit = cls()
        imgkit.source = Source(url_or_file, source_type)
        imgkit.config = Config() if not config else config
        try:
            imgkit.wkhtmltoimage = imgkit.config.wkhtmltoimage.decode('utf-8')
        except AttributeError:
            imgkit.wkhtmltoimage = imgkit.config.wkhtmltoimage

        imgkit.xvfb = imgkit.config.xvfb

        imgkit.options = {}
        if imgkit.source.isString():
            imgkit.options.update(imgkit._find_options_in_meta(url_or_file))

        if options:
            imgkit.options.update(options)

        imgkit.toc = toc if toc else {}
        imgkit.cover = cover
        imgkit.cover_first = cover_first
        imgkit.css = css
        imgkit.stylesheets = []
        return imgkit


    async def to_img(self, path=None):
        args = " ".join(self.command(path))

        result = await asyncio.create_subprocess_shell(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

        # If the source is a string then we will pipe it into wkhtmltoimage.
        # If we want to add custom CSS to file then we read input file to
        # string and prepend css to it and then pass it to stdin.
        # This is a workaround for a bug in wkhtmltoimage (look closely in README)
        if self.source.isString() or (self.source.isFile() and self.css):
            string = self.source.to_s().encode('utf-8')
        elif self.source.isFileObj():
            string = self.source.source.read().encode('utf-8')
        else:
            string = None
        stdout, stderr = await result.communicate(input=string)
        stderr = stderr or stdout
        try:
            stderr = stderr.decode('utf-8')
        except UnicodeDecodeError:
            stderr = ''
        exit_code = result.returncode

        if 'cannot connect to X server' in stderr:
            raise IOError('%s\n'
                          'You will need to run wkhtmltoimage within a "virtual" X server.\n'
                          'Go to the link below for more information\n'
                          'http://wkhtmltopdf.org' % stderr)

        if 'Error' in stderr:
            raise IOError('wkhtmltoimage reported an error:\n' + stderr)

        if exit_code != 0:
            xvfb_error = ''
            if 'QXcbConnection' in stderr:
                xvfb_error = 'You need to install xvfb(sudo apt-get install xvfb, yum install xorg-x11-server-Xvfb, etc), then add option: {"xvfb": ""}.'
            raise IOError("wkhtmltoimage exited with non-zero code {0}. error:\n{1}\n\n{2}".format(exit_code, stderr, xvfb_error))

        # Since wkhtmltoimage sends its output to stderr we will capture it
        # and properly send to stdout
        if '--quiet' not in args:
            sys.stdout.write(stderr)

        if not path:
            return stdout
        else:
            try:
                with codecs.open(path, mode='rb') as f:
                    text = f.read(4)
                    if text == '':
                        raise IOError('Command failed: %s\n'
                                      'Check whhtmltoimage output without \'quiet\' '
                                      'option' % args)
                    return True
            except IOError as e:
                raise IOError('Command failed: %s\n'
                              'Check whhtmltoimage output without \'quiet\' option\n'
                              '%s ' % (args), e)

# -*- coding: utf-8 -*-
import asyncio
import sys


class Config(object):
    @classmethod
    async def create(cls, wkhtmltoimage='', meta_tag_prefix='imgkit-'):
        config = cls()
        config.meta_tag_prefix = meta_tag_prefix

        config.wkhtmltoimage = wkhtmltoimage

        config.xvfb = ''

        if not config.wkhtmltoimage:
            config.wkhtmltoimage = await config.get_executable_path("wkhtmltoimage")
        if not config.xvfb:
            config.xvfb = await config.get_executable_path("xvfb-run")
        try:
            with open(config.wkhtmltoimage):
                pass
        except IOError:
            raise IOError('No wkhtmltoimage executable found: "{0}"\n'
                          'If this file exists please check that this process can '
                          'read it. Otherwise please install wkhtmltopdf - '
                          'http://wkhtmltopdf.org\n'.format(config.wkhtmltoimage))
        return config

    async def get_executable_path(self, executable):
        cmd = "which"
        if sys.platform == 'win32':
            cmd = "where"
        proc = await asyncio.create_subprocess_shell(f"{cmd} {executable}", stdout=asyncio.subprocess.PIPE)

        stdout, stderr = await proc.communicate()

        return stdout.decode().strip()


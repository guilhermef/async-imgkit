# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools.command.test import test
import os
import sys
import async_imgkit


class PyTest(test):
    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = ['imgkit_test.py']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        os.chdir('test/')
        err_no = pytest.main(self.test_args)
        sys.exit(err_no)


def long_description():
    try:
        import pypandoc
        long_desc = pypandoc.convert_file('README.md', 'rst')
        long_desc += '\n' + pypandoc.convert_file('AUTHORS.md', 'rst')
    except Exception as e:
        print(e)
        long_desc = async_imgkit.__doc__.strip()
    return long_desc


setup(
    name='async-imgkit',
    version=async_imgkit.__version__,
    description=async_imgkit.__doc__.strip(),
    long_description=long_description(),
    download_url='https://github.com/guilhermef/async_imgkit',
    license="MIT",
    tests_require=[
        'pytest',
        'aiounittest',
    ],
    install_requires=[
        "imgkit",
    ],
    cmdclass={'test': PyTest},
    packages=['async_imgkit'],
    author="guilhermef",
    author_email="guivideojob@gmail.com",
    url="https://github.com/guilhermef/async_imgkit",
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: General',
        'Topic :: Text Processing :: Markup',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Text Processing :: Markup :: XML',
        'Topic :: Utilities'
    ]
)

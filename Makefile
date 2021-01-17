.PHONY: test setup

setup:
	@pip install -e .\[tests\]

test:
	@nosetests --with-coverage --cover-package=async_imgkit --where test imgkit_test.py

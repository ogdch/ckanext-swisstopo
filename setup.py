from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(
	name='ckanext-swisstopo',
	version=version,
	description="swisstopo CKAN extension",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Liip AG',
	author_email='contact@liip.ch',
	url='http://www.liip.ch',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.swisstopo'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
    [ckan.plugins]
	#swisstopo_plugin=ckanext.swisstopo:PluginClass
    [paste.paster_command]
    swisstopo=ckanext.swisstopo.commands.swisstopo:SwisstopoCommand
	""",
)

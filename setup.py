from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(
	name='ckanext-swisstopo',
	version=version,
	description="CKAN extension of the Federal Office of Topography swisstopo for the OGD portal of Switzerland",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Liip AG',
	author_email='ogd@liip.ch',
	url='http://www.liip.ch',
	license='GPL',
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
    swisstopo=ckanext.swisstopo.plugins:SwisstopoHarvest
    swisstopo_harvester=ckanext.swisstopo.harvesters:SwisstopoHarvester
    [paste.paster_command]
    swisstopo=ckanext.swisstopo.commands.swisstopo:SwisstopoCommand
    swisstopo_harvest=ckanext.swisstopo.commands.harvester:Harvester
	""",
)

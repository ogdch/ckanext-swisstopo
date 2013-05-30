from ckanext.swisstopo.ckan_csw import ckan_csw
from pprint import pprint

swisstopo = ckan_csw.SwisstopoCkanMetadata()

pprint(swisstopo)

pprint(swisstopo.get_ckan_metadata('swissboundaries3D'))

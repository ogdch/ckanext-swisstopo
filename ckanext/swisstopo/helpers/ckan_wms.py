# Parse GetCapabilities: https://wms.geo.admin.ch/?REQUEST=GetCapabilities&SERVICE=WMS&VERSION=1.0.0&lang=de
# Lookup Geocat-ID: http://www.geocat.ch/geonetwork/srv/eng/xml_iso19139?id=112886
# Query Geocat using ckan_csw.py
# Insert or update CKAN dataset

from lxml import etree
from owslib.wms import WebMapService
import ckan_csw
from pprint import pprint
import logging
log = logging.getLogger(__name__)

class WmsLayerParser(object):
    """ Allows parsing of WMS layers as datasets """

    def __init__(self):
        self.csw = ckan_csw.SwisstopoCkanMetadata()

    def parse(self, url):
        wms = wms = WebMapService(url, version='1.1.1') 
        layers = list(wms.contents)
        pprint(layers)
        print len(layers)
        lookup = self._load_geocat_lookup()

    def _load_geocat_lookup(self):
        metadata = self.csw.get_ckan_metadata('wms.geo.admin.ch')
        return metadata['coupled_resources']


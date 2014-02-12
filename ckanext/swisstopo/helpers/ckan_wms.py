# Query Geocat using ckan_csw.py
# Insert or update CKAN dataset

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
        """
        Parses the available WMS layers and maps them to geocat
        The validated result is returned using a generator
        """
        wms = wms = WebMapService(url, version='1.1.1')
        layers = list(wms.contents)
        lookup = self._load_geocat_lookup()

        for layer, geocat_id in self._valid_mapping(lookup, layers):
            try:
                metadata = self.csw.get_ckan_metadata_by_id(geocat_id)
                metadata['layer'] = layer
            except:
                log.exception(
                    'Metadata for layer %s (id: %s) could not be found'
                    % (layer, geocat_id)
                )
            yield metadata


    def _load_geocat_lookup(self):
        metadata = self.csw.get_ckan_metadata('wms.geo.admin.ch')
        return dict(
            zip(
                metadata['layers'],
                metadata['layer_geocat_ids']
            )
        )
    
    def _valid_mapping(self, lookup, layers):
        """
        Filters the geocat mapping based on the available WMS layers
        """
        for key in lookup:
            if key in layers:
                print "Key: %s" % key
                yield key, lookup[key]

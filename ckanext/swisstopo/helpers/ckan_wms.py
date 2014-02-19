# Query Geocat using ckan_csw.py
# Insert or update CKAN dataset

from owslib.wms import WebMapService
import ckan_csw
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class WmsLayerParser(object):
    """ Allows parsing of WMS layers as datasets """

    def __init__(self):
        self.csw = None

    def parse(self, url):
        """
        Parses the available WMS layers and maps them to geocat
        The validated result is returned using a generator
        """
        wms = wms = WebMapService(url, version='1.1.1')
        layers = list(wms.contents)
        lookup = self._load_lookup()

        for layer, key in self._valid_mapping(lookup, layers):
            try:
                metadata = {
                    'de': self.csw.get_ckan_metadata_by_id(key, 'de').copy(),
                    'fr': self.csw.get_ckan_metadata_by_id(key, 'fr').copy(),
                    'it': self.csw.get_ckan_metadata_by_id(key, 'it').copy(),
                    'en': self.csw.get_ckan_metadata_by_id(key, 'en').copy(),
                }
            except Exception:
                log.exception(
                    'Metadata for layer %s (id: %s) could not be found'
                    % (layer, key)
                )
                continue
            yield layer, metadata

    def _load_lookup(self):
        """
        Abstract method to load the lookup dict
        """
        raise NotImplementedError

    def _valid_mapping(self, lookup, layers):
        """
        Filters the geocat mapping based on the available WMS layers
        """
        for key in lookup:
            if key in layers:
                log.debug("Key: %s" % key)
                yield key, lookup[key]


class SwisstopoWmsLayerParser(WmsLayerParser):
    def __init__(self):
        self.csw = ckan_csw.SwisstopoCkanMetadata()
    
    def _load_lookup(self):
        metadata = self.csw.get_ckan_metadata('wms.geo.admin.ch', 'de')
        return dict(
            zip(
                metadata['layers'],
                metadata['layer_geocat_ids']
            )
        )

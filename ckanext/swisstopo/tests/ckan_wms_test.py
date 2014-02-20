import unittest
from mock import Mock
from ckanext.swisstopo.helpers import ckan_wms


class SwisstopoWmsLayerParserTest(unittest.TestCase):
    def setUp(self):
        self.layers = {
            'test.layer1': '123-567',
            'spam.egg': 'dead-beef',
            'foo.bar.baz': 'hax0r-l33t'
        }
        self.metadata = {
            'name': 'test',
            'license': 'cc-by'
        }
        self.wms = ckan_wms.SwisstopoWmsLayerParser()
        self.wms._get_layers_from_wms = Mock(return_value=self.layers.keys())
        self.wms.csw.get_ckan_metadata = Mock(
            return_value={
                'layers': self.layers.keys(),
                'layer_geocat_ids': self.layers.values()
            }
        )
        self.wms.csw.get_ckan_metadata_by_id = Mock(return_value=self.metadata)

    def test_parse(self):
        idx = 0
        for layername, metadata in self.wms.parse('https://wms.geo.admin.ch'):
            self.assertEqual(layername, self.layers.keys()[idx])
            self.assertEqual(len(metadata), 4)
            self.assertEqual(metadata['de'], self.metadata)
            idx = idx + 1

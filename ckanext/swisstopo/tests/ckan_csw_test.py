import unittest
import os
from mock import Mock
from ckanext.swisstopo.helpers import ckan_csw
from lxml import etree


class CkanMetadataTest(unittest.TestCase):
    def test_init(self):
        ckan = ckan_csw.CkanMetadata(
            url='http://www.geocat.ch/geonetwork/srv/deu/csw?',
            schema='http://www.geocat.ch/2008/che'
        )
        self.assertEqual(ckan.schema, 'http://www.geocat.ch/2008/che')

    def test_namespaces_available(self):
        self.assertEquals(17, len(ckan_csw.namespaces))
        for index, item in ckan_csw.namespaces.iteritems():
            self.assertIsInstance(index, str)
            self.assertIsInstance(item, str)


class SwisstopoCkanMetadataTest(unittest.TestCase):
    def setUp(self):
        self.test_xml = etree.parse(os.path.dirname(__file__) +
                                    '/swissboundaries_csw.test.xml')
        self.swisstopo = ckan_csw.SwisstopoCkanMetadata()
        self.swisstopo.get_xml = Mock(return_value=self.test_xml)

    def test_get_attribute_license(self):
        license = self.swisstopo.get_attribute('swissboundaries3D', 'license')
        self.assertIsInstance(license, ckan_csw.StringAttribute)
        self.assertEquals(
            license.get_value(),
            'http://www.toposhop.admin.ch/de/shop/terms/use/finished_products'
        )

    def test_get_attribute_maintainer(self):
        maintainer = self.swisstopo.get_attribute('swissboundaries3D',
                                                  'maintainer')
        self.assertIsInstance(maintainer, ckan_csw.CombinedAttribute)
        for attr in maintainer._config:
            self.assertIsInstance(attr, ckan_csw.XPathTextAttribute)
            # self.assertEquals(attr.get_value(self.test_xml), 'test')
        # self.assertEquals(maintainer.get_value(self.test_xml, ' '), 'Blubb')


class AttributeTest(unittest.TestCase):
    def test_get_value(self):
        attr = ckan_csw.Attribute('config')
        self.assertRaises(NotImplementedError, attr.get_value)


class StringAttributeTest(unittest.TestCase):
    def test_get_value(self):
        attr = ckan_csw.StringAttribute('my test input')
        self.assertEquals('my test input', attr.get_value())


class XmlAttributeTest(unittest.TestCase):
    def setUp(self):
        xml_input = etree.parse(os.path.dirname(__file__) + '/test.xml')
        self.test_xml = xml_input.getroot()

    def remove_all_whitespace(self, str):
        return ''.join(str.split())

    def test_xml_attribute_get_value_init(self):
        attr = ckan_csw.XmlAttribute('', xml=self.test_xml)
        xml_string = open(os.path.dirname(__file__) + '/test.xml', 'r').read()

        xml_string = self.remove_all_whitespace(xml_string)
        attr_value = self.remove_all_whitespace(attr.get_value())

        self.assertEquals(xml_string, attr_value)

    def test_xml_attribute_get_value_call(self):
        attr = ckan_csw.XmlAttribute('')
        xml_string = open(os.path.dirname(__file__) + '/test.xml', 'r').read()

        xml_string = self.remove_all_whitespace(xml_string)
        attr_value = self.remove_all_whitespace(
            attr.get_value(xml=self.test_xml)
        )

        self.assertEquals(xml_string, attr_value)

if __name__ == '__main__':
    unittest.main()

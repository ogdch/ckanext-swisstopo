import traceback
from owslib.csw import CatalogueServiceWeb
from lxml import etree
import logging
log = logging.getLogger(__name__)

namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'che': 'http://www.geocat.ch/2008/che',
    'csw': 'http://www.opengis.net/cat/csw/2.0.2',
    'dc' : 'http://purl.org/dc/elements/1.1/',
    'dct': 'http://purl.org/dc/terms/',
    'dif': 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/',
    'fgdc': 'http://www.opengis.net/cat/csw/csdgm',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gml': 'http://www.opengis.net/gml',
    'ogc': 'http://www.opengis.net/ogc',
    'ows': 'http://www.opengis.net/ows',
    'rim': 'urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'xs' : 'http://www.w3.org/2001/XMLSchema',
    'xs2': 'http://www.w3.org/XML/Schema',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

class Attribute(object):
    def __init__(self, config, **kwargs):
        self._config = config
        self.env = kwargs

    def get_value(self, **kwargs):
        """ Abstract method to return the value of the attribute """
        raise NotImplementedError

class StringAttribute(Attribute):
    def get_value(self, **kwargs):
        return self._config

class XmlAttribute(Attribute):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        xml = self.env['xml']
        return etree.tostring(xml)

class XPathAttribute(Attribute):
    def get_element(self, xml, xpath):
        return xml.xpath(xpath, namespaces=namespaces)[0]

    def get_value(self, **kwargs):
        self.env.update(kwargs)
        xml = self.env['xml']

        lang = self.env['lang']
        xpath = self._config.replace('#DE', '#' + lang.upper())
        log.debug("Lang: %s, XPath: %s" % (lang, xpath))

        try:
            # this should probably return a XPathTextAttribute
            value = self.get_element(xml, xpath)
        except Exception as e:
            log.exception(e)
            value = ''
        return value

class XPathMultiAttribute(XPathAttribute):
    def get_element(self, xml, xpath):
        return xml.xpath(xpath, namespaces=namespaces)

class XPathTextAttribute(XPathAttribute):
    def get_value(self, **kwargs):
        value = super(XPathTextAttribute, self).get_value(**kwargs)
        return value.text if hasattr(value, 'text') else value

class XPathMultiTextAttribute(XPathMultiAttribute):
    def get_value(self, **kwargs):
        value = super(XPathMultiTextAttribute, self).get_value(**kwargs)
        return value.text if hasattr(value, 'text') else value

class CombinedAttribute(Attribute):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        value = ''
        separator = self.env['separator'] if self.env.has_key('separator') else ' '
        for attribute in self._config:
            new_value = attribute.get_value(**kwargs)
            value = value + attribute.get_value(**kwargs) + separator if new_value != None else value
        return value.strip(separator)

class MultiAttribute(Attribute):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        value = ''
        separator = self.env['separator'] if self.env.has_key('separator') else ' '
        for attribute in self._config:
            new_value = attribute.get_value(**kwargs)
            try:
                iterator = iter(new_value)
                for inner_attribute in iterator:
                    # it should be possible to call inner_attribute.get_value and the right thing(tm) happens'
                    value = value + (inner_attribute.text if hasattr(inner_attribute, 'text') else inner_attribute) + separator
            except TypeError:
                value = value + new_value + separator
        return value.strip(separator)

class ArrayAttribute(Attribute):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        value = []
        for attribute in self._config:
            new_value = attribute.get_value(**kwargs)
            try:
                iterator = iter(new_value)
                for inner_attribute in iterator:
                    # it should be possible to call inner_attribute.get_value and the right thing(tm) happens'
                    value.append(inner_attribute.text if hasattr(inner_attribute, 'text') else inner_attribute)
            except TypeError:
                value.append(new_value)
        return value

class FirstInOrderAttribute(CombinedAttribute):
    def get_value(self, **kwargs):
        for attribute in self._config:
            value = attribute.get_value(**kwargs)
            if value != '':
                return value
        return ''

class CkanMetadata(object):
    """ Provides general access to CSW for CKAN """
    def __init__(self, url, schema, version='2.0.2', lang='en-US'):
        self.schema = schema
        self.catalog = CatalogueServiceWeb(url, lang, version, timeout=10, skip_caps=True)
        self.metadata = dict.fromkeys([
            'id', 
            'name', 
            'title', 
            'url', 
            'author', 
            'author_email', 
            'maintainer', 
            'maintainer_email',
            'license_url',
            'version',
            'notes',
            'tags',
            'metadata_url',
            'metadata_raw',
        ])

    def get_by_search(self, searchterm, propertyname='csw:AnyText'):
        """ Returns the found csw dataset with the given searchterm """
        self.catalog.getrecords(keywords=[searchterm], propertyname=propertyname)
        if self.catalog.response == None or self.catalog.results['matches'] == 0:
            raise DatasetNotFoundError("No dataset for the given searchterm '%s' (%s) found" % (searchterm, propertyname))
        return self.catalog.records

    def get_by_id(self, id):
        """ Returns the csw dataset with the given id """
        self.catalog.getrecordbyid(id=[id], outputschema=self.schema)
        return self.catalog.response

    def get_id_by_dataset_name(self, dataset_name):
        """ 
            Returns the id of a dataset identified by it's name.
            If there are multiple datasets with the given name,
            only the id of the first one is returned.
        """
        return self.get_by_search(dataset_name, 'title').itervalues().next().identifier

    def get_attribute(self, dataset_name, ckan_attribute):
        """ Abstract method to define the mapping of a ckan attribute to a csw attribute """
        raise NotImplementedError

    def get_xml(self, id):
        dataset_xml_string = self.get_by_id(id)
        if dataset_xml_string == None:
            raise DatasetNotFoundError("Dataset with id %s not found" % id)
        return dataset_xml_string

    def get_ckan_metadata(self, dataset_name, language='de'):
        """ Returns the requested dataset mapped to CKAN attributes """
        id = self.get_id_by_dataset_name(dataset_name)
        log.debug("Dataset ID: %s" % id)

        dataset_xml = etree.fromstring(self.get_xml(id))
        for key in self.metadata:
            log.debug("Metadata key: %s" % key)
            attribute = self.get_attribute(dataset_name, key)
            self.metadata[key] = attribute.get_value(xml=dataset_xml, lang=language)
        return self.metadata


class SwisstopoCkanMetadata(CkanMetadata):
    """ Provides access to the csw service of swisstopo """

    default_mapping = {
        'id': XPathTextAttribute('.//gmd:fileIdentifier/gco:CharacterString'), 
        'name': XPathTextAttribute(".//gmd:identificationInfo//gmd:citation//gmd:title//gmd:textGroup/gmd:LocalisedCharacterString[@locale='#DE']"), 
        'title': XPathTextAttribute(".//gmd:identificationInfo//gmd:citation//gmd:alternateTitle//gmd:textGroup/gmd:LocalisedCharacterString[@locale='#DE']"), 
        'url': XPathTextAttribute(".//gmd:distributionInfo//gmd:transferOptions//gmd:onLine//gmd:linkage//che:URLGroup/che:LocalisedURL[@locale='#DE']"), 
        'author': CombinedAttribute([
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact//che:individualFirstName/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact//che:individualLastName/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact//gmd:organisationName//gmd:textGroup/gmd:LocalisedCharacterString[@locale='#DE']")
        ]),  
        'author_email': FirstInOrderAttribute([
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact[1]//gmd:CI_RoleCode[@codeListValue='author']/ancestor::gmd:pointOfContact//gmd:address//gmd:electronicMailAddress/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact[1]//gmd:CI_RoleCode[@codeListValue='originator']/ancestor::gmd:pointOfContact//gmd:address//gmd:electronicMailAddress/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact[1]//gmd:CI_RoleCode[@codeListValue='owner']/ancestor::gmd:pointOfContact//gmd:address//gmd:electronicMailAddress/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact[1]//gmd:CI_RoleCode[@codeListValue='pointOfContact']/ancestor::gmd:pointOfContact//gmd:address//gmd:electronicMailAddress/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact//gmd:address//gmd:electronicMailAddress/gco:CharacterString"),
        ]), 
        'maintainer': CombinedAttribute([
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact//che:individualFirstName/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact//che:individualLastName/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact//gmd:organisationName//gmd:textGroup/gmd:LocalisedCharacterString[@locale='#DE']")
        ]),  
        'maintainer_email': FirstInOrderAttribute([
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact[1]//gmd:CI_RoleCode[@codeListValue='publisher']/ancestor::gmd:pointOfContact//gmd:address//gmd:electronicMailAddress/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact[1]//gmd:CI_RoleCode[@codeListValue='custodian']/ancestor::gmd:pointOfContact//gmd:address//gmd:electronicMailAddress/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact[1]//gmd:CI_RoleCode[@codeListValue='distributor']/ancestor::gmd:pointOfContact//gmd:address//gmd:electronicMailAddress/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact[1]//gmd:CI_RoleCode[@codeListValue='pointOfContact']/ancestor::gmd:pointOfContact//gmd:address//gmd:electronicMailAddress/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact[1]//gmd:CI_RoleCode[@codeListValue='owner']/ancestor::gmd:pointOfContact//gmd:address//gmd:electronicMailAddress/gco:CharacterString"),
            XPathTextAttribute(".//gmd:identificationInfo//gmd:pointOfContact//gmd:address//gmd:electronicMailAddress/gco:CharacterString"),
        ]), 
        'license_url': StringAttribute('http://www.toposhop.admin.ch/de/shop/terms/use/finished_products'),
        'version': XPathTextAttribute(".//gmd:identificationInfo//gmd:citation//gmd:date/gco:Date"),
        'notes': XPathTextAttribute(".//gmd:identificationInfo//gmd:abstract//gmd:textGroup/gmd:LocalisedCharacterString[@locale='#DE']"),
        'tags': ArrayAttribute([XPathMultiTextAttribute(".//gmd:identificationInfo//gmd:descriptiveKeywords//gmd:keyword//gmd:textGroup/gmd:LocalisedCharacterString[@locale='#DE']")]),
        'metadata_url': StringAttribute(''),
        'metadata_raw': XmlAttribute(''),
    }

    known_datasets = {
        'swissboundaries3D': {
                'id': '86cb844f-296b-40cb-b972-5b1ae8028f7c',
                'mapping': default_mapping
        }
    }
    

    def __init__(self, url='http://www.geocat.ch/geonetwork/srv/eng/csw?', schema='http://www.geocat.ch/2008/che', version='2.0.2', lang='en-US'):
        super(SwisstopoCkanMetadata, self).__init__(url,schema,version,lang)

    def get_id_by_dataset_name(self, dataset_name):
        if (dataset_name in self.known_datasets):
            return self.known_datasets[dataset_name]['id']
        return super(SwisstopoCkanMetadata, self).get_id_by_dataset_name(dataset_name)
    
    def get_mapping(self, dataset_name):
        if dataset_name in self.known_datasets and 'mapping' in self.known_datasets[dataset_name]:
            return self.known_datasets[dataset_name]['mapping'];
        return self.default_mapping

    def get_attribute(self, dataset_name, ckan_attribute):
        mapping = self.get_mapping(dataset_name)
        if ckan_attribute in mapping:
            return mapping[ckan_attribute]
        raise AttributeMappingNotFoundError("No mapping found for attribute '%s'" % ckan_attribute) 

class DatasetNotFoundError(Exception):
    pass

class AttributeMappingNotFoundError(Exception):
    pass

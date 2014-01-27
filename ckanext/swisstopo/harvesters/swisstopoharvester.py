#n -*- coding: utf-8 -*-

import os
from ckan import model
from ckan.model import Session
from ckan.logic import get_action, action
from ckan.lib.helpers import json
from ckanext.harvest.harvesters.base import munge_tag
from ckan.lib.munge import munge_title_to_name

from ckanext.harvest.model import HarvestObject
from base import OGDCHHarvesterBase

from ckanext.swisstopo.helpers import ckan_csw
from ckanext.swisstopo.helpers import s3

import logging
log = logging.getLogger(__name__)


class SwisstopoHarvester(OGDCHHarvesterBase):
    '''
    The harvester for swisstopo
    '''

    HARVEST_USER = u'harvest'

    DATASETS = {
        'ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill': {
            'csw_query': 'swissboundaries3D Gemeindegrenzen',
        },
        'ch.swisstopo.swissboundaries3d-bezirk-flaeche.fill': {
            'csw_query': 'swissboundaries3D Bezirksgrenzen',
        },
        'ch.swisstopo.swissboundaries3d-kanton-flaeche.fill': {
            'csw_query': 'swissboundaries3D Kantonsgrenzen',
        },
        'ch.swisstopo.swissboundaries3d-land-flaeche.fill': {
            'csw_query': 'swissboundaries3D Landesgrenzen',
        },
        'ch.swisstopo.pixelkarte-farbe-pk1000.noscale': {
            'csw_query': 'Landeskarte 1:1 Mio.',
        },
        'ch.swisstopo-vd.ortschaftenverzeichnis_plz': {
            'csw_query': 'Amtliches Ortschaftenverzeichnis',
        }
    }

    LICENSE = {
        u'de': (
            u'Lizenz für Fertigprodukte',
            'http://www.toposhop.admin.ch/de/shop/terms/use/finished_products'
        ),
        u'fr': (
            u'Accord relatif aux produits finis',
            'http://www.toposhop.admin.ch/fr/shop/terms/use/finished_products'
        ),
        u'it': (
            u'Licenza per prodotti finiti',
            'http://www.toposhop.admin.ch/it/shop/terms/use/finished_products'
        ),
        u'en': (
            u'Licence for finished products',
            'http://www.toposhop.admin.ch/en/shop/terms/use/finished_products'
        ),
    }
    ORGANIZATION = {
        'de': {
            'name': u'Bundesamt für Landestopografie swisstopo',
            'description': (
                u'Das Kompetenzzentrum der Schweizerischen '
                u'Eidgenossenschaft für Geoinformation, d.h. '
                u'für die Beschreibung, Darstellung und Archivierung '
                u'von raumbezogenen Geodaten.'
            ),
            'website': u'http://www.swisstopo.admin.ch/'
        },
        'fr': {
            'name': u'Office fédéral de topographie swisstopo',
            'description': (
                u'Le centre de compétence de la Confédération suisse '
                u'pour les informations géographiques, c\'est-à-dire pour '
                u'la description, la représentation et l’archivage de '
                u'données à référence spatiale.'
            )
        },
        'it': {
            'name': u'Ufficio federale di topografia swisstopo',
            'description': (
                u'Il centro d’eccellenza della Confederazione Elvetica '
                u'per geoinformazione, cioè per la descrizione, '
                u'rappresentazione e archiviazione dei dati '
                u'georeferenziati (geodati).'
            )
        },
        'en': {
            'name': u'Federal Office of Topography swisstopo',
            'description': (
                u'The centre of competence for the Swiss Confederation '
                u'responsible for geographical reference data, for instance '
                u'the description, representation and archiving of ',
                u'geographic spatial data.'
            )
        }
    }
    GROUPS = {
        u'de': [u'Raum und Umwelt'],
        u'fr': [u'Espace et environnement'],
        u'it': [u'Territorio e ambiente'],
        u'en': [u'Territory and environment']
    }

    def info(self):
        return {
            'name': 'swisstopo',
            'title': 'Swisstopo',
            'description': 'Harvests the swisstopo data',
            'form_config_interface': 'Text'
        }

    def gather_stage(self, harvest_job):
        log.debug('In SwisstopoHarvester gather_stage')

        ids = []
        for dataset_name, dataset in self.DATASETS.iteritems():
            csw = ckan_csw.SwisstopoCkanMetadata()
            metadata = csw.get_ckan_metadata(
                dataset['csw_query'], 'de'
            ).copy()
            metadata_fr = csw.get_ckan_metadata(
                dataset['csw_query'], 'fr'
            ).copy()
            metadata_it = csw.get_ckan_metadata(
                dataset['csw_query'], 'it'
            ).copy()
            metadata_en = csw.get_ckan_metadata(
                dataset['csw_query'], 'en'
            ).copy()
            log.debug(metadata)

            metadata['translations'] = self._generate_term_translations()
            log.debug("Translations: %s" % metadata['translations'])

            metadata_trans = {
                u'de': metadata,
                u'fr': metadata_fr,
                u'it': metadata_it,
                u'en': metadata_en,
            }
            metadata['translations'].extend(
                self._generate_metadata_translations(metadata_trans)
            )

            metadata['resources'] = self._generate_resources_dict_array(
                dataset_name
            )
            log.debug(metadata['resources'])

            metadata['license_id'] = self.LICENSE['de'][0]
            metadata['license_url'] = self.LICENSE['de'][1]

            metadata['layer_name'] = dataset_name

            obj = HarvestObject(
                guid=metadata['id'],
                job=harvest_job,
                content=json.dumps(metadata)
            )
            obj.save()
            log.debug('adding ' + dataset_name + ' to the queue')
            ids.append(obj.id)

        return ids

    def fetch_stage(self, harvest_object):
        log.debug('In SwisstopoHarvester fetch_stage')

        # Get the URL
        log.debug(json.loads(harvest_object.content))
        name = json.loads(harvest_object.content)['name']
        log.debug(harvest_object.content)

        # Get contents
        try:
            harvest_object.save()
            log.debug('successfully processed ' + name)
            return True
        except Exception, e:
            log.exception(e)
            raise

    def import_stage(self, harvest_object):
        log.debug('In SwisstopoHarvester import_stage')

        if not harvest_object:
            log.error('No harvest object received')
            return False

        try:
            package_dict = json.loads(harvest_object.content)

            package_dict['id'] = harvest_object.guid
            package_dict['name'] = munge_title_to_name(
                package_dict['layer_name']
            )
            user = model.User.get(self.HARVEST_USER)
            context = {
                'model': model,
                'session': Session,
                'user': self.HARVEST_USER
                }

            # Find or create group the dataset should get assigned to
            package_dict['groups'] = self._find_or_create_groups(context)

            # Find or create the organization
            # the dataset should get assigned to
            package_dict['owner_org'] = self._find_or_create_organization(
                context
            )

            # Save license url in extras
            extras = []
            if 'license_url' in package_dict:
                extras.append(('license_url', package_dict['license_url']))
            package_dict['extras'] = extras

            package = model.Package.get(package_dict['id'])
            model.PackageRole(
                package=package,
                user=user,
                role=model.Role.ADMIN
            )

            log.debug(
                'Save or update package %s (%s)'
                % (package_dict['name'], package_dict['id'])
            )
            self._create_or_update_package(package_dict, harvest_object)

            log.debug('Save or update term translations')
            self._submit_term_translations(context, package_dict)
            Session.commit()

        except Exception, e:
            log.exception(e)
            raise
        return True

    def _find_or_create_groups(self, context):
        group_name = self.GROUPS['de'][0]
        data_dict = {
            'id': group_name,
            'name': munge_title_to_name(group_name),
            'title': group_name
            }
        try:
            group = get_action('group_show')(context, data_dict)
        except:
            group = get_action('group_create')(context, data_dict)
            log.info('created the group ' + group['id'])
        group_ids = []
        group_ids.append(group['id'])
        return group_ids

    def _find_or_create_organization(self, context):
        try:
            data_dict = {
                'permission': 'edit_group',
                'id': munge_title_to_name(self.ORGANIZATION['de']['name']),
                'name': munge_title_to_name(self.ORGANIZATION['de']['name']),
                'title': self.ORGANIZATION['de']['name'],
                'description': self.ORGANIZATION['de']['description'],
                'extras': [
                    {
                        'key': 'website',
                        'value': self.ORGANIZATION['de']['website']
                    }
                ]
            }
            org = get_action('organization_show')(context, data_dict)
        except:
            org = get_action('organization_create')(context, data_dict)
        return org['id']

    def _generate_term_translations(self):
        '''
        Generate term translatations for groups, organizations and metadata
        '''
        try:
            translations = []

            for lang, lic in self.LICENSE.items():
                if lang != u'de':
                    translations.append({
                        'lang_code': lang,
                        'term': self.LICENSE[u'de'][0],
                        'term_translation': lic[0]
                        })
                    translations.append({
                        'lang_code': lang,
                        'term': self.LICENSE[u'de'][1],
                        'term_translation': lic[1]
                        })

            for lang, org in self.ORGANIZATION.items():
                if lang != 'de':
                    for field in ['name', 'description']:
                        translations.append({
                            'lang_code': lang,
                            'term': self.ORGANIZATION['de'][field],
                            'term_translation': org[field]
                        })

            for lang, groups in self.GROUPS.iteritems():
                if lang != u'de':
                    for idx, group in enumerate(self.GROUPS[lang]):
                        translations.append({
                            'lang_code': lang,
                            'term': self.GROUPS[u'de'][idx],
                            'term_translation': group
                            })

            return translations

        except Exception, e:
            log.exception(e)
            raise

    def _generate_metadata_translations(self, metadata_translations):
        try:
            translations = []

            for lang, metadata in metadata_translations.items():
                if lang != u'de':
                    for key, term in metadata_translations[lang].items():
                        if term and term != metadata_translations[u'de'][key]:
                            de_term = metadata_translations[u'de'][key]
                            if (key == 'tags' and len(term) == len(de_term)):
                                for idx, subterm in enumerate(term):
                                    translations.append({
                                        'lang_code': lang,
                                        'term': munge_tag(de_term[idx]),
                                        'term_translation': munge_tag(subterm)
                                    })
                            else:
                                translations.append({
                                    'lang_code': lang,
                                    'term': metadata_translations[u'de'][key],
                                    'term_translation': term
                                })
            return translations

        except Exception, e:
            log.exception(e)
            raise

    def _submit_term_translations(self, context, package_dict):
        for translation in package_dict['translations']:
            log.debug(translation)
            action.update.term_translation_update(context, translation)

    def _generate_resources_dict_array(self, dataset_name):
        try:
            resources = []
            prefix = dataset_name + u'/'
            s3_helper = s3.S3()

            for key in s3_helper.list(prefix=prefix):
                if key.size > 0:
                    resources.append({
                        'url': key.generate_url(
                            0,
                            query_auth=False,
                            force_http=True
                        ),
                        'name': os.path.basename(key.name),
                        'format': self._guess_format(key.name)
                    })
            return resources
        except Exception, e:
            log.exception(e)
            raise

    def _guess_format(self, file_name):
        '''
        Return the format for a given full filename
        '''
        _, file_extension = os.path.splitext(file_name.lower())
        return file_extension[1:]

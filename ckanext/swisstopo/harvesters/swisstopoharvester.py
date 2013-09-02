#n -*- coding: utf-8 -*-

import random
import os
import shutil
import tempfile
import zipfile
from pprint import pprint
from collections import defaultdict

from ckan.lib.base import c
from ckan import model
from ckan.model import Session, Package
from ckan.logic import ValidationError, NotFound, get_action, action
from ckan.lib.helpers import json

from ckanext.harvest.model import HarvestJob, HarvestObject, HarvestGatherError, HarvestObjectError
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
        u'de': u'Lizenz für Fertigprodukte',
        u'fr': u'Accord relatif aux produits finis',
        u'it': u'Licenza per prodotti finiti',
        u'en': u'Licence for finished products',
    }
    ORGANIZATION = {
        u'de': u'Bundesamt für Landestopografie swisstopo',
        u'fr': u'Office fédéral de topographie swisstopo',
        u'it': u'Ufficio federale di topografia swisstopo',
        u'en': u'Federal Office of Topography swisstopo',
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
            csw = ckan_csw.SwisstopoCkanMetadata();
            metadata = csw.get_ckan_metadata(dataset['csw_query'], u'de').copy()
            metadata_fr = csw.get_ckan_metadata(dataset['csw_query'], u'fr').copy()
            metadata_it = csw.get_ckan_metadata(dataset['csw_query'], u'it').copy()
            metadata_en = csw.get_ckan_metadata(dataset['csw_query'], u'en').copy()
            log.debug(metadata)

            metadata['translations'] = self._generate_term_translations()
            log.debug("Translations: %s" % metadata['translations'])

            metadata_trans = {
                u'de': metadata,
                u'fr': metadata_fr,
                u'it': metadata_it,
                u'en': metadata_en,
            }
            metadata['translations'].extend(self._generate_metadata_translations(metadata_trans))

            metadata['resources'] = self._generate_resources_dict_array(dataset_name)
            log.debug(metadata['resources'])

            metadata['license_id'] = self.LICENSE['de']
            metadata['layer_name'] = dataset_name

            obj = HarvestObject(
                guid = metadata['id'],
                job = harvest_job,
                content = json.dumps(metadata)
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
            package_dict['name'] = self._gen_new_name(package_dict['layer_name'])
            user = model.User.get(self.HARVEST_USER)
            context = {
                'model': model,
                'session': Session,
                'user': self.HARVEST_USER
                }

            # Find or create group the dataset should get assigned to
            package_dict['groups'] = self._find_or_create_groups(context)

            # Find or create the organization the dataset should get assigned to
            package_dict['owner_org'] = self._find_or_create_organization(context)

            package = model.Package.get(package_dict['id'])
            pkg_role = model.PackageRole(package=package, user=user, role=model.Role.ADMIN)

            log.debug('Save or update package %s (%s)' % (package_dict['name'],package_dict['id']))
            result = self._create_or_update_package(package_dict, harvest_object)

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
            'name': self._gen_new_name(group_name),
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
                'id': self._gen_new_name(self.ORGANIZATION[u'de']),
                'name': self._gen_new_name(self.ORGANIZATION[u'de']),
                'title': self.ORGANIZATION[u'de']
            }
            organization = get_action('organization_show')(context, data_dict)
        except:
            organization = get_action('organization_create')(context, data_dict)
        return organization['id']

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
                        'term': self.LICENSE[u'de'],
                        'term_translation': lic
                        })

            for lang, org in self.ORGANIZATION.items():
                if lang != u'de':
                    translations.append({
                        'lang_code': lang,
                        'term': self.ORGANIZATION[u'de'],
                        'term_translation': org
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
                            if key == 'tags' and len(term) == len(metadata_translations[u'de'][key]):
                                for idx, subterm in enumerate(term):
                                    translations.append({
                                        'lang_code': lang,
                                        'term': self._gen_new_name(metadata_translations[u'de'][key][idx]),
                                        'term_translation': self._gen_new_name(subterm)
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
                        'url': key.generate_url(0, query_auth=False,
                            force_http=True),
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


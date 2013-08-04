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
from ckanext.harvest.harvesters import HarvesterBase

from ckanext.swisstopo.helpers import ckan_csw
from ckanext.swisstopo.helpers import s3

import logging
log = logging.getLogger(__name__)

class SwisstopoHarvester(HarvesterBase):
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
    }

    FILES_BASE_URL = 'http://opendata-ch.s3.amazonaws.com'

    ORGANIZATION = {
        'de': u'Bundesamt für Landestopografie swisstopo',
        'fr': u'Office fédéral de topographie swisstopo',
        'it': u'Ufficio federale di topografia swisstopo',
        'en': u'Federal Office of Topography swisstopo',
    }
    GROUPS = {
        'de': [u'Raum und Umwelt'],
        'fr': [u'Espace et environnement'],
        'it': [u'Territorio e ambiente'],
        'en': [u'Territory and environment']
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
            metadata = csw.get_ckan_metadata(dataset['csw_query'])
            log.debug(metadata)
            
            metadata['translations'] = self._generate_term_translations()
            log.debug("Translations: %s" % metadata['translations'])

            metadata['resources'] = self._generate_resources_dict_array(dataset_name)
            log.debug(metadata['resources'])

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
    
    def import_stage(self, harvest_object):
        log.debug('In SwisstopoHarvester import_stage')

        if not harvest_object:
            log.error('No harvest object received')
            return False
        
        try:
            package_dict = json.loads(harvest_object.content)

            package_dict['id'] = harvest_object.guid
            package_dict['name'] = self._gen_new_name(package_dict['title'])

            tags = package_dict['tags']
            package_dict['tags'] = []
            package_dict['tags'].extend([t for t in tags.split()])

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
                'id': self._gen_new_name(self.ORGANIZATION['de']),
                'name': self._gen_new_name(self.ORGANIZATION['de']),
                'title': self.ORGANIZATION['de']
            }
            organization = get_action('organization_show')(context, data_dict)
        except:
            organization = get_action('organization_create')(context, data_dict)
        return organization['id']

    def _generate_term_translations(self):
        '''
        '''
        try:
            translations = []

            for k,v in self.ORGANIZATION.items():
                if k != u'de':
                    translations.append({
                        'lang_code': k,
                        'term': self.ORGANIZATION[u'de'],
                        'term_translation': v
                        })

            for k,v in self.GROUPS.items():
                if k != u'de':
                    translations.append({
                        'lang_code': k,
                        'term': self.GROUPS[u'de'],
                        'term_translation': v
                        })

            return translations


        except Exception, e:
            log.exception(e)
            return []

    def _submit_term_translations(self, context, package_dict):
        for translation in package_dict['translations']:
            action.update.term_translation_update(context, translation)
                
    def _generate_resources_dict_array(self, dataset_name):
        try:
            resources = []
            prefix = dataset_name + u'/'
            s3_helper = s3.S3()
            for file in s3_helper.list(prefix=prefix):
                resources.append({
                    'url': self.FILES_BASE_URL + '/' + file,
                    'name': file.replace(prefix, u''),
                    'format': self._guess_format(file)
                })
            return resources
        except Exception, e:
            log.exception(e)
            return []

    def _guess_format(self, file_name):
        '''
        Return the format for a given full filename
        '''
        _, file_extension = os.path.splitext(file_name.lower())
        return file_extension[1:]


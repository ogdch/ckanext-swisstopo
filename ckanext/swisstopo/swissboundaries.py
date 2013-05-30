import ckanclient
import random
import os
import shutil
import tempfile
import zipfile
from pprint import pprint
from collections import defaultdict
import ckan_csw

API_KEY = p.toolkit.asbool(config.get('ckanext.swisstopo.api_key', ''))
BASE_LOCATION = p.toolkit.asbool(config.get('ckanext.swisstopo.base_location', ''))

ckan = ckanclient.CkanClient(api_key=API_KEY, base_location=BASE_LOCATION)

def create_dataset(name, tags, description, metadata):
    dataset_name = name + '_' + str(random.randint(1000000, 9999999999))
    dataset_entity = {
        'name': dataset_name,
        'title': name + ' - ' + metadata['title'],
        'tags': tags + ' ' + metadata['tags'],
        'notes': metadata['notes'],
        'url': metadata['url'],
        'author': metadata['author'],
        'author_email': metadata['author_email'],
        'maintainer': metadata['maintainer'],
        'maintainer_email': metadata['maintainer_email'],
        'license': metadata['license'],
    }
    return dataset_entity

def extract_file(zipped_file, name, extract_path):
    (dirname, filename) = os.path.split(name)
    new_path = os.path.join(extract_path, dirname)
    extracted_filename = os.path.join(extract_path, name)
    if not os.path.exists(new_path):
      	os.makedirs(new_path)
    fd = open(extracted_filename,"w")
    fd.write(zipped_file.read(name))
    fd.close()
    return extracted_filename

# Copy the file
origin_file = '/home/www-data/swissBOUNDARIES3D080312.zip'
origin_path, file_name = os.path.split(origin_file)
temp_dir = tempfile.mkdtemp()
shutil.copy(origin_file, temp_dir);
temporary_file = os.path.join(temp_dir, file_name) 

csw = ckan_csw.SwisstopoCkanMetadata();
metadata = csw.get_ckan_metadata('swissboundaries3D')

aggregates = defaultdict(list)
# Unzip the file
zipped_file = zipfile.ZipFile(temporary_file)
for name in zipped_file.namelist():
    (dirname, filename) = os.path.split(name)
    pure_name, file_extension = os.path.splitext(filename)
    dataset_name = pure_name.lower().replace(".","-")
    if file_extension not in ['.pdf']:
    	print "Extracting " + name
        extracted_filename = extract_file(zipped_file, name, temp_dir)
        resource = {
            'filename': extracted_filename,
            'title': 'swissboundaries3D - ' + filename, 
            'description': 'swissboundaries ' + file_extension + ' file',
            'format': file_extension[1:]
        }
        aggregates[dataset_name].append(resource)


for key, aggregate in aggregates.iteritems():
    dataset = create_dataset(key, 'swissboundaries Verwaltungseinheiten', 'swissboundaries ' + key, metadata)
    ckan.package_register_post(dataset)

    for resource in aggregate:
        pprint(resource)
        try:
            dataset = ckan.add_package_resource(dataset['name'], resource['filename'], name=resource['title'], resource_type='data', format=resource['format'], description=resource['description'])
        except ValueError as e:
            print e
    pprint(dataset)

shutil.rmtree(temp_dir);

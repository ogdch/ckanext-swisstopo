import ckanclient
import sys
from pprint import pprint

API_KEY = p.toolkit.asbool(config.get('ckanext.swisstopo.api_key', ''))
BASE_LOCATION = p.toolkit.asbool(config.get('ckanext.swisstopo.base_location', ''))

ckan = ckanclient.CkanClient(api_key=API_KEY, base_location=BASE_LOCATION)

package_list = ckan.package_register_get()

if (len(package_list) <= 0):
    print "- No datasets found -"
    sys.exit()

package_list.sort()
for index, package in enumerate(package_list):
    print str(index+1) +  ") " + package

try:
    selected_dataset = int(raw_input("Select dataset (1-" + str(len(package_list)) + "): "))
    if not selected_dataset in range(1, len(package_list) + 1):
        raise ValueError("number is out of range (1-" + str(len(package_list)) + ")")
    dataset_name = package_list[selected_dataset-1]
except ValueError as detail:
    print "Invalid dataset number: ", detail
    sys.exit()

package_entity = ckan.package_entity_get(dataset_name)


max_key_len = len(max(package_entity.keys(), key=len))
for key, value in package_entity.iteritems():
    print str(key).ljust(max_key_len) + "\t\t" + str(value)


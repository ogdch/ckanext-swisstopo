import ckanclient
import sys
from optparse import OptionParser
from pprint import pprint

API_KEY = p.toolkit.asbool(config.get('ckanext.swisstopo.api_key', ''))
BASE_LOCATION = p.toolkit.asbool(config.get('ckanext.swisstopo.base_location', ''))

ckan = ckanclient.CkanClient(api_key=API_KEY, base_location=BASE_LOCATION)

parser = OptionParser()
parser.add_option("-s", "--search", dest="search_term", help="search packages with TERM", metavar="TERM")
parser.add_option("-t", "--tag", dest="search_tag", help="Search packages with tag TAG", metavar="TAG")
(options, args) = parser.parse_args()

results = []
if options.search_term:
    search_results = ckan.package_search(options.search_term);
    results = search_results['results']
elif options.search_tag:
    search_results = ckan.package_search('tags:' + options.search_tag);
    results = search_results['results']
else:
    parser.error("No valid argument supplied")

for package_name in results:
    print package_name
    last_message = ckan.package_entity_delete(package_name)
    print last_message

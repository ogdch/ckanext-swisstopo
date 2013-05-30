import ckanclient
import urllib
import os
from  httplib2 import Http
from datetime import datetime

API_KEY = p.toolkit.asbool(config.get('ckanext.swisstopo.api_key', ''))
BASE_LOCATION = p.toolkit.asbool(config.get('ckanext.swisstopo.base_location', ''))

ckan = ckanclient.CkanClient(api_key=API_KEY, base_location=BASE_LOCATION)

now = datetime.now()

# Register the dataset.
dataset_name = 's3_test_dataset_' + now.strftime("%Y-%m-%d_%H-%M-%S")
# csv_url = 'https://commondatastorage.googleapis.com/ckannet-storage/2011-11-24T112025/AfTerFibre_21nov2011.csv'
dataset_entity = {
    'name': dataset_name,
    'tags': 'test',
    'notes': 'Notes about the test',
    }

package_response = ckan.package_register_post(dataset_entity)
print "package_response start"
print package_response
print "package_response end"

# Download the file
# file_name = csv_url.split('/')[-1]
file_name = 'sample.csv'
# urllib.urlretrieve (csv_url, file_name)

# Upload the file
res1, res2 = ckan.upload_file(file_name)
print res1
print res2

# -------------

# import ckanclient
# import urllib
# 
# ckan = ckanclient.CkanClient(api_key=API_KEY, base_location=BASE_LOCATION)
# 
# # dataset_name = 'phils_dataset_2013-02-19_23-44-42'
# dataset_name = 'new_liip_dataset'
# # file_name = 'sample.csv'
# # file_name = 'http://ckan.liip.ch.s3.amazonaws.com/2013-02-19T234442/sample.csv'
# # res1 = ckan.add_package_resource(dataset_name, file_name, resource_type='csv', description='Some CSV')
# 
# res1 = ckan.add_package_resource(dataset_name, 'sample.csv', resource_type='data', description='this-is-a-description')
# print res1
# res2 = ckan.add_package_resource(dataset_name, 'http://ckan.liip.ch.s3.amazonaws.com/2013-02-20T003611/sample.csv', name='Foo', resource_type='metadata', format='csv')
# print res2

# -------------

# url = 'http://ckan.liip.ch.s3.amazonaws.com/'

# from poster.encode import multipart_encode
# from poster.streaminghttp import register_openers
# import urllib2

# register_openers()

# datagen, headers = multipart_encode({
#     'key': '2013-02-19T224240/sample.csv',
#     'acl': 'public-read',
#     'AWSAccessKeyId': 'AKIAIIHWI2WETQQMAW5Q',
#     'policy': 'eyJleHBpcmF0aW9uIjogIjIwMTMtMDItMjBUMTc6NDI6MzhaIiwKImNvbmRpdGlvbnMiOiBbeyJ4LWFtei1tZXRhLXVwbG9hZGVkLWJ5IjogIjc0NmIyYzU4LWU3NGYtNDZhNy1hMzhjLTA2Nzg3YjA2NDBhZSJ9LHsiYnVja2V0IjogImNrYW4ubGlpcC5jaCJ9LHsia2V5IjogIjIwMTMtMDItMTlUMjI0MjQwL3NhbXBsZS5jc3YifSx7ImFjbCI6ICJwdWJsaWMtcmVhZCJ9LHsic3VjY2Vzc19hY3Rpb25fcmVkaXJlY3QiOiAiaHR0cDovLzE4NS4xNC4xODYuMTE6NTAwMC9zdG9yYWdlL3VwbG9hZC9zdWNjZXNzX2VtcHR5P2xhYmVsPTIwMTMtMDItMTlUMjI0MjQwJTJGc2FtcGxlLmNzdiJ9LFsiY29udGVudC1sZW5ndGgtcmFuZ2UiLCAwLCA1MDAwMDAwMF0seyJ4LWFtei1zdG9yYWdlLWNsYXNzIjogIlNUQU5EQVJEIn1dfQ==',
#     'signature': 'RypkJqVhnpbfqDZlsWBU8vifSzE=',
#     'Content-Type': 'multipart/form-data',
#     'file': 'foobar,something,asdfjh'
#     # "image1": open("sample.csv", "r"),
# })
# request = urllib2.Request(url, datagen, headers)
# print request
# print urllib2.urlopen(request).read()

# Cleanup
# os.remove(file_name)

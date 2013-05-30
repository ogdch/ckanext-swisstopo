from boto.s3.connection import S3Connection

S3_KEY = p.toolkit.asbool(config.get('ckanext.swisstopo.s3_key', ''))
S3_TOKEN = p.toolkit.asbool(config.get('ckanext.swisstopo.s3_token', ''))
S3_BUCKET = p.toolkit.asbool(config.get('ckanext.swisstopo.s3_bucket', ''))

conn = S3Connection(S3_KEY,S3_TOKEN)
bucket = conn.get_bucket(S3_BUCKET)
for key in bucket.list():
    print key.name.encode('utf-8')

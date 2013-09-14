ckanext-swisstopo
=================

Harvester for the Federal Office of Topography swisstopo

## Installation

Use `pip` to install this plugin. This example installs it in `/home/www-data`

```bash
source /home/www-data/pyenv/bin/activate
pip install -e git+https://github.com/ogdch/ckanext-swisstopo.git#egg=ckanext-swisstopo --src /home/www-data
cd /home/www-data/ckanext-swisstopo
pip install -r pip-requirements.txt
python setup.py develop
```

Make sure to add `swisstopo` and `swisstopo_harvest` to `ckan.plugins` in your config file.

## Run harvester

```bash
source /home/www-data/pyenv/bin/activate
paster --plugin=ckanext-swisstopo swisstopo_harvest gather_consumer -c development.ini &
paster --plugin=ckanext-swisstopo swisstopo_harvest fetch_consumer -c development.ini &
paster --plugin=ckanext-swisstopo swisstopo_harvest run -c development.ini
```

CSW query:

```bash
source /home/www-data/pyenv/bin/activate
# Show output from CSW, 'query' is typically the name of a dataset like 'swissboundaries3D'
paster --plugin=ckanext-swisstopo swisstopo csw <query> -c development.ini
```

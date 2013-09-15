import ckan
import ckan.plugins as p
from pylons import config

class SwisstopoHarvest(p.SingletonPlugin):
    """
    Plugin containg the harvester for swisstopo
    """

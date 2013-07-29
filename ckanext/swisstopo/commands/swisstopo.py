import logging
import ckan.lib.cli
import sys

from ckanext.swisstopo.s3 import s3
from ckanext.swisstopo.ckan_csw import ckan_csw


class SwisstopoCommand(ckan.lib.cli.CkanCommand):
    '''Command to handle swisstopo data

    Usage:

        # Show this help
        paster --plugin=ckanext-swisstopo swisstopo help -c <path to config file>

        # Import datasets
        paster --plugin=ckanext-swisstopo swisstopo import -c <path to config file>

        # List all files in the S3 bucket
        paster --plugin=ckanext-swisstopo swisstopo list -c <path to config file>

        # Show output from CSW, 'query' is typically the name of a dataset like 'swissboundaries3D'
        paster --plugin=ckanext-swisstopo swisstopo csw <query> -c <path to config file>

    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def command(self):
        # load pylons config
        self._load_config()
        options = {
                'import': self.importCmd,
                'list': self.listCmd,
                'csw': self.cswCmd,
                'help': self.helpCmd,
        }

        try:
            cmd = self.args[0]
            options[cmd](*self.args[1:])
        except KeyError:
            self.helpCmd()
            sys.exit(1)

    def helpCmd(self):
        print self.__doc__

    def listCmd(self):
        s3_helper = s3.S3();
        s3_helper.list()

    def cswCmd(self, query=None):
        if (query is None):
            print "Argument 'query' must be set"
            self.helpCmd()
            sys.exit(1)
        csw = ckan_csw.SwisstopoCkanMetadata();
        print csw.get_ckan_metadata(query)


    def importCmd(self):
        raise NotImplementedError

    def showCmd(self):
        raise NotImplementedError

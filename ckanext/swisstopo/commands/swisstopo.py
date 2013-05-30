import logging
import ckan.lib.cli

class SwisstopoCommand(ckan.lib.cli.CkanCommand):
    '''Command to import swisstopo data

    Usage::

        From the ckanext-swisstopo directory, run:

            paster swisstopo import -c <path to config file>

    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def command(self):
        options = {
                'import': self.importCmd,
                'show': self.showCmd,
                'help': self.helpCmd,
        }

        try:
            cmd = self.args[0]
            options[cmd]()
        except KeyError:
            helpCmd()

    def helpCmd(self):
        print self.__doc__

    def importCmd(self):
        raise NotImplementedError

    def showCmd(self):
        raise NotImplementedError


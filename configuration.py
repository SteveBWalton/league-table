# -*- coding: utf-8 -*-

'''
Module to support the configuration options for the table program.
'''

# System libraries.
import os
import os.path
import xml.dom.minidom

# SportResults libraries.
import walton.configuration
import walton.xml



class Configuration(walton.configuration.IConfiguration):
    '''
    Class to represent the configuration options for the Sport Results database program.
    Originally this used xml.dom.minidom directly but now using my own :py:class:`~walton.xml.XmlDocument` class.

    :ivar XmlDocument xmlDocument: The :py:class:`~walton.xml.XmlDocument` object that persits the configuration options.
    :ivar string databaseFilename: The filename of the sports results database.
    '''


    def __init__(self):
        ''' Class constructor for the :py:class:`Configuration` class. '''
        # Initialise base classes.
        walton.configuration.IConfiguration.__init__(self, 'table')

        # Read the options.
        self.readOptions()

        # If a new document then write the document.
        if self.xmlDocument.dirty:
            self.saveConfigurationFile()



    def readOptions(self):
        ''' Read the options from the configuration file. '''
        # Read the options in the base class.
        super().readOptions()

        # Read the database filename.
        xmlDatabase = self.xmlDocument.root.getNode('database')

        # The filename of the table database.
        self.databaseFilename = xmlDatabase.getAttributeValue('filename', os.getenv("HOME") + '/Documents/Personal/Sports/table.sqlite', True)

        # xmlCurrentSport = self.xmlDocument.root.getNode('current_sport')
        # The ID of the current active sport.
        # self.currentSportIndex = int(xmlCurrentSport.getAttributeValue('index', '1', True))



    def saveConfigurationFile(self):
        ''' Write the configuration file to disk. '''
        self.xmlDocument.save()

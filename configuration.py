# -*- coding: utf-8 -*-

'''
Module to support the configuration options for the table program.
'''

# System libraries.
import os
import os.path
import xml.dom.minidom

# SportResults libraries.
import walton.xml



class Configuration(walton.application.IConfiguration):
    '''
    Class to represent the configuration options for the Sport Results database program.
    Originally this used xml.dom.minidom directly but now using my own :py:class:`~walton.xml.XmlDocument` class.

    :ivar XmlDocument xmlDocument: The :py:class:`~walton.xml.XmlDocument` object that persits the configuration options.
    :ivar string databaseFilename: The filename of the sports results database.
    :ivar string flagsDatabaseFilename: The filename of the flags database.
    :ivar string flagsDirectory: The directory that contains the flags images.
    :ivar int currentSportIndex: The ID of the current active sport.
    '''


    def __init__(self):
        ''' Class constructor for the :py:class:`Configuration` class. '''
        # Initialise base classes.
        walton.application.IConfiguration.__init__(self, 'table')

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

        # The filename of the sports results database.
        self.databaseFilename = xmlDatabase.getAttributeValue('filename', os.getenv("HOME") + '/Documents/Personal/Sports/table.sqlite', True)

        xmlCountries = self.xmlDocument.root.getNode('flags')
        # The filename of the flags database.
        self.flagsDatabaseFilename = xmlCountries.getAttributeValue('filename', os.getenv("HOME") + '/Documents/Personal/Sports/flags.sqlite', True)
        # The directory that contains the flags images.
        self.flagsDirectory = xmlCountries.getAttributeValue('directory', os.getenv("HOME") + '/Projects/Graphics/Flags/', True)

        xmlCurrentSport = self.xmlDocument.root.getNode('current_sport')
        # The ID of the current active sport.
        self.currentSportIndex = int(xmlCurrentSport.getAttributeValue('index', '1', True))



    def saveConfigurationFile(self):
        ''' Write the configuration file to disk. '''
        self.xmlDocument.save()



    def setCurrentSport(self, sportIndex):
        '''
        Set the current sport.

        :param int SportID: Specifies the ID of the new sport.
        '''
        # Get the Current Sport node.
        xmlCurrentSport = self.xmlDocument.root.getNode('current_sport')
        xmlCurrentSport.setAttributeValue('index', sportIndex)
        self.currentSportIndex = sportIndex



    def setFlagsDirectory(self, flagsDirectory):
        '''
        Set the value for the flags directory.

        :param string flagsDirectory: Specifies the new directory for the flag images.
        '''
        # Get the flags node
        xmlCountries = self.xmlDocument.root.getNode('flags')

        # Make sure the final character is a '/'
        if flagsDirectory[-1] != '/':
            flagsDirectory += '/'

        # Write the value into the xml and object
        xmlCountries.setAttributeValue('directory', flagsDirectory)
        self.flagsDirectory = flagsDirectory

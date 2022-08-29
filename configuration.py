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



class Configuration:
    '''
    Class to represent the configuration options for the Sport Results database program.
    Originally this used xml.dom.minidom directly but now using my own :py:class:`~walton.xml.XmlDocument` class.

    :ivar XmlDocument xmlDocument: The :py:class:`~walton.xml.XmlDocument` object that persits the configuration options.
    :ivar string databaseFilename: The filename of the sports results database.
    :ivar string flagsDatabaseFilename: The filename of the flags database.
    :ivar string flagsDirectory: The directory that contains the flags images.
    :ivar int currentSportIndex: The ID of the current active sport.
    '''
    # The directory that contains the configuration settings for the SportsResults database.
    DIRECTORY = os.getenv("HOME") + '/.walton/table'

    # The full filename of the SportsResults database configuration file.
    FILENAME = DIRECTORY + '/table.xml'



    def __init__(self):
        ''' Class constructor for the :py:class:`Configuration` class. '''
        # Create the configuration directory if not already exist.
        if not(os.path.exists(Configuration.DIRECTORY)):
            print("Create {}".format(Configuration.DIRECTORY))
            os.mkdir(Configuration.DIRECTORY)

        # The XmlDocument object that persits the configuration options.
        self.xmlDocument = walton.xml.XmlDocument(self.FILENAME, 'table')

        # Read the options.
        self.readOptions()

        # If a new document then write the document.
        if self.xmlDocument.dirty:
            self.saveConfigurationFile()



    def readOptions(self):
        ''' Read the options from the configuration file. '''
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

        xmlMainWindow = self.xmlDocument.root.getNode('main_window')
        self.textSize = xmlMainWindow.getAttributeValue('text_size', 10, True)
        self.colourScheme = xmlMainWindow.getAttributeValue('colour_scheme', 'grey', True)
        self.fontName = xmlMainWindow.getAttributeValue('font', 'Liberation Sans', True)
        self.verticalSpace = xmlMainWindow.getAttributeValue('vertical_space', 1, True)
        self.horizontalSpace = xmlMainWindow.getAttributeValue('horizontal_space', 2, True)
        self.isDivider = xmlMainWindow.getAttributeValue('divider', False, True)



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



    def setTextSize(self, newSize):
        '''
        Set the current text size.

        :param int newSize: Specifies the new text size.
        '''
        # Get the main window node.
        xmlMainWindow = self.xmlDocument.root.getNode('main_window')
        xmlMainWindow.setAttributeValue('text_size', newSize)
        self.textSize = newSize



    def setColourScheme(self, newScheme):
        ''' Set the current colour scheme. '''
        xmlMainWindow = self.xmlDocument.root.getNode('main_window')
        xmlMainWindow.setAttributeValue('colour_scheme', newScheme)
        self.colourScheme = newScheme



    def setFont(self, newFont):
        ''' Set the current font. '''
        # Replace + with space.
        newFont = newFont.replace('+', ' ')

        # Set the font name.
        xmlMainWindow = self.xmlDocument.root.getNode('main_window')
        xmlMainWindow.setAttributeValue('font', newFont)
        self.fontName = newFont



    def setSpace(self, newVertical, newHorizontal):
        ''' Set the vertical and horizontal space. '''
        xmlMainWindow = self.xmlDocument.root.getNode('main_window')
        xmlMainWindow.setAttributeValue('vertical_space', newVertical)
        xmlMainWindow.setAttributeValue('horizontal_space', newHorizontal)
        self.verticalSpace = newVertical
        self.horizontalSpace = newHorizontal



    def setDivider(self, newDivider):
        ''' Set the divider status. '''
        # print('setDivider({})'.format(newDivider))
        xmlMainWindow = self.xmlDocument.root.getNode('main_window')
        self.isDivider = newDivider
        xmlMainWindow.setAttributeValue('divider', self.isDivider)



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

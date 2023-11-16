#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Module to represent the core application for the table program.
This module implements the :py:class:`Application` class.
This is functionality which all rendering engines will need.
'''

# System libraries.
import sys
import os
import platform
import datetime
import shutil

# The program libraries.
import walton.application
from configuration import Configuration
from database import Database
from render import Render
# import walton.yearrange



class Application(walton.application.IApplication):
    '''
    :ivar Render render: The :py:class:`~render.Render` object for the Formula One results database.
    :ivar Database database: The :py:class:`~database.Database` object for the Formula One results database.
    :ivar Configuration configuration: The :py:class:`~configuration.Configuration` object for the Sports Results database.
    :ivar string request: The url of the current page request.
    :ivar string parameters: The parameters of the current page request.
    :ivar bool showAge: True to add the show age request to each link.
    :ivar YearRange yearRange: The active year range object for the application.

    Class to represent the core Sports results database application.
    This was originally part of the GTK main window.
    This class is inherited from the :py:class:`walton.application.IApplication` class.
    '''



    def __init__(self, args):
        '''
        :param object args: The program arguments.

        Class constructor for the :py:class:`Application` class.
        '''
        # Initialise base classes.
        walton.application.IApplication.__init__(self)

        # Initialise member variables.
        self.request = 'home'
        self.parameters = ''
        self.postRenderPage = None
        self.decodeLink = None
        self.actions = {}

        self.showAge = False

        # The Configuration object for the league table program.
        # This is the application settings and options.
        self.configuration = Configuration()

        # The Database object for the league table program.
        self.database = Database(self.configuration.databaseFilename, self)

        # The Render object for the league table program.
        # This is the object that renders the application results to html pages for display.
        self.render = Render(self)

        # Generate the style sheets.
        self.setStyleSheets()

        # Show the initial page.
        self.current_uri = ''



    def setStyleSheets(self):
        ''' Set the style sheets on the render html object.'''
        folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Styles')
        sizeStyleSheet = self.generateSizeStyleSheet(os.path.join(folder, 'textsize.txt'), self.configuration.textSize, folder)
        fontStyleSheet = self.generateFontStyleSheet(os.path.join(folder, 'font.txt'), self.configuration.fontName, folder)

        # Generate a space stylesheet.
        spaceStyleSheet = os.path.join(folder, 'table-space-{}{}.css'.format(self.configuration.verticalSpace, self.configuration.horizontalSpace))
        fileOutput = open(spaceStyleSheet, 'w')
        fileOutput.write('td {{ padding: {}px {}px {}px {}px; }}\n'.format(self.configuration.verticalSpace, self.configuration.horizontalSpace, self.configuration.verticalSpace, self.configuration.horizontalSpace))
        fileOutput.close()

        # Remove the existing stylesheets.
        self.render.html.stylesheets = []

        # Local files.
        self.render.html.stylesheets.append('file:' + os.path.join(folder, 'table.css'))
        if self.configuration.colourScheme != 'none':
            self.render.html.stylesheets.append('file:' + os.path.join(folder, 'table-{}.css'.format(self.configuration.colourScheme)))
        self.render.html.stylesheets.append('file:' + sizeStyleSheet)
        self.render.html.stylesheets.append('file:' + fontStyleSheet)
        self.render.html.stylesheets.append('file:' + spaceStyleSheet)

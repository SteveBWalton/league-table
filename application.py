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
        # The active YearRange object for formula one database.
        # self.yearRange = walton.year_range.YearRange()

        # The active YearRange object for formula one database.
        # self.yearRange = walton.year_range.YearRange()

        # The Configuration object for the table program.
        # This is the application settings and options.
        self.configuration = Configuration()

        # The Database object for the table program.
        self.database = Database(self.configuration.databaseFilename, self)

        # The Render object for the application.
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



    #def openCurrentPage(self):
    #    '''
    #    Load the current page as specified by :py:attr:`self.request` and :py:attr:`self.parameters` attributes.
    #    Add the options from the main window toolbar to the parameters and fetch the page from the render object.
    #    This will call :py:func:`displayCurrentPage` if the content changes.
    #    Display chain is :py:func:`followLocalLink` -> :py:func:`openCurrentPage` -> :py:func:`displayCurrentPage`.
    #    '''
    #    if self.database.debug:
    #        print('openCurrentPage({}, {})'.format(self.request, self.parameters))
    #
    #    parameters = self.parameters
    #
    #    # Check for the age flag.
    #    if self.showAge:
    #        parameters += '&age=show'
    #
    #    # Check for a year range.
    #    if not self.yearRange.allYears:
    #        if 'firstyear' in parameters:
    #            # Don't add a year again.  Maybe update the object?
    #            self.yearRange.allYears = True
    #        else:
    #            parameters += '&firstyear={}&lastyear={}'.format(self.yearRange.firstYear, self.yearRange.lastYear)
    #
    #    if self.database.debug:
    #        print("    Request '{}', Parameters '{}'".format(self.request, parameters))
    #
    #    # Build a dictionary from the parameters.
    #    dictionary = self.decodeParameters(parameters)
    #
    #    # This is like a switch statement (that Python does not support)
    #    isNewContent = True
    #    if self.request in self.render.actions:
    #        isNewContent = True
    #        self.render.actions[self.request](dictionary)
    #    elif self.request in self.actions:
    #        isNewContent = self.actions[self.request](dictionary)
    #    #else:
    #    #    # Ask the render engine if it knows what to do.
    #    #    isNewContent = False
    #    #    if self.decodeLink != None:
    #    #        isNewContent = self.decodeLink(self.request, parameters)
    #
    #    # Display the content created by the database.
    #    if self.postRenderPage != None:
    #        if isNewContent:
    #            # self.DisplayCurrentPage()
    #            self.postRenderPage()
    #
    #    # Return false so that idle_add does not call here again.
    #    return False




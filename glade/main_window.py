#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Module to display the main GTK window for the table program.
This module implements the :py:class:`MainWindow` class.
This is was originally in GTK 2 but now in GTK 3.
This was originally part of the :py:mod:`sportsresults` module.
This originally had the functionalilty of the App object.
'''


# Import system libraries.
import sys
import os
# import argparse

# Import Gtk3+ libraries.
try:
    import gi
    gi.require_version('Gtk', '3.0')
    # I don't think GObject is required anymore, GLib replaced it.
    from gi.repository import Gtk, Gdk, GLib # GObject
except:
    print("GTK Not Available. ({})".format(__file__))
#_useWebKit2 = False
#try:
#    # This required the 'webkitgtk3' package in Fedora 25.
#    gi.require_version('WebKit', '3.0')
#    from gi.repository import WebKit
#except:
#    print("WebKit Not Available. ({})".format(__file__))
#    _useWebKit2 = True
# This was required in Fedora 27.
#if _useWebKit2:
try:
    # This required the 'webkitgtk4' package in Fedora 27.
    gi.require_version('WebKit2', '4.0')
    from gi.repository import WebKit2
    # print("Using WebKit2")
except:
    print("WebKit2 Not Available. ({})".format(__file__))


# Import more system libraries.
import os
import platform
import subprocess
import shutil
import datetime

# import urllib

# Application libraries.
#import walton.year_range
import walton.glade.webkit
import walton.glade.fullscreen
#import walton.glade.select_years
#import walton.glade.select_country
#import walton.glade.edit_country
#import glade.preferences
#import glade.edit_team
import glade.edit_matches
#import glade.edit_sport
#import glade.edit_tournament
#import glade.edit_location
#import glade.edit_season



class MainWindow(walton.glade.webkit.IWebKit2, walton.glade.fullscreen.IFullscreen):
    '''
    Class to represent the main window for the 'table' program.

    :ivar int noEvents: Set to greater than zero to ingore signals.  Restore to zero to respond to signals.
    :ivar string request: The last page request.
    :ivar string parameters: The parameters on the last page request.
    :ivar array history: The request history.  Used for the 'Back' function.
    :ivar Gtk.Builder builder: The GTK+ builder for the main window.
    :ivar Gtk.Window window: The GTK+ main window for the 'Sports Results' database.
    :ivar WebKit.WebView webview: The webkit (Chrome,Safari) embedded html viewer widget on the main window.
    :ivar Configuration configuration: The configuration options for the sports results database.
    :ivar CYearRange yearRange: The year range to apply to the page requests.
    :ivar int selectedTournamentIndex: The ID of the selected tournament to apply to page requests. Use 'None' for no selected tournament.
    :ivar int tournamentSportIndex: The ID of the sport of the selected tournament.
    :ivar int selectedCountryIndex: The ID of the selected country.  Use 'None' for no selected country.
    :ivar int selectedLevel: The currently selected level.  Use 'None' for the default level.  The first user option is level 0.
    :ivar Database database: The database for the 'Sports Results' database.
    :ivar Render render: The render object for the 'Sports Results' database.
    '''



    def __init__(self, application, args):
        '''
        Class contructor for the :py:class:`MainWindow` class.

        :param Application application: Specifies the main program.
        :param object args: Specifies the program arguments.
        '''
        # Initialise base classes.
        walton.glade.webkit.IWebKit2.__init__(self)
        walton.glade.fullscreen.IFullscreen.__init__(self)

        # Report the Gtk version.
        print('GTK Version {}·{}·{} (expecting GTK3).'.format(Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version()))

        # Set to greater than zero to ingore signals.  Restore to zero to respond to signals.
        self.noEvents = 0

        # The last page request.
        self.request = 'home'

        # The parameters on the last page request.
        self.parameters = ''

        # The request history.  Used for the 'Back' function.
        self.history = ['home']

        # The GTK+ builder for the main window.
        self.builder = Gtk.Builder()
        self.builder.add_from_file('{}/main_window.glade'.format(os.path.dirname(os.path.realpath(__file__))))

        # The main window for the 'Sports Results' database.
        self.window = self.builder.get_object('windowMain')
        if self.window:
            self.window.connect('destroy', Gtk.main_quit)

        # The webkit (Chrome,Safari) embedded html viewer widget on the main window.
        #if _useWebKit2:
        self.webview = WebKit2.WebView()
        self.webview.connect('load_changed', self._webkitLoadChanged)
        #else:
        #    self.webview = WebKit.WebView()
        #    self.webview.connect('navigation-policy-decision-requested', self._NavigationRequest)
        oFrame = self.builder.get_object("scrolledwindowWebView")
        oFrame.add(self.webview)

        signals = {
            'on_menuitemFileHome_activate'          : self._fileHome,
            'on_menuitemFileIndex_activate'         : self._fileIndex,
            'on_menuitemFileBack_activate'          : self._fileBack,
            'on_menuitemFilePrintPreview_activate'  : self._filePrint,
            'on_menuitemFileQuit_activate'          : self._fileQuit,

            'on_menuitemEditEdit_activate'          : self._editEdit,
            'on_menuitemEditAddSeason_activate'     : self._editAddSeason,
            'on_menuitemEditPreferences_activate'   : self._editPreferences,
            'on_menuCopy_activate'                  : self._editCopy,

            'on_menuitemViewNext_activate'          : self._ViewNext,
            'on_menuitemViewPrevious_activate'      : self._ViewPrevious,
            'on_menuitemViewAge_toggled'            : self._ViewAge,
            'on_menuitemViewDebug_toggled'          : self._viewDebug,

            'on_menuitemHelpAbout_activate'         : self._helpAbout,

            'on_menuFileNew_activate'               : self._fileNew,
            'on_tbbFileNew_clicked'                 : self._fileNew,
            'on_menuFileOpen_activate'              : self._fileOpen,
            'on_tbbFileOpen_clicked'                : self._fileOpen,

            'on_toolbuttonHome_clicked'             : self._fileHome,
            'on_toolbuttonIndex_clicked'            : self._fileIndex,
            'on_toolbuttonBack_clicked'             : self._fileBack,
            'on_toolbuttonEdit_clicked'             : self._editEdit,
            'on_toolbuttonNext_clicked'             : self._ViewNext,
            'on_toolbuttonPrevious_clicked'         : self._ViewPrevious,
            'on_toolbuttonAge_toggled'              : self._ViewAge,

            'on_menuitemLevel0_activate'            : self._LevelMenu,
            'on_menuitemLevel1_activate'            : self._LevelMenu,
            'on_menuitemLevel2_activate'            : self._LevelMenu,
            'on_menuitemLevel3_activate'            : self._LevelMenu,
            'on_menuitemLevel4_activate'            : self._LevelMenu,
            'on_menuitemLevel5_activate'            : self._LevelMenu,
            'on_menuitemLevel6_activate'            : self._LevelMenu,

            'on_menuTournamentAll_activate' : self._TournamentMenu,
            'on_menuTournament1_activate' : self._TournamentMenu,
            'on_menuTournament2_activate' : self._TournamentMenu,
            'on_menuTournament3_activate' : self._TournamentMenu,
            'on_menuTournament4_activate' : self._TournamentMenu,
            'on_tbbYears_clicked' : self._YearsClicked,
            'on_tbbCountry_clicked'                 : self._countryClicked,
            'on_menuViewHtml_activate' : self._ViewHtml,

            'on_windowMain_key_press_event'         : self._keyPressEvent,
            'on_windowMain_window_state_event'      : self._windowStateEvent,
        }
        self.builder.connect_signals(signals)

        # Glade does not set the menu on the toolbar menu objects any more
        # You have to create a menu object in the xml file and link to it here.
        menuLevels = self.builder.get_object('menuLevels')
        menutoolbuttonLevel = self.builder.get_object('menutoolbuttonLevel')
        menutoolbuttonLevel.set_menu(menuLevels)
        menuTournaments = self.builder.get_object('menuTournaments')
        tbmenuTournament = self.builder.get_object('tbmenuTournament')
        tbmenuTournament.set_menu(menuTournaments)

        # The application object for the sports results database.
        self.application = application

        # The configuration options for the sports results database.
        self.configuration = self.application.configuration

        # The year range to apply to the page requests.
        # self.yearRange = walton.year_range.YearRange()

        # The ID of the selected tournament to apply to page requests. Use 'None' for no selected tournament.
        self.selectedTournamentIndex = None

        # The ID of the sport of the selected tournament.
        # This is only to check that the selected tournament is valid (same sport).
        self.tournamentSportIndex = 0

        # The ID of the selected country.  Use 'None' for no selected country.
        self.selectedCountryIndex = None

        # The currently selected level.  Use 'None' for the default level.  The first user option is level 0.
        self.selectedLevel = None

        # Open the database for the 'Sports Results' database.
        self.database = self.application.database

        # The render object for the 'Sports Results' database.
        # self.render = modRender.Render(self.database)
        # self.render.html.stylesheets.append('file://' + os.path.dirname(os.path.realpath(__file__)) + '/' +'sportsresults.css')
        # self.render.html.stylesheets.append('file://' + os.path.dirname(os.path.realpath(__file__)) + '/' +'textsize_{}.css'.format(self.configuration.textSize))
        self.render = self.application.render

        self.render.showHome({})
        self.displayCurrentPage()
        #self.window.set_title(self.database.currentSport.name + ' - Sports Results DB')
        #self.render.html.title = self.database.currentSport.name + ' - Sports Results DB'

        # Some silly stuff
        # print "gtk.RESPONSE_OK = ",int(gtk.RESPONSE_OK)
        # print "gtk.RESPONSE_CANCEL = ",int(gtk.RESPONSE_CANCEL)

        # Define the actions this module can handle and the function to handle the action.
        self.actions = {
            'edit_date'         : self.editDate,
            'edit_team'         : self.editTeam,
            'edit_matches'      : self.editMatches,
        }

        # Move the focus off the toolbar.
        self.webview.grab_focus()



    def run(self):
        ''' Run the GTK main loop. '''
        self.window.show_all()
        Gtk.main()



    def _fileHome(self, widget):
        ''' Signal handler for the 'File' → 'Home' menu item. '''
        self.followLocalLink('home', True)



    def _fileIndex(self, widget):
        ''' Signal handler for the 'File' → 'Index' meun item. '''
        self.followLocalLink('index', True)


    def _fileBack(self, widget):
        ''' Signal handler for the 'File' → 'Back' menu item. '''
        if self.database.debug:
            print('FileBack')
        if len(self.history) > 0:
            link = self.history.pop()
        if len(self.history) > 0:
            link = self.history.pop()
            self.followLocalLink(link, True)


    def _filePrint(self, widget):
        ''' Signal handler for the 'File' → 'Print Preview' menu item. '''
        # Save the html to a file.
        filename = '{}/print.html'.format(self.configuration.DIRECTORY)
        writeFile = open(filename, 'w')
        writeFile.write(self.render.html.toHtml())
        writeFile.close()
        if self.database.debug:
            print('Created \'{}\'.'.format(filename))

        # Launch the html with the default viewer.
        subprocess.Popen(['xdg-open', filename])



    def _fileQuit(self, widget):
        '''
        Signal handler for the 'File' → 'Quit' menu item.
        Close the main window and hence exit the program.
        '''
        # Close the main window and hence end the program.
        self.window.destroy()



    def _editEdit(self, widget):
        ''' Signal handler for the 'Edit' → 'Edit' menu item and 'Edit' toolbar button. '''
        self.followLocalLink(self.render.editTarget, False)



    def _editAddSeason(self, widget):
        ''' Signal handler for the 'Edit' → 'Add Season' menu item. '''
        dialog = glade.edit_season.EditSeason(self.window)
        if dialog.editSeason(self.database, None):
            # Get the last easonIndex
            pass
            # Show the season identified.
            # self.render.showSeason({'season': seasonIndex})
        return True



    def _editPreferences(self, widget):
        ''' Signal handler for the 'Edit' → 'Preferences' menu item. '''
        dialog = glade.preferences.Preferences(self.window, self.configuration)
        if dialog.editPreferences():
            self.database.flagsDirectory = self.configuration.flagsDirectory



    def _editCopy(self, widget):
        ''' Signal handler for the 'Edit' → 'Copy' menu item. '''
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.clipboard.set_text(self.render.clipboardText, -1)



    def _ViewNext(self, widget):
        ''' Signal handler for the 'View' → 'Next' menu item. '''
        self.followLocalLink(self.render.nextPage, True)



    def _ViewPrevious(self, widget):
        ''' Signal handler for the 'View' → 'Previous' menu item. '''
        self.followLocalLink(self.render.previousPage, True)



    def _ViewAge(self, widget):
        ''' Signal handler for the 'View' → 'Age' menu item. '''
        # print "AgeToggled by "+type(widget).__name__

        if self.noEvents > 0:
            # print "No Events ({}).".format(self.noEvents)
            return

        # No more signals / events.
        self.noEvents += 1

        if type(widget).__name__ == 'ToggleToolButton':
            bActive = widget.get_active()
            # Update the menu.
            menuitemViewAge = self.builder.get_object('menuitemViewAge')
            if menuitemViewAge.get_active()!=bActive:
                menuitemViewAge.set_active(bActive)
        elif type(widget).__name__ == 'CheckMenuItem':
            bActive = widget.get_active()
            # Update the tool bar button.
            toolbuttonAge = self.builder.get_object('toolbuttonAge')
            if toolbuttonAge.get_active()!=bActive:
                toolbuttonAge.set_active(bActive)

        # Update the page.
        self.openCurrentPage()

        # Events / Signals back on
        self.noEvents -= 1



    def _viewFullscreen(self, widget):
        ''' Signal handler for the 'View' → 'Fullscreen' menu item. '''
        toolbarMain = self.builder.get_object('toolbarMain')
        menubarMain = self.builder.get_object('menubarMain')
        if self.isFullscreen:
            self.window.unfullscreen()
            toolbarMain.set_visible(True)
            menubarMain.set_visible(True)
        else:
            self.window.fullscreen()
            toolbarMain.set_visible(False)
            menubarMain.set_visible(False)



    def _ViewHtml(self, widget):
        ''' Signal handler for the 'View' → 'Html' menu item. '''
        print(self.render.html.toHtml())



    def _viewDebug(self, widget):
        ''' Signal handler for the 'View' → 'Debug Info' menu item. '''
        self.database.debug = widget.get_active()
        if self.database.debug:
            print('DEBUG is active.')
        else:
            print('DEBUG is off.')

        if self.database.debug:
            # Add the debug stylesheet.
            self.render.html.stylesheets.append('file://' + os.path.dirname(os.path.realpath(__file__)) + os.sep + 'debug.css')
            for styleSheet in self.render.html.stylesheets:
                print(styleSheet)
        else:
            # Remove the debug stylesheet
            if len(self.render.html.stylesheets) == 3:
                del self.render.html.stylesheets[2]
        # Update the page.
        self.displayCurrentPage()



    def _helpAbout(self, widget):
        ''' Signal handler for the 'Help' → 'About' menu item. '''
        self.followLocalLink('about', False)



    def _countryClicked(self, widget):
        ''' Signal handler for the Country selector toolbar button. '''
        dialog = walton.glade.select_country.SelectCountry(self.window)
        country = dialog.selectCountry(self.database,self.selectedCountryIndex)
        if country == None:
            widget.set_label('All Countries')
            self.selectedCountryIndex = None
        else:
            widget.set_label(country.name)
            self.selectedCountryIndex = country.index
        # Update the page
        self.openCurrentPage()


    def _YearsClicked(self, widget):
        ''' Signal handler for the years selector toolbar button. '''
        # Fetch the year range for this sport.
        self.database.currentSport.getYearRange()

        # Display a dialog and allow the user to select a year range.
        self.yearRange.minFirstYear = self.database.currentSport.firstYear;
        self.yearRange.maxLastYear = self.database.currentSport.lastYear;
        dialog = walton.glade.select_years.SelectYears(self.window, self.yearRange)
        if dialog.selectYears():
            widget.set_label(self.yearRange.toString())
            # Update the page.
            self.openCurrentPage()



    def _LevelMenu(self, widget):
        ''' Signal handler for the levels menu points. '''
        menutoolbuttonLevel = self.builder.get_object('menutoolbuttonLevel')
        sLevel = widget.get_label()
        menutoolbuttonLevel.set_label(sLevel)
        self.selectedLevel = None
        for nIndex, sPossibleLevel in enumerate(self.render.levels):
            if sPossibleLevel == sLevel:
                self.selectedLevel = nIndex
        # Update the page.
        self.openCurrentPage()



    def _TournamentMenu(self, widget):
        ''' Signal handler for the tournament menu points. '''
        tbmenuTournament = self.builder.get_object('tbmenuTournament')
        sTournamentLabel = widget.get_label();
        tbmenuTournament.set_label(sTournamentLabel)
        self.selectedTournamentIndex = None
        for nTournamentID in self.database.currentSport.tournamentsByStatus:
            tournament = self.database.getTournament(nTournamentID)
            if tournament.name == sTournamentLabel:
                self.selectedTournamentIndex=tournament.index
        # Update the page.
        self.openCurrentPage()



    def _fileNew(self, widget):
        ''' Signal handler for the 'File' → 'New' menu point. '''
        print('FileNew')



    def _fileOpen(self, widget):
        ''' Signal handler for the 'File' → 'Open' menu point. '''
        dialog = gtk.FileChooserDialog("Select File", None, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        fileFilter = gtk.FileFilter()
        fileFilter.set_name("All files")
        fileFilter.add_pattern("*")
        dialog.add_filter(fileFilter)

        fileFilter = gtk.FileFilter()
        fileFilter.set_name("Python files")
        fileFilter.add_pattern("*.py")
        dialog.add_filter(fileFilter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            print('FileOpen ', dialog.get_filename())

        dialog.destroy()



#    def _NavigationRequest(self, view, frame, net_req, nav_act, pol_dec):
#        ''' Signal handler for a link request / click on the webview control. '''
#        # Get the Uri of the requested page.
#        uri = net_req.get_uri()
#        # print 'Navigation Request url: ',uri
#
#        if uri.startswith('app:'):
#            # Don't try and follow this request.
#            pol_dec.ignore()
#
#            # Follow the local link.
#            self.followLocalLink(uri[4:],True)
#
#        if uri.startswith('folder:'):
#            # Open the specified folder.
#            pol_dec.ignore()
#            # This was in urllib2 in python '2.7'.
#            # subprocess.Popen(['nautilus',urllib.parse.unquote(uri[8:])])
#            # Open the folder with the default handler, rather than force nautilus.
#            subprocess.Popen(['xdg-open', urllib.parse.unquote(uri[7:])])
#
#        if uri.startswith('http:') or uri.startswith('https:'):
#            # Open the specified link with the default handler, rather than force firefox.
#            pol_dec.ignore()
#            subprocess.Popen(['xdg-open', uri])
#
#        # Not sure why you return false.
#        return False



    def followLocalLink(self, link, addToHistory):
        '''
        Enact the specified local link.
        Decode the link, update history, update cursor and put :py:func:`openCurrentPage` in the idle queue.
        This only deals with links of the form 'app:{link}', ie local links.
        Display chain is :py:func:`followLocalLink` → :py:func:`openCurrentPage` → :py:func:`displayCurrentPage`.

        :param string link: Specifies the link to follow.  This is expected to be the link after the 'app:' prefix.
        :param boolean addToHistory: Specifies true to add the specified link to the history.
        '''
        if self.application.debug:
            print('followLocalLink("{}")'.format(link))

        # Show the wait cursor.
        waitCursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        self.window.get_window().set_cursor(waitCursor)
        self.webview.get_window().set_cursor(waitCursor)
        isDecode = True

        # Check for an exit request.
        if link == 'quit':
            # Close the main window and hence exit the Gtk loop.
            self.window.destroy()

        # Check for a back request.
        if link == 'back':
            if len(self.history) > 0:
                link = self.history.pop()
            if len(self.history) > 0:
                link = self.history.pop()
            else:
                link = 'home'

        if link == 'refresh':
            addToHistory = False
            isDecode = False

        # Check for a yearRange request.
        if link == 'year_range':
            # Display the previous page again but now with the year range.
            if len(self.history) > 0:
                link = self.history.pop()

            self.yearRange.minFirstYear = self.database.currentSport.firstYear
            self.yearRange.maxLastYear = self.database.currentSport.lastYear
            dialog = walton.glade.select_years.SelectYears(self.window, self.yearRange)
            if dialog.selectYears():
                # Remove any existing year range.
                # print(link)
                firstYear = link.find('firstyear')
                if firstYear > 0:
                    # This misses the leading & but better than getting the one ?
                    link = '{}{}'.format(link[0:firstYear], link[firstYear+14:])
                # print(link)
                lastYear = link.find('lastyear')
                if lastYear > 0:
                    # This misses the leading & but better than getting the one ?
                    link = '{}{}'.format(link[0:lastYear], link[lastYear+14:])
                # print(link)

        # Check for an age request.
        if link == 'toogle_age':
            # Display the previous page again but now with the age request.
            if len(self.history) > 0:
                link = self.history.pop()

            # Change the age toolbar status.
            toolbuttonAge = self.builder.get_object('toolbuttonAge')
            toolbuttonAge.set_active(not(toolbuttonAge.get_active()))
            menuitemViewAge = self.builder.get_object('menuitemViewAge')
            menuitemViewAge.set_active(toolbuttonAge.get_active())

        # Check for a country filter request.
        if link == 'select_country':
            # Display the previous page again but now with the year range.
            if len(self.history) > 0:
                link = self.history.pop()

            # Select a country.
            dialog = walton.glade.select_country.SelectCountry(self.window)
            country = dialog.selectCountry(self.database, self.selectedCountryIndex)
            if country == None:
                # widget.set_label('All Countries')
                self.selectedCountryIndex = None
            else:
                # widget.set_label(country.name)
                self.selectedCountryIndex = country.index

        # Check for a control code.
        if link == 'fullscreen':
            isDecode = False
            self._viewFullscreen(None)

        # Add this link to the history.
        if link[0:4] != 'edit':
            if addToHistory:
                if len(self.history) > 5:
                    self.history.pop(0)
                self.history.append(link)

        # Decode the request into action and parameters.
        if isDecode:
            nSplit = link.find('?')
            if nSplit == -1:
                self.request = link
                self.parameters = ''
            else:
                self.parameters = link[nSplit+1:]
                self.request = link[:nSplit]

        # This should be changed to call the version in application.

        # Call this function once there are no messages in the queue (ie the wait cursor has appeared).
        # GObject.idle_add(self.openCurrentPage)
        GLib.idle_add(self.openCurrentPage)



    def decodeParameters(self, parametersString):
        '''
        Decode the parameters from a link into a dictionary object.

        :param string parametersString: Specify the request parameters as a string.
        :returns: A dictionary object of the parameter names and values.
        '''
        # Create an empty dictionary.
        parametersDictionary = {}

        # Split into Key Value pairs by the '&' character.
        items = parametersString.split('&')
        for item in items:
            if item != '':
                key, value = item.split('=')
                parametersDictionary[key] = value

        # Return the dictionary object built.
        return parametersDictionary



    def openCurrentPage(self):
        '''
        Load the current page as specified by :py:attr:`self.request` and :py:attr:`self.parameters` attributes.
        Add the options from the main window toolbar to the parameters and fetch the page from the render object.
        This will call :py:func:`displayCurrentPage` if the content changes.
        Display chain is :py:func:`followLocalLink` → :py:func:`openCurrentPage` → :py:func:`displayCurrentPage`.
        '''
        parametersString = self.parameters

        # Check for the age flag.
        toolbuttonAge = self.builder.get_object('toolbuttonAge')
        if toolbuttonAge.get_active():
            parametersString += '&age=show'

        # Check for a year range.
        #if not self.yearRange.allYears:
        #    parametersString += '&firstyear={}&lastyear={}'.format(self.yearRange.firstYear, self.yearRange.lastYear)

        # Check for a selected tournament.
        #if self.selectedTournamentIndex != None:
        #    parametersString += '&tournamentid={}'.format(self.selectedTournamentIndex)

        # Check for a selected country.
        #if self.selectedCountryIndex != None:
        #    parametersString += '&countryid={}'.format(self.selectedCountryIndex)

        # Check for a specified level.
        if self.selectedLevel != None:
            parametersString += '&level={}'.format(self.selectedLevel)

        # Remove the initial '&' (if any).
        if parametersString[0:1] == '&':
            parametersString = parametersString[1:]

        # Display this request.
        if self.application.debug:
            print("Request '{}', Parameters '{}'".format(self.request, parametersString))

        parameters = self.decodeParameters(parametersString)

        isNewContent = True

        # This is like a switch statement (that Python does not support).
        if self.request in self.render.actions:
            isNewContent = True
            self.render.actions[self.request](parameters)
        elif self.request in self.actions:
            isNewContent = True
            self.actions[self.request](parameters)
        else:
            # Error don't do anything.
            isNewContent = False

        # Display the content created by the database.
        if isNewContent:
            self.displayCurrentPage()

        # Remove the wait cursor.
        if self.window.get_window() != None:
            self.window.get_window().set_cursor(None)
        if self.webview.get_window() != None:
            self.webview.get_window().set_cursor(None)

        # Return false so that idle_add does not call here again.
        return False



    def displayCurrentPage(self):
        '''
        Display the current content on the window.
        This is mainly the html content in the webview widget but also includes updating the toolbar options.
        This does not reload the page from the render object, use :py:func:`openCurrentPage` for that.
        Display chain is :py:func:`followLocalLink` → :py:func:`openCurrentPage` → :py:func:`displayCurrentPage`.
        '''
        # print "displayCurrentPage()"

        # No events / signals until this finishes.
        self.noEvents += 1

        # Enable / disable the back button.
        toolbuttonBack = self.builder.get_object('toolbuttonBack')
        menuitemFileBack = self.builder.get_object('menuitemFileBack')
        if len(self.history) > 1:
            toolbuttonBack.set_sensitive(True)
            menuitemFileBack.set_sensitive(True)
        else:
            toolbuttonBack.set_sensitive(False)
            menuitemFileBack.set_sensitive(False)

        # Enable / disable the edit buttons.
        toolbuttonEdit = self.builder.get_object('toolbuttonEdit')
        menuitemEditEdit = self.builder.get_object('menuitemEditEdit')
        if self.render.editTarget == None:
            # Disable the button.
            toolbuttonEdit.set_sensitive(False)
            menuitemEditEdit.set_sensitive(False)
        else:
            # Enable the button.
            toolbuttonEdit.set_sensitive(True)
            menuitemEditEdit.set_sensitive(True)

        # Enable / disable the Next button.
        toolbuttonNext = self.builder.get_object('toolbuttonNext')
        menuitemViewNext = self.builder.get_object('menuitemViewNext')
        if self.render.nextPage == None:
            # Disable the button.
            toolbuttonNext.set_sensitive(False)
            menuitemViewNext.set_sensitive(False)
        else:
            # Enable the button.
            toolbuttonNext.set_sensitive(True)
            menuitemViewNext.set_sensitive(True)

        # Enable / disable the Previous button.
        toolbuttonPrevious = self.builder.get_object('toolbuttonPrevious')
        menuitemViewPrevious = self.builder.get_object('menuitemViewPrevious')
        if self.render.previousPage == None:
            # Disable the button.
            toolbuttonPrevious.set_sensitive(False)
            menuitemViewPrevious.set_sensitive(False)
        else:
            # Enable the button.
            toolbuttonPrevious.set_sensitive(True)
            menuitemViewPrevious.set_sensitive(True)

        # Enable / Disable the Age button.
        #toolbuttonAge = self.builder.get_object('toolbuttonAge')
        #if self.render.showAge and self.database.currentSport.birthdates:
        #    toolbuttonAge.set_sensitive(True)
        #else:
        #    toolbuttonAge.set_sensitive(False)
        #    toolbuttonAge.set_active(False)

        # Enable / Disable the tournaments menu system.
        #tbmenuTournament = self.builder.get_object('tbmenuTournament')
        #if self.render.tournamentSelect and len(self.database.currentSport.tournamentsByStatus)>1:
        #    # Check that the menu options are upto date
        #    if self.tournamentSportIndex != self.database.currentSport.index:
        #        for nIndex in [1, 2, 3, 4]:
        #            menuTourament = self.builder.get_object('menuTournament'+str(nIndex))
        #            if len(self.database.currentSport.tournamentsByStatus) >= nIndex:
        #                tournament = #self.database.getTournament(self.database.currentSport.tournamentsByStatus[nIndex-1])
        #                menuTourament.set_visible(True)
        #                menuTourament.set_label(tournament.name)
        #            else:
        #                menuTourament.set_visible(False)
        #        self.tournamentSportIndex=self.database.currentSport.index
        #    tbmenuTournament.set_sensitive(True)
        #else:
        #    tbmenuTournament.set_label('All Tournaments')
        #    tbmenuTournament.set_sensitive(False)
        #    self.selectedTournamentIndex = None

        # Enable / Disable the levels menu system.
        menutoolbuttonLevel = self.builder.get_object('menutoolbuttonLevel')
        if self.render.levels == None:
            menutoolbuttonLevel.set_label('Default')
            menutoolbuttonLevel.set_sensitive(False)
            self.selectedLevel = None
        else:
            for nIndex in [1, 2, 3, 4, 5, 6]:
                menuitemLevel = self.builder.get_object('menuitemLevel'+str(nIndex))
                if len(self.render.levels) >= nIndex:
                    menuitemLevel.set_visible(True)
                    menuitemLevel.set_label(self.render.levels[nIndex-1])
                else:
                    menuitemLevel.set_visible(False)
            menutoolbuttonLevel.set_sensitive(True)

        # Enable / Disable the country select button.
        tbbCountry = self.builder.get_object('tbbCountry')
        if self.render.countrySelect:
            tbbCountry.set_sensitive(True)
        else:
            tbbCountry.set_label('All Countries')
            tbbCountry.set_sensitive(False)
            self.selectedCountryIndex = None

        # Enable / Disable the year range button.
        tbbYears = self.builder.get_object('tbbYears')
        if self.render.yearsSelect:
            tbbYears.set_sensitive(True)
        else:
            tbbYears.set_label('All Years')
            self.yearRange.allYears = True
            tbbYears.set_sensitive(False)

        # Enable / Disable the copy menu item.
        menuEditCopy = self.builder.get_object('menuCopy')
        if self.render.clipboardText != None:
            menuEditCopy.set_sensitive(True)
        else:
            menuEditCopy.set_sensitive(False)

        # Display the html content on the webview control.
        #if _useWebKit2:
        self.webview.load_html(self.render.html.toHtml(), 'file:///')

        # self.webview.loadData(self.render.html.toHtml(),'text/html', 'UTF-8')
        #else:
        #    self.webview.load_string(self.render.html.toHtml(), 'text/html', 'UTF-8', 'file:///')

        # Events / signals back on.
        self.noEvents -= 1



    def editTeam(self, parameters):
        '''
        Displays the EditMatches dialog with initial matches on the specified date.
        '''
        teamIndex = parameters['team'] if 'team' in parameters else None

        sql = f"SELECT ID, THE_DATE, 0 AS THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE HOME_TEAM_ID = {teamIndex} OR AWAY_TEAM_ID = {teamIndex} ORDER BY THE_DATE DESC;"

        # Edit these matches.
        dialog = glade.edit_matches.EditMatches(self.window)
        if dialog.editMatches(self.database, sql):
            self.render.showHome({'season': seasonIndex})
        return True




    def editDate(self, parameters):
        '''
        Displays the EditMatches dialog with initial matches on the specified date.
        '''
        seasonIndex = parameters['season']
        theDate = parameters['date'] if 'date' in parameters else None

        if theDate is None:
            sql = f"SELECT ID, THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = {seasonIndex} ORDER BY THE_DATE DESC LIMIT 20"
        else:
            sql = f"SELECT ID, THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = {seasonIndex} AND THE_DATE = '{theDate}'"

        dialog = glade.edit_matches.EditMatches(self.window)
        if dialog.editMatches(self.database, sql, seasonIndex):
            self.render.showHome({'season': seasonIndex})
        return True



    def editSeason(self, parameters):
        '''
        Displays the EditSeason dialog.
        Opens a dialog to allow the user to edit the specified season and writes the results into the database.

        :param Dict parameters: Specifies the parameters as a dictionary.  This should include a 'season' key that identifies the season to edit.
        '''
        seasonIndex = int(parameters['season']) if 'season' in parameters else None

        dialog = glade.edit_season.EditSeason(self.window)
        if dialog.editSeason(self.database, seasonIndex):
            self.render.showSeason({'season': seasonIndex})
        return True



    def editMatches(self, parameters):
        '''
        Displays the EditMatches dialog.
        Opens a dialog to allow the user to edit the specified season and writes the results into the database.

        :var Dict parameters: Specifies the parameters as dictionary. This should include a 'index' key that identifies the tournament season to edit.
        '''
        # Decode the parameters.
        tournamentSeasonIndex = int(parameters['index']) if 'index' in parameters else None

        if tournamentSeasonIndex != None:
            dialog = glade.edit_matches.EditMatches(self.window)
            dialog.editMatches(self.database, tournamentSeasonIndex)

            self.render.showTournamentSeason({'index': tournamentSeasonIndex})

        return True



    def editSport(self, parametersString):
        '''
        Displays the editSport dialog.
        Opens a dialog to allow the user to edit the current sport.
        Any changes are written to the database.

        :var string parametersString: Specifies the parameters as a string. No keys are required.
        '''
        dialog = glade.edit_sport.EditSport(self.window)
        if dialog.editSport(self.database):
            return True
        return False



    def addSport(self, parameters):
        '''
        Displays the editSport dialog.
        Open a dialog to allow the user to create a new sport.
        The user selections are written to the database.
        '''
        dialog = glade.edit_sport.EditSport(self.window)
        if dialog.addSport(self.database):
            return True
        return False



    def editTournament(self, parameters):
        ''' Displays the EditTournament dialog. '''
        # Decode the parameters.
        tournament = self.database.getTournament(int(parameters['tournament'])) if 'tournament' in parameters else None

        dialog = glade.edit_tournament.EditTournament(self.window)
        if tournament != None:
            if dialog.editTournament(tournament):
                return True
        else:
            if dialog.addTournament(self.database):
                self.database.currentSport.loadTournaments()
                return True
        return False



    def editLocation(self, parameters):
        ''' Displays the EditLocation dialog. '''
        locationID = int(parameters['location']) if 'location' in parameters else None

        # Display the dialog.
        dialog = glade.edit_location.EditLocation(self.window)
        if locationID == None:
            return dialog.addLocation(self.database)
        else:
            location = self.database.getLocation(locationID)
            return dialog.editLocation(location)
        return False



    def editCountry(self, parameters):
        '''
        Displays the EditCountry dialog.
        Opens a dialog to allow the user to edit the specified country.
        Any changes are written to the countries database.

        :var string parametersString: Specifies the parameters as a string.  This should include a 'id' key that identifies the country.
        '''
        # Decode the parameters.
        if 'id' in parameters:
            # Display the particular country.
            country = self.database.getCountry(parameters['id'])

            dialog = walton.glade.edit_country.EditCountry(self.window)
            if dialog.editCountry(country):
                return True
        return False

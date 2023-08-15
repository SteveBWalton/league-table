# -*- coding: utf-8 -*-

'''
Module to support the Edit Season dialog.
This module implements the :py:class:`EditSeason` class.
'''



# Import Gtk3 libraries.
# Gdk is required for drag-drop.
try:
    from gi.repository import Gtk, GObject, Gdk
except:
    print('GTK Not Available ({})'.format(__name__))

import sqlite3
import datetime
import time
import os
from datetime import timedelta

# Application libraries.
#import glade.edit_team
#import glade.edit_location
#import glade.edit_season
#import glade.edit_points



class EditSeason:
    '''
    Class to represent the dialog that allows the user to edit seasons.

    :ivar Database database: The Database to edit results in.
    :ivar Season season: The season object to edit.
    :ivar Gtk.Builder builder: The GTK builder for the dialog.
    :ivar Gtk.Dialog dialog: The actial GTK dialog.
    '''



    def __init__(self, parentWindow):
        '''
        Class constructor for the :py:class:`EditSeason` class.
        Construct the dialog but do not show it.
        Call :py:func:`editSeason` to actually show the dialog.

        :param Gtk.Window parentWindow: Specify the GTK+ parent window for the dialog.
        '''
        # Initialise member variables.
        self.database = None
        self.season = None

        # The GTK builder for the dialog.
        self.builder = Gtk.Builder()
        self.builder.add_from_file('{}/edit_season.glade'.format(os.path.dirname(os.path.realpath(__file__))))
        # The actual GTK dialog.
        self.dialog = self.builder.get_object('dialogEditSeason')
        self.dialog.set_transient_for(parentWindow)

        # Custom settings that don't work from glade.

        # Add the events to the dialog.
        #signals = {
        #    'on_cmdAddRow_clicked'                  : self._addRow,
        #    'on_cmdDeleteRow_clicked'               : self._deleteRow,
        #
        #    'on_cellrenderercomboDate_edited'       : self._matchDateEdited,
        #    'on_cellrendertoggleDateGuess_toggled'  : self._dateGuessToggled,
        #    'on_cellrenderercomboTeam1_changed'     : self._homeTeamChanged,
        #    'on_cellrenderertextScore_edited'       : self._homeScoreEdited,
        #    'on_cellrenderercomboTeam2_changed'     : self._awayTeamChanged,
        #    'on_cellrenderertextAwayScore_edited'   : self._awayScoreEdited,
        #}
        #self.builder.connect_signals(signals)

        # Set the add link button as a drag-drop target.
        #buttonAddLink = self.builder.get_object('buttonAddLink')
        #buttonAddLink.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        #buttonAddLink.drag_dest_add_text_targets()



    def _matchDateEdited(self, widget, row, newValue):
        ''' Signal handler for the match date changing in a cell. '''
        liststoreMatches = self.builder.get_object('liststoreMatches')
        if newValue == 'Pick...':
            # Create a dialog with a calendar control.
            dialog = Gtk.Dialog('Pick Date', self.dialog, Gtk.DialogFlags.MODAL,(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
            calendar = Gtk.Calendar()

            # Get the current value from the grid control.
            iterMatches = liststoreMatches.get_iter(int(row))
            currentValue = liststoreMatches.get_value(iterMatches, 2)
            # print 'Current Date {}'.format(sCurrentValue)
            theMonth = currentValue[3:5]
            # print 'Current Month {}'.format(sMonth)
            if theMonth == '..':
                monthIndex = datetime.date.today().month - 1
            else:
                dtCurrent = datetime.date(*time.strptime(currentValue, "%d-%m-%Y")[:3])
                calendar.select_day(dtCurrent.day)
                monthIndex = int(theMonth)-1

            # Setup the current year as the initial value.
            theYear = datetime.date.today().year
            calendar.select_month(monthIndex, theYear)

            calendar.show()
            dialog.get_content_area().add(calendar)

            # Display the dialog.
            response = dialog.run()

            # Decode the response from the dialog.
            if response == Gtk.ResponseType.OK:
                tupDate = calendar.get_date()
                newValue = '{:0=2}-{:0=2}-{}'.format(tupDate[2], 1+tupDate[1], tupDate[0])
            else:
                newValue = 'None'
            dialog.destroy()
        elif newValue == 'As Above' or newValue == 'Day After Above' or newValue == 'Day Before Above' or newValue == '2 Days Before Above':
            if row == 0:
                newValue = 'None'
            else:
                iterMatches = liststoreMatches.get_iter(int(row)-1)
                if newValue == 'Day After Above':
                    newValue = liststoreMatches.get_value(iterMatches, 2)
                    dtCurrent = datetime.date(*time.strptime(newValue, "%d-%m-%Y")[:3])
                    dtCurrent = dtCurrent + timedelta(days=1)
                    newValue = dtCurrent.strftime('%d-%m-%Y')
                elif newValue == 'Day Before Above':
                    newValue = liststoreMatches.get_value(iterMatches, 2)
                    dtCurrent = datetime.date(*time.strptime(newValue, "%d-%m-%Y")[:3])
                    dtCurrent = dtCurrent - timedelta(days=1)
                    newValue = dtCurrent.strftime('%d-%m-%Y')
                elif newValue == '2 Days Before Above':
                    newValue = liststoreMatches.get_value(iterMatches, 2)
                    dtCurrent = datetime.date(*time.strptime(newValue, "%d-%m-%Y")[:3])
                    dtCurrent = dtCurrent - timedelta(days=2)
                    newValue = dtCurrent.strftime('%d-%m-%Y')
                else:
                    newValue = liststoreMatches.get_value(iterMatches, 2)
                # Set guess as above.
                isGuess = liststoreMatches.get_value(iterMatches, 3)
                iterMatches = liststoreMatches.get_iter(row)
                liststoreMatches.set_value(iterMatches, 3, isGuess)

        elif newValue == 'Today':
            newValue = datetime.date.today().strftime('%d-%m-%Y')

        iterMatches = liststoreMatches.get_iter(row)
        liststoreMatches.set(iterMatches, 1, 1, 2, newValue)
        self.isChanged = True



    def _homeTeamChanged(self, widget, row, iterSelected):
        ''' Signal handler the the team one cell value changing. '''
        # Get the selected values from the combobox.
        liststoreTeams = self.builder.get_object('liststoreTeams')
        teamIndex = liststoreTeams.get_value(iterSelected, 0)

        if teamIndex == -1:
            # All...
            self.populateTeamCombos(-1)
            return;
        if teamIndex == -3:
            # More...
            self.populateTeamCombos(-3)
            return;
        if teamIndex == -2:
            # New...
            dialog = glade.edit_team.EditTeam(self.dialog)
            dialog.editNewTeam(self.database, self.tournamentSeason.season.theFinish.year)
            self.populateTeamCombos(self.tournamentSeason.season.theFinish.year)
            return

        # Lookup the name of the team.
        if teamIndex == 0:
            teamLabel = '<None>'
        else:
            teamLabel = liststoreTeams.get_value(iterSelected, 1)

        # Calculate the seed of the team.
        # seed = self.searchSeed(teamIndex)

        # Update the matches liststore.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatches = liststoreMatches.get_iter(row)
        liststoreMatches.set(iterMatches, 1, 1, 4, teamIndex, 5, teamLabel)
        self.isChanged = True



    def _awayTeamChanged(self, widget, row, iterSelected):
        ''' Signal handler for the team two value changing. '''
        # Get the selected values from the combobox.
        liststoreTeams = self.builder.get_object('liststoreTeams')
        teamIndex = liststoreTeams.get_value(iterSelected, 0)

        if teamIndex == -1:
            # All...
            self.populateTeamCombos(-1)
            return;
        if teamIndex == -3:
            # More...
            self.populateTeamCombos(-3)
            return;
        if teamIndex == -2:
            # New...
            dialog = glade.edit_team.EditTeam(self.dialog)
            dialog.editNewTeam(self.database, self.tournamentSeason.season.theFinish.year)
            self.populateTeamCombos(self.tournamentSeason.season.theFinish.year)
            return

        # Lookup the name of this team.
        if teamIndex == 0:
            teamLabel = '<None>'
        else:
            teamLabel = liststoreTeams.get_value(iterSelected, 1)

        # Calculate the seed of the team.
        # seed = self.searchSeed(teamIndex)

        # Update the matches liststore.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatches = liststoreMatches.get_iter(row)
        liststoreMatches.set(iterMatches, 1, 1, 6, teamIndex, 7, teamLabel)
        self.isChanged = True



    def _dateGuessToggled(self, widget, row):
        ''' Signal handler for the date guess value changing in a cell. '''
        isActive = widget.get_active()
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatches = liststoreMatches.get_iter(row)
        if isActive:
            liststoreMatches.set(iterMatches, 1, 1, 3, False)
        else:
            liststoreMatches.set(iterMatches, 1, 1, 3, True)

            ## Try and guess the date ?
            #row = int(row)
            #if row > 0:
            #    theDate = liststoreMatches.get_value(iterMatches, 1)
            #    if theDate[0:2] == '..':
            #        # Date is unknow.  Check the date above.
            #        iterAbove = liststoreMatches.get_iter(int(row)-1)
            #        dateAbove = liststoreMatches.get_value(iterAbove, 1)
            #        if dateAbove[0:2] != '..':
            #            # Check if same type of match.
            #            matchType = liststoreMatches.get_value(iterMatches, 2)
            #            matchTypeAbove = liststoreMatches.get_value(iterAbove, 2)
            #            # print('MatchType {} {}'.format(matchType, matchTypeAbove))
            #            if matchType != matchTypeAbove:
            #                dtCurrent = datetime.date(*time.strptime(dateAbove, "%d-%m-%Y")[:3])
            #                dtCurrent = dtCurrent - timedelta(days=2)
            #                dateAbove = dtCurrent.strftime('%d-%m-%Y')
            #            # Guess the date.
            #            liststoreMatches.set_value(iterMatches, 1, dateAbove)

        self.isChanged = True




    def _homeScoreEdited(self, widget, row, newValue):
        ''' Signal handler for the home score value changing in a cell. '''
        # Convert the input into a number.
        homeScore = -1
        try:
            homeScore = int(newValue)
        except:
            homeScore = -1

        # Only set if a valid value.
        if homeScore >= 0:
            liststoreMatches = self.builder.get_object('liststoreMatches')
            iterMatches = liststoreMatches.get_iter(row)
            liststoreMatches.set(iterMatches, 1, 1, 8, homeScore)
            self.isChanged = True



    def _awayScoreEdited(self, widget, row, newValue):
        ''' Signal handler for the home score value changing in a cell. '''
        # Convert the input into a number.
        awayScore = -1
        try:
            awayScore = int(newValue)
        except:
            awayScore = -1

        # Only set if a valid value.
        if awayScore >= 0:
            liststoreMatches = self.builder.get_object('liststoreMatches')
            iterMatches = liststoreMatches.get_iter(row)
            liststoreMatches.set(iterMatches, 1, 1, 9, awayScore)
            self.isChanged = True



    def _addRow(self, widget):
        ''' Signal handler for the 'Add Row' button. '''
        # Add a new row.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        newRow = liststoreMatches.append()

        # Using the '<None>' because in this version of GTK+3 the combobox will not scroll forward only backwards so start at the end!
        theYear = datetime.date.today().year
        liststoreMatches.set(newRow, 0, 0, 1, 0, 2, '..-..-' + str(theYear), 3, False, 5, '<None>', 7, '<None>', 8, 0, 9, 0)

        # Get the number of results.
        count = 0
        iterMatches = liststoreMatches.get_iter_first()
        while iterMatches:
            count += 1
            iterMatches = liststoreMatches.iter_next(iterMatches)

        # Show this row on the window.
        treeviewMatches = self.builder.get_object('treeviewMatches')
        path = (count - 1,)
        treeviewMatches.scroll_to_cell(path, None, True, 1, 0)



    def _deleteRow(self, widget):
        ''' Signal handler for the 'Delete Match' button. '''
        # Find the selected row.
        treeviewMatches = self.builder.get_object('treeviewMatches')
        matchPath, focusColumn = treeviewMatches.get_cursor()
        if matchPath == None:
            # Nothing is selected
            return

        # Find the selected record.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatch = liststoreMatches.get_iter(matchPath)
        matchIndex = liststoreMatches.get_value(iterMatch, 0)
        if matchIndex > 0:
            self.matchesDelete.append(matchIndex)

        # Remove the identified row.
        liststoreMatches.remove(iterMatch)



    def writeChanges(self):
        ''' Write the contents of the dialog to the database. '''
        entrySeason = self.builder.get_object('entrySeason')
        self.season.name = entrySeason.get_text()



    def populateDialog(self):
        ''' Populate the dialog with settings from the season object. '''
        entrySeason = self.builder.get_object('entrySeason')
        try:
            entrySeason.set_text(self.season.name)
        except:
            pass



    def editSeason(self, database, season):
        '''
        Show the dialog and allow the user to edit the matches.

        :param Database database: Specify the database to read and write seasons.
        :param Season season: Specify the season object to edit.
        '''

        # Save the parameters, initialise the class.
        self.database = database
        self.season = season

        # Populate the dialog.
        self.populateDialog()

        # Show the dialog and wait for a response.
        response = self.dialog.run()

        # Save the changes if the user clicked OK ( and there are any changes ).
        if response == Gtk.ResponseType.OK:
            self.writeChanges()

        # Close the dialog.
        self.dialog.hide()
        self.dialog.destroy()

        return response == Gtk.ResponseType.OK

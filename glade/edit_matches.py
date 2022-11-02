# -*- coding: utf-8 -*-

'''
Module to support the Edit Matches dialog.
This module implements the :py:class:`EditMatches` class.
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



class EditMatches:
    '''
    Class to represent the dialog that allows the user to edit match results.
    This is the way that the user enters data into the program.

    :ivar Database database: The Database to edit results in.
    :ivar int tournamentDetails: The details level of the current tournament.
    :ivar int year: The year of the current edits.
    :ivar int tournamentIndex: The ID of the tournament of the current edits.
    :ivar bool isChanged: True if the current edits are not written to the database.  False if there are no changes on the current edits.
    :ivar Gtk.Builder builder: The GTK builder for the dialog.
    :ivar Gtk.Dialog dialog: The actial GTK dialog.
    :ivar list linksDelete: The list of link IDs to delete.
    '''



    def __init__(self, parentWindow):
        '''
        Class constructor for the :py:class:`EditMatches` class.
        Construct the dialog but do not show it.
        Call :py:func:`editMatches` to actually show the dialog.

        :param Gtk.Window parentWindow: Specify the GTK+ parent window for the dialog.
        '''
        # Initialise member variables.
        self.database = None
        self.tournamentDetails = -1
        # self.year = -1
        # self.tournamentIndex = -1
        self.isChanged = False
        # The link IDs to delete.
        self.linksDelete = []
        # The match records to delete.
        self.matchesDelete = []

        # The GTK builder for the dialog.
        self.builder = Gtk.Builder()
        self.builder.add_from_file('{}/edit_matches.glade'.format(os.path.dirname(os.path.realpath(__file__))))
        # The actual GTK dialog.
        self.dialog = self.builder.get_object('dialogEditMatches')
        self.dialog.set_transient_for(parentWindow)

        # Custom settings that don't work from glade.
        cellrenderertextHomeScore = self.builder.get_object('cellrenderertextHomeScore')
        cellrenderertextHomeScore.set_alignment(0.5, 0.5)
        cellrenderertextAwayScore = self.builder.get_object('cellrenderertextAwayScore')
        cellrenderertextAwayScore.set_alignment(0.5, 0.5)
        #cellrenderertextSeed1 = self.builder.get_object('cellrenderertextSeed1')
        #cellrenderertextSeed1.set_alignment(0.5, 0.5)
        #cellrenderertextSeed2 = self.builder.get_object('cellrenderertextSeed2')
        #cellrenderertextSeed2.set_alignment(0.5, 0.5)

        # Add the events to the dialog.
        signals = {
            'on_cmdAddRow_clicked'                  : self._addRow,
            'on_cmdDeleteRow_clicked'               : self._deleteRow,

            'on_cellrenderercomboDate_edited'       : self._matchDateEdited,
            'on_cellrendertoggleDateGuess_toggled'  : self._dateGuessToggled,
            'on_cellrenderercomboTeam1_changed'     : self._homeTeamChanged,
            'on_cellrenderertextScore_edited'       : self._homeScoreEdited,
            'on_cellrenderercomboTeam2_changed'     : self._awayTeamChanged,
            'on_cellrenderertextAwayScore_edited'   : self._awayScoreEdited,
        }
        self.builder.connect_signals(signals)

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
            theYear = 2022
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
        theYear = 2022
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
        # Get handlers to the liststores.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        liststoreTeams = self.builder.get_object('liststoreTeams')

        # Get the current mode.
        comboboxMode = self.builder.get_object('comboboxMode')
        modeIter = comboboxMode.get_active_iter()
        liststoreModes = self.builder.get_object('liststoreModes')
        activeMode = liststoreModes.get_value(modeIter, 0)

        # Open the database.
        cndb = sqlite3.connect(self.database.filename)

        # Remove any matches marked for delete.
        for matchIndex in self.matchesDelete:
            sql = f"DELETE FROM MATCHES WHERE ID = {matchIndex};"
            cursor = cndb.execute(sql)
            cndb.commit()

        # Loop through the liststore of matches.
        iterMatches = liststoreMatches.get_iter_first()
        while iterMatches:
            matchIndex = liststoreMatches.get_value(iterMatches, 0)
            isChange = True if liststoreMatches.get_value(iterMatches, 1) == 1 else False
            if isChange:
                theDate = liststoreMatches.get_value(iterMatches, 2)
                if theDate == 'None' or theDate[0:1] == '.':
                    theDate = 'NULL'
                else:
                    dtDate = datetime.date(*time.strptime(theDate, "%d-%m-%Y")[:3])
                    # strftime does not work for years < 1900, so don't use it.
                    theDate = "'{}-{:0=2}-{:0=2}'".format(dtDate.year, dtDate.month, dtDate.day)
                isDateGuess = 1 if liststoreMatches.get_value(iterMatches, 3) else 0
                homeTeamIndex = liststoreMatches.get_value(iterMatches, 4)
                awayTeamIndex = liststoreMatches.get_value(iterMatches, 6)
                homeTeamFor = liststoreMatches.get_value(iterMatches, 8)
                awayTeamFor = liststoreMatches.get_value(iterMatches, 9)

                if matchIndex == 0:
                    sql = f"INSERT INTO MATCHES (SEASON_ID, THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, REAL_HOME_TEAM_FOR, REAL_AWAY_TEAM_FOR) VALUES ({self.seasonIndex}, {theDate}, {isDateGuess}, {homeTeamIndex}, {awayTeamIndex}, {homeTeamFor}, {awayTeamFor});"
                else:
                    if activeMode == 1:
                        # What if mode.
                        sql = f"UPDATE MATCHES SET THE_DATE = {theDate}, THE_DATE_GUESS = {isDateGuess}, HOME_TEAM_ID = {homeTeamIndex}, AWAY_TEAM_ID = {awayTeamIndex}, HOME_TEAM_FOR = {homeTeamFor}, AWAY_TEAM_FOR = {awayTeamFor} WHERE ID = {matchIndex};"
                    else:
                        # Real mode.
                        sql = f"UPDATE MATCHES SET THE_DATE = {theDate}, THE_DATE_GUESS = {isDateGuess}, HOME_TEAM_ID = {homeTeamIndex}, AWAY_TEAM_ID = {awayTeamIndex}, HOME_TEAM_FOR = {homeTeamFor}, AWAY_TEAM_FOR = {awayTeamFor}, REAL_HOME_TEAM_FOR = {homeTeamFor}, REAL_AWAY_TEAM_FOR = {awayTeamFor} WHERE ID = {matchIndex};"

                # Execute the command.
                # print(sql)
                # cursor = cnDb.execute(sql, params)
                cursor = cndb.execute(sql)
                cndb.commit()

            # Move to next record.
            iterMatches = liststoreMatches.iter_next(iterMatches)

        # Close the database.
        cndb.close()

        # Mark the data as saved.
        self.isChanged = False



    def populateTeamCombos(self, year):
        '''
        Populate the team comboboxes with the available teams.
        If the sports had retiring teams then only the teams with results around the specified year (and currentSport.lastYearPadding) will be added to the comboxboxes.
        :param int year: Specifies the year for the teams.  Specify -1 for all teams regarding of currentSport.lastYearPadding.  Specify -3 for extra teams.
        '''
        # print('populateTeamCombos')

        # Fetch the liststore
        liststoreTeams = self.builder.get_object('liststoreTeams')
        liststoreTeams.clear()

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        # Fetch the list of teams.
        sql = 'SELECT ID, LABEL FROM TEAMS ORDER BY LABEL;'
        cursor = cndb.execute(sql)
        for row in cursor:
            newRow = liststoreTeams.append()
            teamName = row[1]
            if row[0] == None:
                print('Error ({}) "{}"'.format(row[0], teamName))
            else:
                liststoreTeams.set(newRow, 0, row[0], 1, teamName)
        cursor.close()

        # Add the special buttons.
        #newRow = liststoreTeams.append()
        #liststoreTeams.set(newRow, 0, 0, 1, '<None>')
        #if isSpecialOption:
        #    newRow = liststoreTeams.append()
        #    liststoreTeams.set(newRow, 0, -1, 1, 'All...')
        #    newRow = liststoreTeams.append()
        #    liststoreTeams.set(newRow, 0, -3, 1, 'More...')

        #newRow = liststoreTeams.append()
        #liststoreTeams.set(newRow, 0, -2, 1, 'New...')

        # Close the database.
        cndb.close()



    def populateMatches(self, sql):
        ''' Populate the dialog with the matches from the year and tournament specified on the dialog. '''
        if self.database == None:
            return

        # print 'Populate Matches Season {} TournamentID {}'.format(theYear,tournamentIndex)
        entrySeason = self.builder.get_object('entrySeason')
        entrySeason.set_text(self.seasonIndex)

        comboboxMode = self.builder.get_object('comboboxMode')
        comboboxMode.set_active(0)

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        # If the year has changed then load another group of players.
        self.populateTeamCombos(0)

        if sql == '':
            return
        # print(sql)

        # Build the list of actual matches.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        liststoreMatches.clear()

        # Fetch the list of matches in this tournament.
        cursor = cndb.execute(sql)
        for row in cursor:
            newRow = liststoreMatches.append()
            if row[1] == None:
                theDate = f'..-..-{2022}'
            else:
                theDate = f'{row[1][8:10]}-{row[1][5:7]}-{row[1][0:4]}'
            isDateGuess = True if row[2] == 1 else False
            if row[3] == None or row[3] == 0:
                homeTeamName = '<None>'
            else:
                team = self.database.getTeam(row[3])
                homeTeamName = team.toHtml(False, True)
            if row[4] == None or row[4] == 0:
                awayTeamName = '<None>'
            else:
                team = self.database.getTeam(row[4])
                awayTeamName = team.toHtml(False, True, None)
            liststoreMatches.set(newRow, 0, row[0], 1, 0, 2, theDate, 3, isDateGuess, 4, row[3], 5, homeTeamName, 6, row[4], 7, awayTeamName, 8, row[5], 9, row[6])
        cursor.close()

        # Close the database.
        cndb.close()

        # The database is up to date with the dialog contents.
        self.isChanged = False



    def editMatches(self, database, sql, seasonIndex):
        '''
        Show the dialog and allow the user to edit the matches.

        :param Database database: Specify the database to read and write matches.
        :param int tournamentSeasonIndex: Specify the tournament season to edit.
        '''

        #liststoreSeasons = self.builder.get_object('liststoreSeasons')
        #cboSeason = self.builder.get_object('cboSeason')
        #cell = Gtk.CellRendererText()
        #cboSeason.pack_start(cell, True)
        #cboSeason.add_attribute(cell, 'text', 1)

        # Add the seasons to the combobox liststoreSeasons.
        #count = 0
        #seasons = database.currentSport.getSeasons()
        #for index, seasonIndex in enumerate(seasons):
        #    season = database.getSeason(seasonIndex)
        #    newRow = liststoreSeasons.append(None)
        #    liststoreSeasons.set(newRow, 0, season.index, 1, season.name)
        #    # print('{} {} {}'.format(index, season.index, season.name))
        #    if seasonIndex == self.tournamentSeason.seasonIndex:
        #        count = index
        ## print('Set season to {}'.format(count))
        #cboSeason.set_active(count)

        # Save the parameters, initialise the class.
        self.database = database
        self.seasonIndex = seasonIndex

        # Populate the list of matches.
        self.populateMatches(sql)

        # Show the dialog and wait for a response.
        response = self.dialog.run()

        # Save the changes if the user clicked OK ( and there are any changes ).
        if response == Gtk.ResponseType.OK:
            self.writeChanges()

        # Close the dialog.
        self.dialog.hide()
        self.dialog.destroy()

        return response == Gtk.ResponseType.OK

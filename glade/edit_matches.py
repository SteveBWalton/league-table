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

        # The GTK builder for the dialog.
        self.builder = Gtk.Builder()
        self.builder.add_from_file('{}/edit_matches.glade'.format(os.path.dirname(os.path.realpath(__file__))))
        # The actual GTK dialog.
        self.dialog = self.builder.get_object('dialogEditMatches')
        self.dialog.set_transient_for(parentWindow)

        # Custom settings that don't work from glade.
        cellrenderertextScore = self.builder.get_object('cellrenderertextScore')
        cellrenderertextScore.set_alignment(0.5, 0.5)
        cellrenderertextSeed1 = self.builder.get_object('cellrenderertextSeed1')
        cellrenderertextSeed1.set_alignment(0.5, 0.5)
        cellrenderertextSeed2 = self.builder.get_object('cellrenderertextSeed2')
        cellrenderertextSeed2.set_alignment(0.5, 0.5)

        # Add the events to the dialog.
        signals = {
            'on_cboTournament_changed'              : self._selectionChanged,
            'on_spinYear_value_changed'             : self._selectionChanged,
            'on_cmdApply_clicked'                   : self._applyChanges,
            'on_cmdAddRow_clicked'                  : self._addRow,

            'on_cellrenderercomboDate_edited'       : self._matchDateEdited,
            'on_cellrenderercomboMatchType_changed' : self._matchTypeChanged,
            'on_cellrenderercomboTeam1_changed'     : self._teamOneChanged,
            'on_cellrenderertextScore_edited'       : self._scoreEdited,
            'on_cellrenderercomboTeam2_changed'     : self._teamTwoChanged,
            'on_cellrenderercomboResult_changed'    : self._resultChanged,
            'on_cellrenderertextPts1_edited'        : self._teamOnePtsEdited,
            'on_cellrenderertextPts2_edited'        : self._teamTwoPtsEdited,
            'on_cellrenderertextSeed1_edited'       : self._seedOneEdited,
            'on_cellrenderertextSeed2_edited'       : self._seedTwoEdited,
            'on_cellrenderercomboLocation_changed'  : self._locationChanged,
            'on_cellrendertoggleDateGuess_toggled'  : self._dateGuessToggled,

            'on_buttonAddLink_clicked'              : self._addLink,
            'on_buttonAddLink_drag_data_received'   : self._dragDataReceived,
            'on_buttonRemoveLink_clicked'           : self._deleteLink,
            'on_cellrenderercomboLabel_edited'      : self._linkLabelEdited,
            'on_cellrenderertextUrl_edited'         : self._linkUrlEdited,
            'on_togglebuttonShowSeed_toggled'       : self._seedsToggled,
            'on_togglebuttonShowPoints_toggled'     : self._pointsToggled,
            'on_comboboxDefaultLocation_changed'    : self._defaultLocationChanged,
            'on_buttonDefaultLocationToAll_clicked' : self._defaultLocationToAll,
            'on_buttonSwap_clicked'                 : self._swapTeams,
            'on_buttonEditSeason_clicked'           : self._editSeason,
            'on_buttonEncode_clicked'               : self._encodePoints,
        }
        self.builder.connect_signals(signals)

        # Set the add link button as a drag-drop target.
        buttonAddLink = self.builder.get_object('buttonAddLink')
        buttonAddLink.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        buttonAddLink.drag_dest_add_text_targets()



    def _matchDateEdited(self, widget, row, newValue):
        ''' Signal handler for the match date changing in a cell. '''
        liststoreMatches = self.builder.get_object('liststoreMatches')
        if newValue == 'Pick...':
            # Create a dialog with a calendar control.
            dialog = Gtk.Dialog('Pick Date', self.dialog, Gtk.DialogFlags.MODAL,(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
            calendar = Gtk.Calendar()

            # Get the current value from the grid control.
            iterMatches = liststoreMatches.get_iter(int(row))
            sCurrentValue = liststoreMatches.get_value(iterMatches,1)
            # print 'Current Date {}'.format(sCurrentValue)
            sMonth = sCurrentValue[3:5]
            # print 'Current Month {}'.format(sMonth)
            if sMonth == '..':
                nMonth = datetime.date.today().month-1
            else:
                dtCurrent = datetime.date(*time.strptime(sCurrentValue, "%d-%m-%Y")[:3])
                calendar.select_day(dtCurrent.day)
                nMonth = int(sMonth)-1

            # Setup the current year as the initial value.
            theYear = self.tournamentSeason.season.theFinish.year
            calendar.select_month(nMonth, theYear)

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
                    newValue = liststoreMatches.get_value(iterMatches, 1)
                    dtCurrent = datetime.date(*time.strptime(newValue, "%d-%m-%Y")[:3])
                    dtCurrent = dtCurrent + timedelta(days=1)
                    newValue = dtCurrent.strftime('%d-%m-%Y')
                elif newValue == 'Day Before Above':
                    newValue = liststoreMatches.get_value(iterMatches, 1)
                    dtCurrent = datetime.date(*time.strptime(newValue, "%d-%m-%Y")[:3])
                    dtCurrent = dtCurrent - timedelta(days=1)
                    newValue = dtCurrent.strftime('%d-%m-%Y')
                elif newValue == '2 Days Before Above':
                    newValue = liststoreMatches.get_value(iterMatches, 1)
                    dtCurrent = datetime.date(*time.strptime(newValue, "%d-%m-%Y")[:3])
                    dtCurrent = dtCurrent - timedelta(days=2)
                    newValue = dtCurrent.strftime('%d-%m-%Y')
                else:
                    newValue = liststoreMatches.get_value(iterMatches, 1)
                # Set guess as above.
                isGuess = liststoreMatches.get_value(iterMatches, 17)
                iterMatches = liststoreMatches.get_iter(row)
                liststoreMatches.set_value(iterMatches, 17, isGuess)

        elif newValue == 'Today':
            newValue = datetime.date.today().strftime('%d-%m-%Y')

        iterMatches = liststoreMatches.get_iter(row)
        liststoreMatches.set_value(iterMatches, 1, newValue)
        self.isChanged = True



    def _teamOneChanged(self, widget, row, iterSelected):
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
        seed = self.searchSeed(teamIndex)

        # Update the matches liststore.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatches = liststoreMatches.get_iter(row)
        liststoreMatches.set(iterMatches, 4, teamIndex, 5, teamLabel, 13, seed)
        self.isChanged = True



    def _teamTwoChanged(self, widget, row, iterSelected):
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
        seed = self.searchSeed(teamIndex)

        # Update the matches liststore.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatches = liststoreMatches.get_iter(row)
        liststoreMatches.set(iterMatches, 7, teamIndex, 8, teamLabel, 14, seed)
        self.isChanged = True



    def _dateGuessToggled(self, widget, row):
        ''' Signal handler for the date guess value changing in a cell. '''
        isActive = widget.get_active()
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatches = liststoreMatches.get_iter(row)
        if isActive:
            liststoreMatches.set_value(iterMatches, 17, False)
        else:
            liststoreMatches.set_value(iterMatches, 17, True)

            # Try and guess the date ?
            row = int(row)
            if row > 0:
                theDate = liststoreMatches.get_value(iterMatches, 1)
                if theDate[0:2] == '..':
                    # Date is unknow.  Check the date above.
                    iterAbove = liststoreMatches.get_iter(int(row)-1)
                    dateAbove = liststoreMatches.get_value(iterAbove, 1)
                    if dateAbove[0:2] != '..':
                        # Check if same type of match.
                        matchType = liststoreMatches.get_value(iterMatches, 2)
                        matchTypeAbove = liststoreMatches.get_value(iterAbove, 2)
                        # print('MatchType {} {}'.format(matchType, matchTypeAbove))
                        if matchType != matchTypeAbove:
                            dtCurrent = datetime.date(*time.strptime(dateAbove, "%d-%m-%Y")[:3])
                            dtCurrent = dtCurrent - timedelta(days=2)
                            dateAbove = dtCurrent.strftime('%d-%m-%Y')
                        # Guess the date.
                        liststoreMatches.set_value(iterMatches, 1, dateAbove)

        self.isChanged = True




    def _scoreEdited(self, widget, row, newValue):
        ''' Signal handler for the score value changing in a cell. '''
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatches = liststoreMatches.get_iter(row)
        liststoreMatches.set_value(iterMatches, 6, newValue)
        self.isChanged = True



    def _teamOnePtsEdited(self, widget, row, newValue):
        ''' Signal handler for the team one points value changing in a cell. '''
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatches = liststoreMatches.get_iter(row)
        liststoreMatches.set_value(iterMatches, 11, newValue)
        self.isChanged = True



    def _teamTwoPtsEdited(self, widget, row, newValue):
        ''' Signal handler for the team two points value changing in a cell. '''
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatches = liststoreMatches.get_iter(row)
        liststoreMatches.set_value(iterMatches, 12, newValue)
        self.isChanged = True



    def _seedOneEdited(self, widget, row, newValue):
        ''' Signal handler for the team one seed value changing in a cell. '''
        # Get player one.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatches = liststoreMatches.get_iter(row)
        player1Index = liststoreMatches.get_value(iterMatches, 4)

        self.setPlayerSeed(player1Index, newValue)



    def _seedTwoEdited(self, widget, row, newValue):
        ''' Signal handler for the team two seed value changing in a cell. '''
        # Get player two.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        iterMatches = liststoreMatches.get_iter(row)
        player2Index = liststoreMatches.get_value(iterMatches, 7)

        self.setPlayerSeed(player2Index, newValue)



    def _selectionChanged(self, widget):
        '''
        Signal handler for the selected matches changing.
        This is either the year or the tournment changing.
        Write the existing changes to the database before loading the existing matches for the new year and tournament combination.
        '''
        # Save the current selection if changed
        if self.isChanged:
            dialog = Gtk.Dialog('Edit Matches', self.dialog, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
            label = Gtk.Label('The results has changed. Do you want to save the changes?')
            label.show()
            dialog.get_content_area().add(label)
            response = dialog.run()
            dialog.destroy()
            if response == Gtk.ResponseType.OK:
                self.writeChanges()

        # Display the new selection.
        self.populateMatches()



    def _applyChanges(self, widget):
        ''' Signal handler for the 'Apply' button.  Write any changes to the database. '''
        self.writeChanges()



    def _addRow(self, widget):
        ''' Signal handler for the 'Add Row' button. '''
        # Get the default location.
        comboboxDefaultLocation = self.builder.get_object('comboboxDefaultLocation')
        iterLocations = comboboxDefaultLocation.get_active_iter()
        if iterLocations != None:
            liststoreLocations = self.builder.get_object('liststoreLocations')
            defaultLocationID = liststoreLocations.get_value(iterLocations, 0)
            if defaultLocationID > 0:
                locationName = liststoreLocations.get_value(iterLocations, 1)
            else:
                defaultLocationID = None
                locationName = None
        else:
            defaultLocationID = None
            locationName = None

        # Add a new row.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        newRow = liststoreMatches.append()

        # Using the '<None>' because in this version of GTK+3 the combobox will not scroll forward only backwards so start at the end!
        theYear = self.tournamentSeason.season.theFinish.year
        liststoreMatches.set(newRow, 1, '..-..-' + str(theYear), 5, '<None>', 8, '<None>', 9, 1, 10, self.database.matchResults[1], 11, '', 12, '', 15, defaultLocationID, 16, locationName)

        # Get the number of results.
        nCount = 0
        iterMatches = liststoreMatches.get_iter_first()
        while iterMatches:
            nCount += 1
            iterMatches = liststoreMatches.iter_next(iterMatches)

        # Show this row on the window.
        treeviewMatches = self.builder.get_object('treeviewMatches')
        path = (nCount-1,)
        treeviewMatches.scroll_to_cell(path, None, True, 1, 0)



    def writeChanges(self):
        ''' Write the contents of the dialog to the database. '''
        # Get handlers to the liststores.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        liststoreMatchTypes = self.builder.get_object('liststoreMatchTypes')
        liststoreTeams = self.builder.get_object('liststoreTeams')
        liststoreResults = self.builder.get_object('liststoreResults')

        # Update the tournament.
        cboTournament = self.builder.get_object('cboTournament')
        iterTournament = cboTournament.get_active_iter()
        liststoreTournaments = self.builder.get_object('liststoreTournaments')
        self.tournamentSeason.tournamentIndex = liststoreTournaments.get_value(iterTournament, 0)

        # Update the season.
        cboSeason = self.builder.get_object('cboSeason')
        iterSeason = cboSeason.get_active_iter()
        liststoreSeasons = self.builder.get_object('liststoreSeasons')
        self.tournamentSeason.seasonIndex = liststoreSeasons.get_value(iterSeason, 0)

        # Update the alternative name.
        cboAltName = self.builder.get_object('cboAltName')
        iterAltName = cboAltName.get_active_iter()
        liststoreAltNames = self.builder.get_object('liststoreAltNames')
        self.tournamentSeason.altNameIndex = liststoreAltNames.get_value(iterAltName, 0)
        if self.tournamentSeason.altNameIndex == 0:
            self.tournamentSeason.altNameIndex = None

        # Open the database.
        cnDb = sqlite3.connect(self.database.filename)

        # Loop through the liststore of matches.
        iterMatches = liststoreMatches.get_iter_first()
        while iterMatches:
            matchIndex = liststoreMatches.get_value(iterMatches, 0)

            theDate = liststoreMatches.get_value(iterMatches, 1)
            if theDate == 'None' or theDate[0:1] == '.':
                theDate = 'NULL'
            else:
                dtDate = datetime.date(*time.strptime(theDate, "%d-%m-%Y")[:3])
                # strftime does not work for years < 1900, so don't use it.
                theDate = "'{}-{:0=2}-{:0=2}'".format(dtDate.year, dtDate.month, dtDate.day)

            matchTypeName = liststoreMatches.get_value(iterMatches, 2)
            team1Name = liststoreMatches.get_value(iterMatches, 4)
            if team1Name == None:
                team1Name = 'NULL'
            sScore = liststoreMatches.get_value(iterMatches, 6)
            if sScore == '' or sScore == None:
                sScore = 'NULL'
            else:
                sScore = "'{}'".format(sScore)

            team2Name = liststoreMatches.get_value(iterMatches, 7)
            if team2Name == None or team2Name == 0:
                team2Name = 'NULL'

            sResult = liststoreMatches.get_value(iterMatches, 9)
            if sResult == None:
                sResult = 1

            ptsTeam1 = liststoreMatches.get_value(iterMatches, 11)
            if ptsTeam1 == '' or ptsTeam1 == None:
                ptsTeam1 = 'NULL'

            ptsTeam2 = liststoreMatches.get_value(iterMatches, 12)
            if ptsTeam2 == '' or ptsTeam2 == None:
                ptsTeam2 = 'NULL'

            seed1 = liststoreMatches.get_value(iterMatches, 13)
            if seed1 == '' or seed1 == None or seed1 == 0:
                seed1 = 'NULL'
            seed2 = liststoreMatches.get_value(iterMatches, 14)
            if seed2 == '' or seed2 == None or seed2 == 0:
                seed2 = 'NULL'
            locationIndex = liststoreMatches.get_value(iterMatches, 15)
            if locationIndex == 0:
                locationIndex = None
            isDateGuess = liststoreMatches.get_value(iterMatches, 17)
            dateGuess = 1 if isDateGuess else 0

            if matchIndex == 0:
                sql = "INSERT INTO MATCHES (SPORT_ID, TOURNAMENT_SEASON_ID, THE_DATE, TYPE_ID, TEAM_ONE_ID, TEAM_TWO_ID, SCORE, RESULT_ID, TEAM_ONE_PTS, TEAM_TWO_PTS, SEED1, SEED2, LOCATION_ID, DATE_GUESS) VALUES({}, ?, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, ?, ?)".format(self.database.currentSport.index, theDate, matchTypeName, team1Name, team2Name, sScore, sResult, ptsTeam1, ptsTeam2, seed1, seed2)
                params = (self.tournamentSeason.index, locationIndex, dateGuess)
            else:
                sql = "UPDATE MATCHES SET THE_DATE = {}, TYPE_ID = {}, TEAM_ONE_ID = {}, TEAM_TWO_ID = {}, SCORE = {}, RESULT_ID = {}, TEAM_ONE_PTS = {}, TEAM_TWO_PTS = {}, SEED1 = {}, SEED2 = {}, LOCATION_ID = ?, DATE_GUESS = ? WHERE ID = {};".format(theDate, matchTypeName, team1Name, team2Name, sScore, sResult, ptsTeam1, ptsTeam2, seed1, seed2, matchIndex)
                params = (locationIndex, dateGuess)

            # Execute the command.
            if self.database.debug:
                print(sql)
            cursor = cnDb.execute(sql, params)
            cnDb.commit()

            # Check the year range of objects in this record.
            if theDate != 'NULL':
                theYear = int(theDate[1:5])
                # Check the year range on the 2 teams.
                if team1Name != 'NULL':
                    team = self.database.getTeam(int(team1Name))
                    if team.lastYear < theYear:
                        team.lastYear = theYear
                        team.write()
                    if team.firstYear > theYear:
                        team.firstYear = theYear
                        team.write()
                if team2Name != 'NULL':
                    team = self.database.getTeam(int(team2Name))
                    if team.lastYear < theYear:
                        team.lastYear = theYear
                        team.write()
                    if team.firstYear > theYear:
                        team.firstYear = theYear
                        team.write()

            # Move to next record.
            iterMatches = liststoreMatches.iter_next(iterMatches)

        # Comments.
        textviewNotes = self.builder.get_object('textviewComments')
        oBuffer = textviewNotes.get_buffer()
        oBufferStart = oBuffer.get_iter_at_line_offset(0, 0)
        oBufferEnd = oBuffer.get_end_iter()
        self.tournamentSeason.comments = oBuffer.get_text(oBufferStart, oBufferEnd, False)
        # Flags.
        self.tournamentSeason.flags = 0
        mask = 1
        for index in range(3):
            checkbuttonFlag = self.builder.get_object('checkbuttonFlag{}'.format(index))
            if checkbuttonFlag.get_active():
                self.tournamentSeason.flags += mask
            mask *= 2
        self.tournamentSeason.write()

        # Update the links.
        liststoreLinks = self.builder.get_object('liststoreLinks')
        iterLinks = liststoreLinks.get_iter_first()
        while iterLinks:
            # Check if the row has changed.
            rowChanged = liststoreLinks.get_value(iterLinks, 1)
            if rowChanged != 0:
                # Get information for this row in the liststore.
                linkIndex = liststoreLinks.get_value(iterLinks, 0)
                label = liststoreLinks.get_value(iterLinks, 2)
                url = liststoreLinks.get_value(iterLinks, 3)
                if linkIndex == 0:
                    sql = 'INSERT INTO LINKS (TYPE_ID, KEY_ID, LABEL, URL) VALUES (2, ?, ?, ?);'
                    params = (self.tournamentSeason.index, label, url)
                else:
                    sql = 'UPDATE LINKS SET LABEL = ?, URL = ? WHERE ID = ?;'
                    params = (label, url, linkIndex);
                if self.database.debug:
                    print(sql, params)
                # Execute the command.
                cnDb.execute(sql, params)

            # Move to next record.
            iterLinks = liststoreLinks.iter_next(iterLinks)

        for deleteIndex in self.linksDelete:
            sql = 'DELETE FROM LINKS WHERE ID = ?;'
            params = (deleteIndex, );
            if self.database.debug:
                print(sql, params)
            # Execute the command.
            cnDb.execute(sql, params)

        # Remove the old tournament links.
        sql = 'DELETE FROM LINKS_TOURNAMENTS WHERE SEASON = ? AND TOURNAMENT_ID = ?;'
        params = (self.tournamentSeason.season.theFinish.year, self.tournamentSeason.tournamentIndex)
        cnDb.execute(sql, params)

        # Have to commit now, otherwise the following reads will lock on the database.
        cnDb.commit()

        # Close the database.
        cnDb.close()

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
        cnDb = sqlite3.connect(self.database.filename)

        # Fetch the list of teams.
        isSpecialOption = True
        if self.database.currentSport.lastYearPadding < 0 or year == -1:
            # Special case. All Players.
            sql = 'SELECT ID, Name, FirstYear, LastYear FROM Teams WHERE SportID = {} ORDER BY Name;'.format(self.database.currentSport.index)
            isSpecialOption = False
        elif year == -3:
            # Special case.  Extra players.
            sql = 'SELECT ID, Name, FirstYear, LastYear FROM Teams WHERE SportID = {} AND FirstYear <= {} AND LastYear >= {} ORDER BY Name;'.format(self.database.currentSport.index, self.tournamentSeason.season.theFinish.year + 2 * self.database.currentSport.lastYearPadding, self.tournamentSeason.season.theFinish.year - 3 * self.database.currentSport.lastYearPadding)
        else:
            # Default. Current players.
            sql = 'SELECT ID, Name, FirstYear, LastYear FROM Teams WHERE SportID = {} AND FirstYear <= {} AND LastYear >= {} ORDER BY Name;'.format(self.database.currentSport.index, year, year-self.database.currentSport.lastYearPadding)
        if self.database.debug:
            print(sql)
        cursor = cnDb.execute(sql)
        for row in cursor:
            newRow = liststoreTeams.append()
            teamName = row[1]
            if row[2] == row[3]:
                teamName += ' (' + str(row[2]) + ')'
            else:
                teamName += ' (' + str(row[2]) + '-' + str(row[3]) + ')'
            if self.database.debug:
                print('{} {}'.format(row[0], teamName))
            if row[0] == None:
                print('Error ({}) "{}"'.format(row[0], teamName))
            else:
                liststoreTeams.set(newRow, 0, row[0], 1, teamName)
        cursor.close()

        # Add the special buttons.
        newRow = liststoreTeams.append()
        liststoreTeams.set(newRow, 0, 0, 1, '<None>')
        if isSpecialOption:
            newRow = liststoreTeams.append()
            liststoreTeams.set(newRow, 0, -1, 1, 'All...')
            newRow = liststoreTeams.append()
            liststoreTeams.set(newRow, 0, -3, 1, 'More...')

        newRow = liststoreTeams.append()
        liststoreTeams.set(newRow, 0, -2, 1, 'New...')

        # Close the database.
        cnDb.close()



    def populateMatches(self):
        ''' Populate the dialog with the matches from the year and tournament specified on the dialog. '''
        if self.database == None:
            return

        # print 'Populate Matches Season {} TournamentID {}'.format(theYear,tournamentIndex)

        # Connect to the database.
        cnDb = sqlite3.connect(self.database.filename)

        # If the detail level has changed then update the options in the combo box.
        # Get the new tournament and season from the dialog.
        tournament = self.database.getTournament(self.tournamentSeason.tournamentIndex)

        if tournament.details != self.tournamentDetails:
            # print 'Update match levels'
            matchTypeGroup = self.database.getMatchTypeGroup(tournament.details)
            liststoreMatchTypes = self.builder.get_object('liststoreMatchTypes')
            liststoreMatchTypes.clear()
            for matchTypeIndex in matchTypeGroup.matchTypes:
                matchType = self.database.getMatchType(matchTypeIndex)
                newRow = liststoreMatchTypes.append()
                liststoreMatchTypes.set(newRow, 0, matchTypeIndex, 1, matchType.name)
            self.tournamentDetails = tournament.details

        # Hide the second team for those tournaments that do not require a second team.
        treeviewcolumnTeam2 = self.builder.get_object('treeviewcolumnTeam2')
        if tournament.typeIndex == 2:
            # League Results.
            treeviewcolumnTeam2.set_visible(False)
        else:
            # Cup matches.
            treeviewcolumnTeam2.set_visible(True)

        # Hide the team points for those tournaments that do not show points.
        togglebuttonShowPoints = self.builder.get_object('togglebuttonShowPoints')
        treeviewcolumnPts1 = self.builder.get_object('treeviewcolumnPts1')
        treeviewcolumnPts2 = self.builder.get_object('treeviewcolumnPts2')
        # if self.database.currentSport.ptsDecPlaces>0:
        if False:
            treeviewcolumnPts1.set_visible(True)
            treeviewcolumnPts2.set_visible(True)
            togglebuttonShowPoints.set_active(True)
        else:
            treeviewcolumnPts1.set_visible(False)
            treeviewcolumnPts2.set_visible(False)
            togglebuttonShowPoints.set_active(False)

        # Hide the seeds for those tournaments that do not show seeds.
        # Actually always hide seeds by default.
        togglebuttonShowSeed = self.builder.get_object('togglebuttonShowSeed')
        treeviewcolumnSeed1 = self.builder.get_object('treeviewcolumnSeed1')
        treeviewcolumnSeed2 = self.builder.get_object('treeviewcolumnSeed2')
        # if tournament.seeded_teams:
        if False:
            treeviewcolumnSeed1.set_visible(True)
            treeviewcolumnSeed2.set_visible(True)
            togglebuttonShowSeed.set_active(True)
        else:
            treeviewcolumnSeed1.set_visible(False)
            treeviewcolumnSeed2.set_visible(False)
            togglebuttonShowSeed.set_active(False)

        # If the year has changed then load another group of players.
        #if theYear != self.year:
        self.populateTeamCombos(self.tournamentSeason.season.theFinish.year)
        #    self.year = theYear

        # Build the list of actual matches.
        liststoreMatches = self.builder.get_object('liststoreMatches')
        liststoreMatches.clear()

        # Fetch the list of matches in this tournament.
        cursor = cnDb.execute("SELECT ID, THE_DATE, TYPE_ID, RESULT_ID, TEAM_ONE_ID, TEAM_TWO_ID, SCORE, TEAM_ONE_PTS, TEAM_TWO_PTS, SEED1, SEED2, LOCATION_ID, DATE_GUESS, SEASON_ID FROM MATCHES WHERE TOURNAMENT_SEASON_ID = {} ORDER BY TYPE_ID, THE_DATE DESC, ID;".format(self.tournamentSeason.index))
        # seasonIndex = self.year
        for row in cursor:
            newRow = liststoreMatches.append()
            if row[1] == None:
                sTheDate = '..-..-{}'.format(self.tournamentSeason.season.theFinish.year)
            else:
                sTheDate = '{}-{}-{}'.format(row[1][8:10], row[1][5:7], row[1][0:4])#.strftime('%d-%m-%Y')
            if row[2] == None:
                matchTypeName = 'None'
            else:
                matchType = self.database.getMatchType(row[2])
                matchTypeName = matchType.name
            if row[3] in self.database.matchResults:
                sResult = self.database.matchResults[row[3]]
            else:
                sResult = self.database.matchResults[1]
            if row[4] == None or row[4] == 0:
                team1Name = '<None>'
            else:
                oTeam1 = self.database.getTeam(row[4])
                team1Name = oTeam1.toHtml(False, True)
            if row[5] == None or row[5] == 0:
                team2Name = '<None>'
            else:
                oTeam2 = self.database.getTeam(row[5])
                team2Name = oTeam2.toHtml(False, True, None)
            if row[6] == None:
                sScore = ''
            else:
                sScore = row[6]
            if row[7] == None:
                ptsTeam1 = ''
            else:
                if self.database.currentSport.ptsDecPlaces == 5:
                    ptsTeam1 = '{:.5f}'.format(row[7])
                elif self.database.currentSport.ptsDecPlaces == 4:
                    ptsTeam1 = '{:.4f}'.format(row[7])
                elif self.database.currentSport.ptsDecPlaces == 6:
                    ptsTeam1 = '{:.6f}'.format(row[7])
                else:
                    ptsTeam1 = '{:.3f}'.format(row[7])
            if row[8] == None:
                ptsTeam2 = ''
            else:
                if self.database.currentSport.ptsDecPlaces == 5:
                    ptsTeam2 = '{:.5f}'.format(row[8])
                elif self.database.currentSport.ptsDecPlaces == 4:
                    ptsTeam2 = '{:.4f}'.format(row[8])
                elif self.database.currentSport.ptsDecPlaces == 6:
                    ptsTeam2 = '{:.6f}'.format(row[8])
                else:
                    ptsTeam2 = '{:.3f}'.format(row[8])
            if row[9] == None:
                seed1 = ''
            else:
                seed1 = '{}'.format(row[9])
            if row[10] == None:
                seed2 = ''
            else:
                seed2 = '{}'.format(row[10])
            locationIndex = row[11]
            if locationIndex == None:
                locationName = ''
            else:
                location = self.database.getLocation(locationIndex)
                locationName = location.getName(1)
                self.database.locationCountryIndex = location.countryIndex
            isDateGuess = True if row[12] == 1 else False
            # seasonIndex = row[13] if row[13] != None else seasonIndex

            liststoreMatches.set(newRow, 0, row[0], 1, sTheDate, 2, row[2], 3, matchTypeName, 4, row[4], 5, team1Name, 6, sScore, 7, row[5], 8,team2Name, 9, row[3], 10, sResult, 11, ptsTeam1, 12, ptsTeam2, 13, seed1, 14, seed2, 15, locationIndex, 16, locationName, 17, isDateGuess)
        cursor.close()

        #if seasonIndex != None:
        #    # Always expect to come here really.
        #    adjustmentSeason = self.builder.get_object('adjustmentSeason')
        #    adjustmentSeason.set_value(seasonIndex)

        # Not sure about this??
        # This is here so taht self.database.locationCountryIndex can be set already.
        # This is not correct.  Populate from the actual matches.
        self.database.populateLocationsCombobox(0, tournament.defaultLocationIndex, self.builder.get_object('liststoreLocations'), self.builder.get_object('comboboxDefaultLocation'), self.tournamentSeason.season.theFinish.year)

        # Initialise the tournament seasons (formally comments).
        textviewComments = self.builder.get_object("textviewComments")
        oBuffer = textviewComments.get_buffer()
        oBuffer.set_text(self.tournamentSeason.comments)
        sport_flags = tournament.database.currentSport.flags
        mask = 1
        for index in range(3):
            checkbuttonFlag = self.builder.get_object('checkbuttonFlag{}'.format(index))
            if index < len(sport_flags):
                checkbuttonFlag.set_label(sport_flags[index][1])
                if self.tournamentSeason.flags & mask == mask:
                    checkbuttonFlag.set_active(True)
                else:
                    checkbuttonFlag.set_active(False)
                mask *= 2
            else:
                checkbuttonFlag.set_visible(False)

        # Initialise the links.
        liststoreLinks = self.builder.get_object('liststoreLinks')
        liststoreLinks.clear()
        theYear = self.tournamentSeason.season.theFinish.year
        sql = "SELECT ID, LABEL, URL FROM LINKS_TOURNAMENTS WHERE SEASON = ? AND TOURNAMENT_ID = ? ORDER BY ID;"
        params = (theYear, self.tournamentSeason.tournamentIndex)
        cursor = cnDb.execute(sql, params)
        for row in cursor:
            newRow = liststoreLinks.append(None)
            liststoreLinks.set(newRow, 0, None, 1, 1, 2, row[1], 3, row[2])
        sql = "SELECT ID, LABEL, URL FROM LINKS WHERE TYPE_ID = 2 AND KEY_ID = ? ORDER BY ID;"
        params = (self.tournamentSeason.index, )
        cursor = cnDb.execute(sql, params)
        for row in cursor:
            newRow = liststoreLinks.append(None)
            liststoreLinks.set(newRow, 0, row[0], 1, 0, 2, row[1], 3, row[2])

        # Close the database.
        cnDb.close()

        # The database is up to date with the dialog contents.
        self.isChanged = False



    def editMatches(self, database, sql):
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

# -*- coding: utf-8 -*-

'''
Module to marshall the database connections for the Table program.
This module implements the :py:class:`Database` class.
'''

import sys

# Require the Sqlite3 library
try:
    import sqlite3
except:
    print('pysqlite is not available ({})'.format(__name__));

import datetime
import time

# Application Libraries.
import walton.database
import walton.country
from team import Team
from sport import Sport
from tournament import Tournament
from match_type import MatchType
from match_type_group import MatchTypeGroup
from location import Location
from season import Season
from tournament_season import TournamentSeason
#import dialogEditMatches
#import dialogEditSport
#import dialogEditTeam
#import dialogEditCountry



class Database(walton.database.IDatabase):
    '''
    :ivar string filename: The filename of the database file. (INHERITED)
    :ivar Sport currentSport: The current active :py:class:`Sport` object.
    :ivar Dictionary teams: Dictionary of :py:class:`Team` objects.   This is the cache for the :py:func:`getTeam` function.
    :ivar Dictionary tournaments: Dictionary of :py:class:`Tournament` objects. This is the cache for the :py:func:`getTournament` function.
    :ivar Dictionary matchResults: Dictionary of match results types (The mean if result_index).
    :ivar Dictionary seasons: Dictionary of :py:class:`~season.Season` objects.  This is the cache for the :py:func:`getSeason` function.
    :ivar bool debug: True for additional debugging outputs.

    Class to represent the database for the sports results database.
    Originally this class handled the rendering as well.
    This class is inherited from :py:class:`~walton.database.IDatabase` and :py:class:`~walton.country.IFlagsDatabase`.
    '''



    def __init__(self, databaseFilename):
        '''
        :param string DatabaseFilename: Specify the filename of the sports database.
        :param string FlagDbFilename: Specify the filename of the countries database.
        :param string FlagsDirectory: Specify the directory that contains the flag images.

        Class constructor for the :py:class:`Database` object.
        '''
        # Call the constructor for the inherited classes.
        walton.database.IDatabase.__init__(self, databaseFilename)

        # The current active Sport object.
        self.currentSport = None

        # Dictionary of Team objects.  This is the cache for the GetTeam() function.
        self.teams = {}

        # Dictionary of Tournament objects. This is the cache for the GetTournament() function.
        self.tournaments = {}

        # Dictionary of MatchType objects.
        self._matchTypes = {}

        # Dictionary of Location objects.
        self.locations = {}

        # Dictionary of match results types (The mean if result_index).
        self.matchResults = {1:'Team 1', 2:'Team 2', 3:'Draw', 4:'Tie', 5:'Not Played'}

        # Dictionary of Season objects.
        self.seasons = {}
        self.tournamentSeason = {}
        self.altNames = {}

        # True for additional debugging information.
        self.debug = False

        self.locationCountryIndex = None



    def setCurrentSport(self, newSportIndex):
        '''
        :param int newSportIndex: Specify the ID of the sport to switch to.

        Change the current active sport.
        '''
        self.currentSport = Sport(self)
        self.currentSport.read(newSportIndex)

        # The seasons depend in the current sport so must be reset when is is changed.
        self.seasons = {}

        # The other caches now hold lots of useless data now but still work if the sport changes back.



    def getTeam(self, teamIndex):
        '''
        :param int teamIndex: Specify the ID of the team required.
        :returns: The requested :py:class:`~team.Team` object from the database or cache.

        Returns the specified team from the database.
        In actual fact the the team is probably fetched from the cache.
        '''
        if teamIndex == None:
            return None

        # Only use int types as the key.
        if type(teamIndex) != type(int):
            teamIndex = int(teamIndex)

        # Check if the team is already in the dictionary.
        if teamIndex in self.teams:
            return self.teams[teamIndex]

        # Read from the database.
        team = Team(self)
        team.read(teamIndex)

        # Store this team in the dictionary.
        self.teams[teamIndex] = team

        # Return the team.
        return team



    def getTournament(self, tournamentIndex):
        '''
        :param int tournamentIndex: Specify the ID of the tournament required.
        :returns: The requested :py:class:`~tournament.Tournament` object.

        Returns the specified tournament from the database.
        In actual fact the tournament is probably fetched from the cache.
        '''
        # Only use int types as the key.
        if type(tournamentIndex) != type(int):
            tournamentIndex = int(tournamentIndex)

        # Check if the tournament is already in the dictionary.
        if tournamentIndex in self.tournaments:
            return self.tournaments[tournamentIndex]

        # Read from database.
        tournament = Tournament(self)
        tournament.read(tournamentIndex)

        # Store this tournament in the dictionary.
        self.tournaments[tournamentIndex] = tournament

        # Return the tournament.
        return tournament



    def getLocation(self, locationIndex):
        '''
        :param int locationIndex: Specifies the ID of the location requested.
        :returns: The specified :py:class:`Location` object from the database.
        '''
        # Only use int types as the key.
        if type(locationIndex) != type(int):
            locationIndex = int(locationIndex)

        # Check if the location is already in the dictionary.
        if locationIndex in self.locations:
            return self.locations[locationIndex]

        # Read from database.
        location = Location(self)
        location.read(locationIndex)

        # Store this location in the dictionary.
        self.locations[locationIndex] = location

        # Return the location.
        return location



    def getMatchType(self, matchTypeID):
        '''
        :param int matchTypeID: Specify the ID of the required MatchType object.
        :returns: The requested :py:class:`~matchtype.MatchType` object.

        Returns the match type from the database.
        '''
        # Only use int types as the key..
        if type(matchTypeID) != type(int):
            matchTypeID = int(matchTypeID)

        # Check if the match type is already in the dictionary.
        if matchTypeID in self._matchTypes:
            return self._matchTypes[matchTypeID]

        matchType = MatchType(self)
        matchType.read(matchTypeID)

        # Store this match type in the dictionary.
        self._matchTypes[matchTypeID] = matchType

        # Return the match type.
        return matchType



    def getMatchTypeGroup(self, matchTypeGroupIndex):
        '''
        :param int matchTypeGroupIndex: Specify the ID of required match type group.
        :returns: The requested :py:class:`~matchtypegroup.MatchTypeGroup` object.

        Return the match type group.
        The data for this should be moved into the database in future.
        '''
        matchTypeGroup = MatchTypeGroup()
        matchTypeGroup.ID = matchTypeGroupIndex
        if matchTypeGroupIndex == 1:
            matchTypeGroup.name = 'All Cup Levels'
            matchTypeGroup.matchTypes = [1, 9, 10, 20, 30, 40, 67, 68, 69, 70, 73, 74, 75, 76, 77, 78, 79, 80, 90]
        elif matchTypeGroupIndex == 2:
            matchTypeGroup.name = 'All League Levels'
            matchTypeGroup.matchTypes = [2, 11, 21, 22, 31, 32, 33, 34, 41, 42, 43, 44, 45, 46, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58]
        elif matchTypeGroupIndex == 100:
            matchTypeGroup.name = 'Matches and Results'
            matchTypeGroup.matchTypes = [2, 11, 21, 22, 80]

        elif matchTypeGroupIndex == 3:
            matchTypeGroup.name = 'Final'
            matchTypeGroup.matchTypes = [1]
        elif matchTypeGroupIndex == 4:
            matchTypeGroup.name = 'Semi Finals'
            matchTypeGroup.matchTypes = [1, 10]
        elif matchTypeGroupIndex == 5:
            matchTypeGroup.name = 'Quarter Finals'
            matchTypeGroup.matchTypes = [1, 10, 20]
        elif matchTypeGroupIndex == 6:
            matchTypeGroup.name = 'Last 16'
            matchTypeGroup.matchTypes = [1, 10, 20, 30]
        elif matchTypeGroupIndex == 7:
            matchTypeGroup.name = 'Last 32'
            matchTypeGroup.matchTypes = [1, 10, 20, 30, 40]

        elif matchTypeGroupIndex == 51:
            matchTypeGroup.name = 'Winner'
            matchTypeGroup.matchTypes = [2]
        elif matchTypeGroupIndex == 52:
            matchTypeGroup.name = 'Top 2'
            matchTypeGroup.matchTypes = [2, 11]
        elif matchTypeGroupIndex == 53:
            matchTypeGroup.name = 'Top 3'
            matchTypeGroup.matchTypes = [2, 11, 21]
        elif matchTypeGroupIndex == 54:
            matchTypeGroup.name = 'Top 4'
            matchTypeGroup.matchTypes = [2, 11, 21, 22]
        else:
            pass

        return matchTypeGroup



    def getSeason(self, seasonIndex):
        '''
        :param int seasonIndex: Specified the ID of the requested season.
        :returns: The requested :py:class:`~season.Season` object.

        Returns the specified season from the database.
        '''
        # Only use int types as the key.
        if type(seasonIndex) != type(int):
            seasonIndex = int(seasonIndex)

        # Check if the season is already in the dictionary.
        if seasonIndex in self.seasons:
            return self.seasons[seasonIndex]

        # Read from database.
        season = Season(self, self.currentSport.index, seasonIndex)
        season.read(seasonIndex)

        # Store this season in the dictionary.
        self.seasons[seasonIndex] = season

        # Return the season.
        return season



    def getTournamentSeason(self, tournamentSeasonIndex):
        ''' Returns the :py:class:`TournamentSeason` object for the specified season. '''
        # Only use int types as the key.
        if type(tournamentSeasonIndex) != type(int):
            tournamentSeasonIndex = int(tournamentSeasonIndex)

        # Check if the season is already in the dictionary.
        if tournamentSeasonIndex in self.tournamentSeason:
            return self.tournamentSeason[tournamentSeasonIndex]

        # Read from database.
        tournamentSeason = TournamentSeason(self, None, None, None, None, None, None)
        tournamentSeason.read(tournamentSeasonIndex)

        # Store this season in the dictionary.
        self.tournamentSeason[tournamentSeasonIndex] = tournamentSeason

        # Return the season.
        return tournamentSeason



    def getAltName(self, altNameIndex):
        ''' Returns the alternative name for the tournament. '''
        # Only use int types as the key.
        if type(altNameIndex) != type(int):
            altNameIndex = int(altNameIndex)

        # Check if the season is already in the dictionary.
        if altNameIndex in self.altNames:
            return self.altNames[altNameIndex]

        # Read from database.
        cndb = sqlite3.connect(self.filename)
        sql = "SELECT NAME FROM TOURNAMENT_ALT_NAMES WHERE ID = ?;"
        params = (altNameIndex, )
        cursor = cndb.execute(sql, params)
        row = cursor.fetchone()
        cursor.close()
        if row == None:
            # Error, don't really expect this.
            altName = 'Error({})'.format(altNameIndex)
        else:
            altName = row[0]

        # Store this season in the dictionary.
        self.altNames[altNameIndex] = altName

        # Return the season.
        return altName



    def getMatchResultTypeLabel(self, matchResultTypeIndex):
        '''
        :param int matchResultTypeIndex: Specify the ID of the match result type.
        :returns: The label for the specified match result type.

        The label for the match result types.
        '''
        if matchResultTypeIndex == 1:
            return 'Team A always wins'
        elif matchResultTypeIndex == 2:
            return 'Draws Possible'
        elif matchResultTypeIndex == 3:
            return 'Ties Possible'
        return 'Error ({})'.format(matchResultTypeIndex)



    def getSportDetailLabel(self, detailIndex):
        '''
        :param int detailIndex: Specify the ID of the detail level.
        :returns: The label of the specified detail level ID.

        Get a label to represent the specified detail level
        This data for this should be moved into the database in due course.
        '''
        if detailIndex == 1:
            return 'Winner only'
        elif detailIndex == 2:
            return 'Finalists and winners'
        elif detailIndex == 3:
            return 'Semi Finalists, etc...'
        elif detailIndex == 4:
            return 'Quarter Finalists, etc...'
        elif detailIndex == 5:
            return 'Last 16, etc...'
        elif detailIndex == 6:
            return 'Last 32, etc...'
        return 'Detail({})'.format(detailIndex)



    def populateLocationsCombobox(self, mode, locationIndex, listStore, comboBox, theYear):
        '''
        :param int mode: 0 Just the actual entry.  -2 Locations in country.  -3 More locations.  -4 All locations.  -5 All locations in country.  -6 Location in year range.
        :param int locationIndex: Specifies the ID of the current location.
        :param Gtk.Listore listStore: Specifies the liststore control for the combobox.
        :param Gtk.ComboBox comboBox: Specifies the combobox control.
        :param int theYear: Specifies the year that the this match.

        Populate the locations combobox.
        Might put this in shared location to use on other dialogs.
        '''
        # Number of years to look backwards in the year span.
        YEAR_SPAN = 6

        # Open the database.
        cndb = sqlite3.connect(self.filename)

        # Every mode has None available.
        listStore.clear()
        newRow = listStore.append((0, 'None', None))
        newRow = listStore.append((-1, 'Add New Location...', None))
        if mode != -2:
            if locationIndex != None:
                location = self.getLocation(locationIndex)
                country = self.getCountry(location.countryIndex)
                newRow = listStore.append((-2, 'Locations in {}'.format(country.name), None))
                self.locationCountryIndex = country.index
            elif self.locationCountryIndex != None:
                country = self.getCountry(self.locationCountryIndex)
                newRow = listStore.append((-2, 'Locations in {}'.format(country.name), None))

        if mode != -3:
            newRow = listStore.append((-3, 'More Locations', None))
        if mode != -4:
            newRow = listStore.append((-4, 'All Locations', None))
        if mode != -5:
            if locationIndex != None:
                location = self.getLocation(locationIndex)
                country = self.getCountry(location.countryIndex)
                newRow = listStore.append((-5, 'All Locations in {}'.format(country.name), None))
                self.locationCountryIndex = country.index
            elif self.locationCountryIndex != None:
                country = self.getCountry(self.locationCountryIndex)
                newRow = listStore.append((-5, 'All Locations in {}'.format(country.name), None))
        if mode != -6:
            if theYear != None:
                newRow = listStore.append((-6, 'All Locations in {}-{}'.format(theYear - YEAR_SPAN , (theYear + 1) % 100), None))

        if mode == 0:
            # Just the selected location.
            # print('populateLocationsCombobox() mode: Location = {}'.format(locationIndex))
            sql = 'SELECT ID, NAME FROM LOCATIONS WHERE ID = ?;'
            params = (locationIndex, )
        elif mode == -3:
            # Locations in this sport.
            # print('populateLocationsCombobox() mode: Sport = {}'.format(self.currentSport.index))
            # TODO: Change the sql to be locations in this sport.
            sql = 'SELECT LOCATIONS.ID, LOCATIONS.NAME FROM LOCATIONS INNER JOIN MATCHES ON LOCATIONS.ID = MATCHES.LOCATION_ID WHERE MATCHES.SPORT_ID = ? GROUP BY LOCATIONS.ID ORDER BY LOCATIONS.NAME;'
            params = (self.currentSport.index, )
        elif mode == -2:
            # Locations in this sport with the same location.
            # print('populateLocationsCombobox() mode: Sport = {}, Country = {}'.format(self.currentSport.index, self.locationCountryIndex))
            sql = 'SELECT LOCATIONS.ID, LOCATIONS.NAME FROM LOCATIONS INNER JOIN MATCHES ON LOCATIONS.ID = MATCHES.LOCATION_ID WHERE MATCHES.SPORT_ID = ? AND LOCATIONS.COUNTRY_ID = ? GROUP BY LOCATIONS.ID ORDER BY LOCATIONS.NAME;'
            countryIndex = 1
            params = (self.currentSport.index, self.locationCountryIndex)
        elif mode == -5:
            # All locations with the same country location.
            # print('populateLocationsCombobox() mode: Country = {}'.format(self.locationCountryIndex))
            sql = 'SELECT ID, NAME FROM LOCATIONS WHERE LOCATIONS.COUNTRY_ID = ? ORDER BY NAME;'
            params = (self.locationCountryIndex, )
        elif mode == -6:
            # All locations with matches in this year (add +-1?).
            # print('populateLocationsCombobox() mode: Sport = {}, Year = {}'.format(self.currentSport.index, theYear))
            sql = "SELECT LOCATIONS.ID, LOCATIONS.NAME FROM LOCATIONS INNER JOIN MATCHES ON LOCATIONS.ID = MATCHES.LOCATION_ID WHERE MATCHES.SPORT_ID = ? AND MATCHES.THE_DATE >= '{}-01-01' AND MATCHES.THE_DATE <= '{}-12-31' GROUP BY LOCATIONS.ID ORDER BY LOCATIONS.NAME;".format(theYear - YEAR_SPAN , theYear + 1)
            countryIndex = 1
            params = (self.currentSport.index, )
        else:
            # All locations.
            # print('populateLocationsCombobox() mode: All Locations')
            sql = 'SELECT ID, NAME FROM LOCATIONS ORDER BY NAME;'
            params = None
        if params == None:
            cursor = cndb.execute(sql)
        else:
            cursor = cndb.execute(sql, params)
        rowSelected = 0 # The None row.
        for row in cursor:
            location = self.getLocation(row[0])
            # newRow = listStore.append((row[0], row[1], None))
            newRow = listStore.append((row[0], location.getName(1), None))
            if row[0] == locationIndex:
                rowSelected = len(listStore)-1
        cursor.close()

        # Select the active selection.
        if comboBox != None:
            comboBox.set_active(rowSelected)

        # Close the database.
        cndb.close()

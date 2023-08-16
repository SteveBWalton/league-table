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
from team import Team
from season import Season



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



    def __init__(self, databaseFilename, application):
        '''
        :param string DatabaseFilename: Specify the filename of the sports database.
        :param string FlagDbFilename: Specify the filename of the countries database.
        :param string FlagsDirectory: Specify the directory that contains the flag images.

        Class constructor for the :py:class:`Database` object.
        '''
        # Call the constructor for the inherited classes.
        walton.database.IDatabase.__init__(self, databaseFilename)

        self.application = application

        # Dictionary of Team objects.  This is the cache for the GetTeam() function.
        self.teams = {}

        # Dictionary of Season objects.
        self.seasons = {}




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
        season = Season(self)
        season.read(seasonIndex)

        # Store this season in the dictionary.
        self.seasons[seasonIndex] = season

        # Return the season.
        return season



    def restore(self):
        ''' Remove the what if results. '''
        # Connect to the database.
        cndb = sqlite3.connect(self.filename)

        sql = "UPDATE MATCHES SET HOME_TEAM_FOR = REAL_HOME_TEAM_FOR, AWAY_TEAM_FOR = REAL_AWAY_TEAM_FOR WHERE REAL_HOME_TEAM_FOR IS NOT NULL AND REAL_AWAY_TEAM_FOR IS NOT NULL AND (HOME_TEAM_FOR != REAL_HOME_TEAM_FOR OR AWAY_TEAM_FOR != REAL_AWAY_TEAM_FOR);"
        cndb.execute(sql)
        cndb.commit()

        # Close the database.
        cndb.close()


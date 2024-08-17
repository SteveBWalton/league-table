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



    def getListTeams(self, startDate, finishDate):
        '''
        Return an array of teams which played matches between the specified dates.
        This only works once all the teams have played a home match.
        '''
        cndb = sqlite3.connect(self.filename)

        sql = f"SELECT HOME_TEAM_ID FROM MATCHES WHERE THE_DATE >= '{startDate}' AND THE_DATE <= '{finishDate}' GROUP BY HOME_TEAM_ID;"
        cursor = cndb.execute(sql)
        listTeams = []
        for row in cursor:
            listTeams.append(row[0])

        return listTeams



    def getArrayTeamPts(self, teamIndex, startDate, finishDate):
        ''' Return an array of the points scored by the specified team between the specified dates. '''
        # Connect to the database.
        cndb = sqlite3.connect(self.filename)

        sql = f"SELECT HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, HOME_BONUS_PTS, AWAY_BONUS_PTS FROM MATCHES WHERE (HOME_TEAM_ID = {teamIndex} OR AWAY_TEAM_ID = {teamIndex}) AND (THE_DATE >= '{startDate}' AND THE_DATE <= '{finishDate}') ORDER BY THE_DATE;"
        cursor = cndb.execute(sql)
        listPts = []
        totalPts = 0.0
        for row in cursor:
            if row[2] == row[3]:
                # Draw.  Doesn't matter home or away or goal difference.
                pts = 1
            else:
                if row[0] == teamIndex:
                    # Home match.
                    if row[2] > row[3]:
                        pts = 3.0
                    else:
                        pts = 0.0
                    pts += (row[2] - row[3]) / 1000
                else:
                    # Away match.
                    if row[2] > row[3]:
                        pts = 0.0
                    else:
                        pts = 3.0
                    pts += (row[3] - row[2]) / 1000
            if row[0] == teamIndex:
                # Home match.
                if row[4] != 0:
                    # Bonus points.
                    pts += row[4]
            else:
                # Away match.
                if row[5] != 0:
                    # Bonus points.
                    pts += row[5]
            totalPts += pts
            listPts.append(totalPts)

        # Close the database.
        cndb.close()

        return listPts

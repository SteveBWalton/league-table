# -*- coding: utf-8 -*-

'''
Module to support seasons in the table program.
Each team is a row from the SEASONS table in the table database.
'''

# Require the Sqlite3 library
try:
    import sqlite3
except:
    print("pysqlite is not available");
    print("Try package python-sqlite2");
    sys.exit(1)

import datetime
import time

# import modDatabase



class Season:
    '''
    Class to represent a season in the table database.
    Each season is a row from the SEASONS table in the table database.

    :ivar Database database: The database that contains this season.
    :ivar int index: The ID of this season.
    :ivar string name: The name or label for this season.
    :ivar datetime.date startDate: The start date for this season.
    :ivar datetime.date finishDate: The finish date for this season.
    :ivar string comments: Optional additional text description of the team.
    '''



    def __init__(self, database):
        '''
        Class constructor for the :py:class:`Season` class.

        :param Database Database: Specifies the :py:class:`~database.Database` database that contains the team.
        '''
        # The database that contains this team.
        self.database = database
        # The ID of this team.
        self.index = -1
        # The name or label for this team.
        self.name = 'Undefined'
        # Optional additional text description of the team.
        self.comments = None
        # The start date of the season.
        self.startDate = None
        # The finish date of the season.
        self.finishDate = None
        # The index of the next season.
        self._nextSeasonIndex = None
        # The index of the previous season.
        self._previousSeasonIndex = None
        # Number of matches this season.
        self.numMatches = None
        # A good finish position.
        self.goodPos = None
        # A bad finish position.
        self.badPos = None
        # A not quite as good finish position.
        self.goodPos2 = None



    def toHtml(self):
        '''
        Returns the team name in html format.
        '''
        # Add a link.
        html = '<a href="app:home?season={}">'.format(self.index)

        # Add the actual name
        html += self.name

        html += '</a>'

        # Return the construction
        return html



    def getLinks(self):
        ''' Returns a dictionary of links for this team. '''
        # Default to an empty dictionary.
        links = {}

        # Open the database.
        cndb = sqlite3.connect(self.database.filename)

        # Fetch the links.
        sql = 'SELECT LABEL, URL FROM LINKS WHERE TYPE_ID = 2 AND KEY_ID = ?;'
        params = (self.index, )
        cursor = cndb.execute(sql, params)
        for row in cursor:
            links[row[0]] = row[1]
        cursor.close()

        # Close the database.
        cndb.close()

        # Return the links found.
        return links



    def read(self, seasonIndex):
        '''
        Read this season from the database.

        :param int seasonIndex: Specifies the index of the season to read.
        '''
        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        # sql = 'SELECT Name, CountryID, DoB, DoD, FirstYear, LastYear, Comments, InternetURL FROM Teams WHERE ID = ?;'
        sql = 'SELECT LABEL, START_DATE, FINISH_DATE, COMMENTS, NUM_MATCHES, GOOD_POS, BAD_POS, POSITIVE_POS FROM SEASONS WHERE ID = ?;'
        params = (seasonIndex, )
        cursor = cndb.execute(sql, params)
        row = cursor.fetchone()
        cursor.close()
        if row == None:
            print('Error ')
            print(sql)
            print(params)
            return None

        self.index = seasonIndex
        self.name = row[0]
        self.startDate = datetime.date(*time.strptime(row[1], "%Y-%m-%d")[:3]) if row[1] is not None else None
        self.finishDate = datetime.date(*time.strptime(row[2], "%Y-%m-%d")[:3]) if row[2] is not None else None
        self.comments = row[3]
        self.numMatches = 0 if row[4] is None else int(row[4])
        self.goodPos = 0 if row[5] is None else int(row[5])
        self.badPos = 0 if row[6] is None else int(row[6])
        self.positivePos = 0 if row[7] is None else int(row[7])

        # For debugging.
        if self.index == 1:
            self._previousSeasonIndex = 2
            self._nextSeasonIndex = 4
        elif self.index == 2:
            self._nextSeasonIndex = 1
            self._previousSeasonIndex = 3
        elif self.index == 3:
            self._nextSeasonIndex = 2
            self._previousSeasonIndex = 5
        elif self.index == 4:
            self._previousSeasonIndex = 1
            self._nextSeasonIndex = None
        elif self.index == 5:
            self._previousSeasonIndex = None
            self._nextSeasonIndex = 3

        # Close the database.
        cndb.close()



    def write(self):
        ''' Write this season into the database. '''
        if self.database.application.debug:
            print('Season::write()')
        if self.index == -1:
            # Write a new record.
            sql = 'INSERT INTO SEASONS (Name, SportID, CountryID, FirstYear, LastYear, DoB, DoD, Comments, InternetURL) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);'
            params = (self.database.param(self.name, ''), self.database.currentSport.index, self.database.param(self.countryIndex, -1), self.firstYear, self.lastYear, self.dob, self.dod, self.database.param(self.comments, ''), self.database.param(self.internetUrl, ''))
        else:
            # Update an existing record.
            sql = 'UPDATE SEASONS SET LABEL = ?, COMMENTS = ?, START_DATE = ?, FINISH_DATE = ?, WIN_PTS = ?, DRAW_PTS = ?, NUM_MATCHES = ?, GOOD_POS = ?, BAD_POS = ?, POSITIVE_POS = ? WHERE ID = ?;'
            params = (self.database.param(self.name, ''), self.database.param(self.comments, ''), self.startDate, self.finishDate, self.winPts, self.drawPts, self.numMatches, self.goodPos, self.badPos, self.positivePos, self.index)

        if self.database.application.debug:
            print(sql)
            print(params)

        # Open the database.
        cndb = sqlite3.connect(self.database.filename)

        # Execute the command.
        cursor = cndb.execute(sql, params)
        cndb.commit()

        # Load the index if it not known.
        if self.index == -1:
            sql = "SELECT MAX(ID) FROM SEASONS;"
            cursor = cndb.execute(sql)
            row = cursor.fetchone()
            cursor.close()
            self.index = row[0]

        # Close the database.
        cndb.close()

        # Return success.
        return True



    def getNextSeasonIndex(self):
        ''' Returns the index of the next season or none. '''
        if self._nextSeasonIndex is not None:
            return self._nextSeasonIndex
        return None



    def getPreviousSeasonIndex(self):
        '''  Returns the index of the previous season or none. '''
        if self._previousSeasonIndex is not None:
            return self._previousSeasonIndex
        return None

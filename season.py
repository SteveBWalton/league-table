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



    def toHtml(self, addLink=True, showYears=False, ageDate = None, headLinkID = None):
        '''
        Returns the team name in html format.

        :param bool addLink: Specify true to wrap the team name in link.
        :param bool showYears: Specify true to add the active teams for the team after the team name.
        :param date ageDate: Optionally specify the date to display the teams age on.
        :param int headLinkID: Optionally specify the ID of a team to link to the head to head results from.
        '''
        # Add a link ( if requested )
        if addLink:
            if headLinkID == None:
                html = '<a href="app:show_team?id={}">'.format(self.index)
            else:
                html = '<a href="app:head_head?team1={}&team2={}">'.format(headLinkID, self.index)
            html += '<span class="team">'
        else:
            html = ''

        # Add the actual name
        html += self.name

        if addLink:
            html += '</span>'
            # Temporary fix for the antialaising length problem
            # html += '&nbsp;'
            html += '</a>'

        if ageDate != None:
            # html += ' ({} {} {})'.format(ageDate,self.dob,self.Age(ageDate))
            nAge = self.getAge(ageDate)
            if nAge > 0:
                html += '&nbsp;<span class="age" style="vertical-align: middle;">({})</span>'.format(nAge)

        if showYears:
            html += self.getSpan(addLink)

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
        sql = 'SELECT LABEL FROM SEASONS WHERE ID = ?;'
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

        # Close the database.
        cndb.close()



    def write(self):
        ''' Write this season into the database. '''
        if self.index == -1:
            # Write a new record.
            sql = 'INSERT INTO SEASONS (Name, SportID, CountryID, FirstYear, LastYear, DoB, DoD, Comments, InternetURL) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);'
            params = (self.database.param(self.name, ''), self.database.currentSport.index, self.database.param(self.countryIndex, -1), self.firstYear, self.lastYear, self.dob, self.dod, self.database.param(self.comments, ''), self.database.param(self.internetUrl, ''))
        else:
            # Update an existing record.
            sql = 'UPDATE SEASONS SET LABEL = ?, COMMENTS = ? WHERE ID = ?;'
            params = (self.database.param(self.name, ''), self.database.param(self.comments, ''), self.index)

        if self.database.debug:
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

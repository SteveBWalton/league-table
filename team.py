# -*- coding: utf-8 -*-

'''
Module to support teams in the table program.
Each team is a row from the TEAMS table in the table database.
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



class Team:
    '''
    Class to represent a team in the Sports Results database.
    Each team is a row from the TEAMS table in the sports database.
    In the program a team can be labelled as a player instead of a team.

    :ivar Database database: The database that contains this team.
    :ivar int index: The ID of this team.
    :ivar string name: The name or label for this team.
    :ivar int countryIndex: The ID of the country for this team.  Can be None.
    :ivar datetime.date dob: The date of birth for this team.  Makes more sense for a player.  Can be None.
    :ivar datetime.date dob: The date of death for this team.  Makes more sense for a player.  Can be None.
    :ivar int firstYear: The first season with results for this team.
    :ivar int lastYear: The last season with results for this team.
    :ivar string comments: Optional additional text description of the team.
    '''



    def __init__(self, database):
        '''
        Class constructor for the :py:class:`Team` class.

        :param Database Database: Specifies the :py:class:`~database.Database` database that contains the team.
        '''
        # The database that contains this team.
        self.database = database
        # The ID of this team.
        self.index = -1
        # The name or label for this team.
        self.name = 'Undefined'
        # The first season with results for this team.
        self.firstYear = -1
        # The last season with results for this team.
        self.lastYear = -1
        # Optional additional text description of the team.
        self.comments = None
        # Optional url for a link for more information about this team.
        self.internetUrl = None



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



    def getSpan(self, isHtmlFormat = True):
        '''
        Return the span of this team as a string.

        :param bool isHtmlFormat: Optionally specifiy false to return the span in ascii, otherwise html format is used.
        :returns: A human readable string that describes the range of active seasons for this team.
        '''
        if self.firstYear > 0 or self.lastYear > 0:
            if isHtmlFormat:
                html = '&nbsp;<span class="years">('
            else:
                html = ' ('
            if self.firstYear > 0:
                html += str(self.firstYear)
            if self.lastYear > 0 and self.lastYear != self.firstYear:
                html += '-' + str(self.lastYear)
            html += ')'
            if isHtmlFormat:
                html += '</span>'
        else:
            html = ''
        return html



    def getLinks(self):
        ''' Returns a dictionary of links for this team. '''
        # Default to an empty dictionary.
        oLinks = {}

        # Open the database.
        cnDb = sqlite3.connect(self.database.filename)

        # Fetch the links.
        sql = 'SELECT LABEL, URL FROM LINKS WHERE TYPE_ID = 1 AND KEY_ID = ?;'
        params = (self.index, )
        cursor = cnDb.execute(sql, params)
        for row in cursor:
            oLinks[row[0]] = row[1]
        cursor.close()

        # Close the database.
        cnDb.close()

        # Return the links found.
        return oLinks



    def read(self, teamIndex):
        '''
        Read this team from the database.

        :param int teamIndex: Specifies the index of the team to read.
        '''
        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        # sql = 'SELECT Name, CountryID, DoB, DoD, FirstYear, LastYear, Comments, InternetURL FROM Teams WHERE ID = ?;'
        sql = 'SELECT LABEL FROM TEAMS WHERE ID = ?;'
        params = (teamIndex, )
        cursor = cndb.execute(sql, params)
        row = cursor.fetchone()
        cursor.close()
        if row == None:
            print('Error ')
            print(sql)
            print(params)
            return None

        self.index = teamIndex
        self.name = row[0]
        #self.countryIndex = row[1]
        #if row[2] == None:
        #    self.dob = None
        #else:
        #    #oTeam.dob = datetime.strptime(row[2],'%Y-%m-%d')
        #    self.dob = datetime.date(*time.strptime(row[2], "%Y-%m-%d")[:3])
        #if row[3] == None:
        #    self.dod = None
        #else:
        #    self.dod = datetime.date(*time.strptime(row[3], "%Y-%m-%d")[:3])
        #self.firstYear = row[4]
        #self.lastYear = row[5]
        #self.comments = row[6]
        #self.internetUrl = row[7]

        # Close the database.
        cndb.close()



    def write(self):
        ''' Write this team into the database. '''
        if self.index == -1:
            # Write a new record.
            sql = 'INSERT INTO Teams(Name, SportID, CountryID, FirstYear, LastYear, DoB, DoD, Comments, InternetURL) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);'
            params = (self.database.param(self.name, ''), self.database.currentSport.index, self.database.param(self.countryIndex, -1), self.firstYear, self.lastYear, self.dob, self.dod, self.database.param(self.comments, ''), self.database.param(self.internetUrl, ''))
        else:
            # Update an existing record.
            sql = 'UPDATE Teams SET Name = ?, CountryID = ?, FirstYear = ?, LastYear = ?, DoB = ?, DoD = ?, Comments = ?, InternetURL = ? WHERE ID = ?;'
            params = (self.database.param(self.name, ''), self.database.param(self.countryIndex, -1), self.firstYear, self.lastYear, self.dob, self.dod, self.database.param(self.comments, ''), self.database.param(self.internetUrl, ''), self.index)

        if self.database.debug:
            print(sql)
            print(params)

        # Open the database.
        cnDb = sqlite3.connect(self.database.filename)

        # Execute the command.
        cursor = cnDb.execute(sql, params)
        cnDb.commit()

        # Load the index if it not known.
        if self.index == -1:
            sql = "SELECT MAX(ID) FROM Teams;"
            cursor = cnDb.execute(sql)
            row = cursor.fetchone()
            cursor.close()
            self.index = row[0]

        # Close the database.
        cnDb.close()

        # Return success.
        return True

# -*- coding: utf-8 -*-

'''
Module to handle the output for the table program.
These functions were originally in the database module.
'''

# System Libraries.
import sys
import sqlite3
import datetime
import time
import math

# Import my own libraries.
import walton.html
import walton.toolbar
# from match_type import MatchType



class Render(walton.toolbar.IToolbar):
    '''
    :ivar Database database: The :py:class:`~database.Database` object to build pages from.
    :ivar Html html: A :py:class:`~walton.html.Html` object to prepare the output for the browser.
    :ivar string editTarget: The url to edit the current page or None if no edit available.
    :ivar string next: The url to move to the next page or None for no next page.
    :ivar string previous: The url to the previous page or None for no previous page.
    :ivar bool showAge: True to enable the show ages button, false to disable it.
    :ivar bool tournamentSelect: True to enable the tournament selection combobox, false to disable it.
    :ivar bool yearsSelect: True to enable the year selection button, false to disable it.
    :ivar bool countrySelect: True to enable the country selection button, false to disable it.
    :ivar array levels: The page options or levels. Use [] to specify upto 7 custom options for the page. The first option has value 0. Specify None to disable the combobox.
    :ivar string clipboardText: The text to copy to the clipboard for a copy request.
    :ivar Dictionary action: The requests and coresponding fuctions that this class can handle.

    Class to represent the output for the Sports Results database.
    These functions were originally in the :py:class:`~database.Database` class.
    '''
    # True to show toolbars initially.
    TOOLBAR_INITIAL_SHOW = False



    def __init__(self, application):
        '''
        :param Database database: Specifies the :py:class:`~modDatabase.Database` object to connect to.

        Class constructor for the :py:class:`Render` class.
        '''
        # Initialise base classes.
        walton.toolbar.IToolbar.__init__(self)

        # The database to build page from.
        self.database = application.database
        self.application = application
        # The url to the edit for the page or None for no edit available.
        self.editTarget = None
        # The url to move to the next page or None for no next page.
        self.nextPage = None
        # The url to the previous page or None for no previous page.
        self.previousPage = None
        # True to enable the show ages button.
        self.showAge = False
        # True to enable the tournament selection combobox, false to disable it.
        self.tournamentSelect = False
        # True to enable the year selector, false to disable it.
        self.yearsSelect = False
        # True to enable the country selector, false to disable it.
        self.countrySelect = False
        # The page options or levels.  Use [] to specify upto 7 custom options for the page.  The first option has value 0.  Specify None to disable the combobox.
        self.levels = None
        # The text to copy to the clipboard for a copy request.
        self.clipboardText = None
        # A Html object to prepare the output for the browser.
        self.html = walton.html.Html()

        # Define the actions this module can handle and the function to handle the action.
        self.actions = {
            'home'              : self.showHome,
            'index'             : self.showIndex,
            'preferences'       : self.showPreferences,
            'show_team'         : self.showTeam,
            'head'              : self.showHeadToHead,
            'table_teams'       : self.showTableTeams,
            'table_last'        : self.showTableLast,
            'table_subset'      : self.showTableSubset
        }




    def decodeParameters(self, parametersString):
        '''
        :param string parametersString: Specify the request parameters as a string.
        :returns: A dictionary object of the parameter names and values.

        Decode the parameters from a link into a dictionary object.
        '''
        # Create an empty dictionary.
        dictionary = {}

        # Split into Key Value pairs by the '&' character.
        items = parametersString.split('&')
        for item in items:
            if item != '':
                key, value = item.split('=')
                dictionary[key] = value

        # Return the dictionary object built.
        return dictionary



    def getDefaultBoxHeight(self):
        ''' Results the default height for a win draw loss box. '''
        return max(20, 9 + self.application.configuration.textSize)



    def displayLastResults(self, cndb, teamIndex, theDate, lastResults):
        ''' Show the last results for the specified team. '''
        height = 18
        width = (height + 4) * lastResults
        self.html.add('<td>')
        self.html.add(f'<svg class="wdlbox" width="{width}" height="{height}" style="vertical-align: middle;">')

        sql = f"SELECT HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE (HOME_TEAM_ID = {teamIndex} OR AWAY_TEAM_ID = {teamIndex}) AND THE_DATE <= '{theDate}' ORDER BY THE_DATE DESC LIMIT 5;";
        # print(sql)
        cursor = cndb.execute(sql)
        count = 0
        pts = 0
        for row in cursor:
            pos = (lastResults - count - 1) * (height + 4)
            count += 1
            if row[2] == row[3]:
                # Draw.
                self.html.add(f'<rect class="wdlbox_draw" x="{pos}" y="0" width="{height}" height="{height}" style="stroke-width: 1; stroke: rgb(0, 0, 0);" />')
                pts += 1
            elif row[0] == teamIndex:
                # Home Team.
                if row[2] > row[3]:
                    self.html.add(f'<rect class="wdlbox_win" x="{pos}" y="0" width="{height}" height="{height}" style="stroke-width: 1; stroke: rgb(0, 0, 0);" />')
                    pts += 3
                else:
                    self.html.add(f'<rect class="wdlbox_lose" x="{pos}" y="0" width="{height}" height="{height}" style="stroke-width: 1; stroke: rgb(0, 0, 0);" />')
            else:
                # Away Team.
                if row[2] < row[3]:
                    self.html.add(f'<rect class="wdlbox_win" x="{pos}" y="0" width="{height}" height="{height}" style="stroke-width: 1; stroke: rgb(0, 0, 0);" />')
                    pts += 3
                else:
                    self.html.add(f'<rect class="wdlbox_lose" x="{pos}" y="0" width="{height}" height="{height}" style="stroke-width: 1; stroke: rgb(0, 0, 0);" />')
        cursor.close()
        self.html.addLine('</svg></td>')
        self.html.add(f'<td class="secondary" style="text-align: right;">{pts}</td>')



    def drawWinDrawLossBox(self, width, height, numWins, numDraws, numLosses):
        ''' Draws a svg graphical box to display the specified wins, draws and losses ratio.

        :param int width: Specifies the width of the box.  Default to 200.
        :param int height: Specifies the height of the box.  Default to 18.
        :param int numWins: Specifies the number of wins.
        :param int numDraws: Specifies the number of draws.
        :param int numLosses: Specifies the number of losses.
        '''
        totalMatches = numWins + numDraws + numLosses
        self.html.add('<svg class="wdlbox" width="{}" height="{}" style="vertical-align: middle;">'.format(width, height))
        if totalMatches > 0:
            pixWin = int(round(width * numWins / totalMatches, 0))
            if numWins > 0:
                self.html.add('<rect class="wdlbox_win" width="{}" height="{}" style="stroke-width: 0; stroke: rgb(0, 0, 0);" />'.format(pixWin, height))
            pixDraw = int(round(width * numDraws / totalMatches, 0))
            if numDraws > 0:
                self.html.add('<rect class="wdlbox_draw" x="{}" y="0" width="{}" height="{}" style="stroke-width: 0; stroke: rgb(0, 0, 0);" />'.format(pixWin, pixDraw, height))
            if numLosses > 0:
                self.html.add('<rect class="wdlbox_lose" x="{}" y="0" width="{}" height="{}" style="stroke-width: 0; stroke: rgb(0, 0, 0);" />'.format(pixWin + pixDraw, width - pixWin - pixDraw, height))
        # Border.
        self.html.add('<rect class="wdlbox" width="{}" height="{}" style="fill: none; stroke-width: 2;" />'.format(width, height))
        # Draw a tick mark at half way.
        self.html.add('<line class="wdlbox" x1="{}" y1="0" x2="{}" y2="4" style="stroke-width: 1;" />'.format(width / 2, width / 2))
        self.html.add('<line class="wdlbox" x1="{}" y1="{}" x2="{}" y2="{}" style="stroke-width: 1;" />'.format(width / 2, height, width / 2, height - 4))
        self.html.addLine('</svg>')



    def drawPossiblePointsBox(self, width, height, minimum, maximum, scaleMin, scaleMax, expectedPoints, safePoints):
        ''' Draws a svg graphical box to display the specified wins, draws and losses ratio.

        :param int width: Specifies the width of the box.  Default to 200.
        :param int height: Specifies the height of the box.  Default to 18.
        :param int numWins: Specifies the number of wins.
        :param int numDraws: Specifies the number of draws.
        :param int numLosses: Specifies the number of losses.
        '''
        self.html.add('<svg class="wdlbox" width="{}" height="{}" style="vertical-align: middle;">'.format(width, height))
        pixMinimum = int(round(width * (minimum - scaleMin) / (scaleMax - scaleMin), 0))
        pixMaximum = int(round(width * (maximum - scaleMin) / (scaleMax - scaleMin), 0))

        self.html.add(f'<rect class="wdlbox_draw" x="{pixMinimum}" y="0" width="{pixMaximum - pixMinimum}" height="{height}" style="stroke-width: 0; stroke: rgb(0, 0, 0);" />')
        tickPos = int(round(width * (expectedPoints - scaleMin) / (scaleMax - scaleMin), 0))
        pixMinimum = ( pixMinimum + tickPos ) // 2
        pixMaximum = ( pixMaximum + tickPos ) // 2
        self.html.add(f'<rect class="wdlbox_win" x="{pixMinimum}" y="0" width="{pixMaximum - pixMinimum}" height="{height}" style="stroke-width: 0; stroke: rgb(0, 0, 0);" />')

        # Border.
        self.html.add('<rect class="wdlbox" width="{}" height="{}" style="fill: none; stroke-width: 2;" />'.format(width, height))
        # Draw a tick mark at safe point points.
        tickPos = int(round(width * (safePoints - scaleMin) / (scaleMax - scaleMin), 0))
        self.html.add(f'<line class="wdlbox" x1="{tickPos}" y1="0" x2="{tickPos}" y2="4" style="stroke-width: 1;" />')
        self.html.add(f'<line class="wdlbox" x1="{tickPos}" y1="{height}" x2="{tickPos}" y2="{height - 4}" style="stroke-width: 1;" />')
        # Draw a line at expected points.
        tickPos = int(round(width * (expectedPoints - scaleMin) / (scaleMax - scaleMin), 0))
        self.html.add(f'<line class="wdlbox" x1="{tickPos}" y1="0" x2="{tickPos}" y2="{height}" style="stroke-width: 2;" />')
        self.html.addLine('</svg>')



    def displayTable(self, cndb, sql, isCombinedHomeAway, isAddColour, isShowRange, theDate, lastResults, isBySeason):
        ''' Display a table on the html object. '''
        if isShowRange:
            isShowPossiblePoints = False
            cursor = cndb.execute(sql)
            count = 0
            minPoints = 0
            maxPoints = 0
            safePoints = 0
            arrayPoints = []
            for row in cursor:
                count += 1
                played = row[1] + row[2] + row[3] + row[6] + row[7] + row[8]
                if played < 38:
                    isShowPossiblePoints = True
                teamMinPoints = row[11]
                remainingMatches = 38 - played
                teamMaxPoints = teamMinPoints + remainingMatches * 3
                goalDifference = row[12]
                arrayPoints.append((teamMinPoints + (goalDifference - 2 * remainingMatches) / 1000.0, teamMaxPoints + (goalDifference + 2 * remainingMatches) / 1000.0))
                if count == 1:
                    minPoints = teamMinPoints
                    maxPoints = teamMaxPoints
                else:
                    if teamMaxPoints > maxPoints:
                        maxPoints = teamMaxPoints
                    if teamMinPoints < minPoints:
                        minPoints = teamMinPoints
                if count == 17:
                    safePoints = (int)(math.ceil(38 * row[11] / played))
                elif count == 18:
                    safePoints = (int)(math.ceil((safePoints + (int)(math.ceil(38 * row[11] / played))) / 2))
            cursor.close()

        self.html.addLine('<table>')
        if isCombinedHomeAway:
            self.html.add('<tr><td colspan="2">Team</td><td style="text-align: right;">P</td><td style="text-align: right;">W</td><td style="text-align: right;">D</td><td style="text-align: right;">L</td><td style="text-align: right;">F</td><td style="text-align: right;">A</td>')
        else:
            self.html.add('<tr><td colspan="2">Team</td><td style="text-align: right;">P</td><td style="text-align: right;">W</td><td style="text-align: right;">D</td><td style="text-align: right;">L</td><td style="text-align: right;">F</td><td style="text-align: right;">A</td><td style="text-align: right;">W</td><td style="text-align: right;">D</td><td style="text-align: right;">L</td><td style="text-align: right;">F</td><td style="text-align: right;">A</td>')
        self.html.add('<td style="text-align: right;">Pts</td><td style="text-align: right;">Dif</td>')
        self.html.add('<td style="text-align: center;">Ratio</td>')
        if isShowRange and isShowPossiblePoints:
            self.html.add('<td colspan="2">Possible Points</td>')
        if lastResults > 0:
            self.html.add(f'<td colspan="2">Last {lastResults} Matches</td>')
        self.html.addLine('</tr>')
        # print(sql)
        cursor = cndb.execute(sql)
        count = 0
        for row in cursor:
            if count <= 3 and isAddColour:
                self.html.add('<tr class="win2">')
            elif count >= 17 and isAddColour:
                self.html.add('<tr class="lost2">')
            else:
                self.html.add('<tr>')

            if isBySeason:
                season = self.database.getSeason(row[14])
                self.html.add(f'<td colspan="2" style="text-align: right;">{season.name}</td>')
            else:

                team = self.database.getTeam(row[0])

                count += 1
                self.html.add(f'<td class="rank" style="text-align: right; vertical-align: middle;">{count}</td>')
                self.html.add(f'<td style="text-align: right;">{team.toHtml()}</td>')

            played = row[1] + row[2] + row[3] + row[6] + row[7] + row[8]
            self.html.add(f'<td class="secondary" style="text-align: right;">{played}</td>')

            if isCombinedHomeAway:
                # Combined home and away.
                self.html.add(f'<td class="win" style="text-align: right;">{row[1] + row[6]}</td>')
                self.html.add(f'<td class="draw" style="text-align: right;">{row[2] + row[7]}</td>')
                self.html.add(f'<td class="lost" style="text-align: right;">{row[3] + row[8]}</td>')
                self.html.add(f'<td class="secondary" style="text-align: right;">{row[4] + row[9]}</td>')
                self.html.add(f'<td class="secondary" style="text-align: right;">{row[5] + row[10]}</td>')
            else:
                # Separate home and away.
                self.html.add(f'<td class="win" style="text-align: right;">{row[1]}</td>')
                self.html.add(f'<td class="draw" style="text-align: right;">{row[2]}</td>')
                self.html.add(f'<td class="lost" style="text-align: right;">{row[3]}</td>')
                self.html.add(f'<td class="secondary" style="text-align: right;">{row[4]}</td>')
                self.html.add(f'<td class="secondary" style="text-align: right;">{row[5]}</td>')

                self.html.add(f'<td class="win" style="text-align: right;">{row[6]}</td>')
                self.html.add(f'<td class="draw" style="text-align: right;">{row[7]}</td>')
                self.html.add(f'<td class="lost" style="text-align: right;">{row[8]}</td>')
                self.html.add(f'<td class="secondary" style="text-align: right;">{row[9]}</td>')
                self.html.add(f'<td class="secondary" style="text-align: right;">{row[10]}</td>')

            self.html.add(f'<td class="pts" style="text-align: right;">{row[11]}</td>')
            self.html.add(f'<td class="secondary" style="text-align: right;">{row[12]:+}</td>')

            self.html.add('<td>')
            self.drawWinDrawLossBox(200, 18, row[1] + row[6], row[2] + row[7], row[3] + row[8])
            self.html.add('</td>')

            if isShowRange and isShowPossiblePoints:
                teamMinPoints = row[11]
                teamMaxPoints = teamMinPoints + (38 - played) * 3
                if teamMaxPoints > maxPoints:
                    maxPoints = teamMaxPoints
                # self.html.add(f'<td class="minor" style="text-align: right;">{teamMaxPoints}</td>')
                if count >= 17:
                    self.html.add(f'<td title="Expected safe points are {safePoints}.">')
                else:
                    self.html.add('<td style="white-space: nowrap;">')
                self.drawPossiblePointsBox(400, 18, teamMinPoints, teamMaxPoints, minPoints, maxPoints, 38 * row[11] / played, safePoints)
                self.html.add('</td>')

                # Show possible final ranking.
                self.html.add(f'<td class="rank" style="white-space: nowrap; text-align: center;" title="{team.name} maximum points are {teamMaxPoints}.">')
                goalDifference = row[12]
                teamMinPoints += goalDifference / 1000.0
                teamMaxPoints += goalDifference / 1000.0
                count1 = 0
                count2 = 1
                for points in arrayPoints:
                    if teamMinPoints <= points[1]:
                        count1 += 1
                    if teamMaxPoints < points[0]:
                        count2 += 1
                    # print(f'{points[0]:.3f} {points[1]:.3f} {teamMaxPoints:.3f} {teamMinPoints:.3f} {count1:3} {count2:3}')
                # print()
                if count1 != count2:
                    self.html.add(f' {count2}-{count1}')
                else:
                    self.html.add(f' {count1}')
                self.html.add('</td>')

            if lastResults > 0:
                self.displayLastResults(cndb, team.index, theDate, lastResults)

            self.html.addLine('</tr>')
        self.html.addLine('</table>')



    def displaySelectDates(self, linkTarget, cndb, parameters):
        ''' Display a select dates fieldset onto the page. '''

        # Decode the parameters.
        startDate = parameters['start_date'] if 'start_date' in parameters else None
        finishDate = parameters['finish_date'] if 'finish_date' in parameters else None
        dateType = int(parameters['date_type']) if 'date_type' in parameters else 0

        # Show the date selector.
        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;"><legend>Select Dates</legend>')
        self.html.addLine(f'<form action="app:{linkTarget}">')
        for key in parameters:
            if key in ['start_date', 'finish_date', 'date_type']:
                # Ignore these keys.
                pass
            else:
                self.html.addLine(f'<input type="hidden" name="{key}" value="{parameters[key]}" />')
            # print(f'{key} => {parameters[key]}')

        self.html.addLine('<table>')
        self.html.add('<tr><td>Type</td><td colspan="4"><select name="date_type" onchange="this.form.submit();">')
        if dateType == 0:
            self.html.add('<option value="0">Free</option>')
        if dateType == -1:
            self.html.add('<option value="0" selected="yes">This Season</option>')
            startDate = '2022-08-06'
            finishDate = datetime.date.today()
        else:
            self.html.add('<option value="-1">This Season</option>')
        if dateType == -2:
            self.html.add('<option value="0" selected="yes">Last Season</option>')
            startDate = '2021-08-14'
            finishDate = '2022-05-22'
        else:
            self.html.add('<option value="-2">Last Season</option>')
        if dateType == -3:
            self.html.add('<option value="0" selected="yes">This Year</option>')
            startDate = f'{datetime.date.today().year}-01-01'
            finishDate = datetime.date.today()
        else:
            self.html.add('<option value="-3">This Year</option>')
        if dateType == -4:
            self.html.add('<option value="0" selected="yes">Last Year</option>')
            startDate = f'{datetime.date.today().year - 1}-01-01'
            finishDate = f'{datetime.date.today().year - 1}-12-31'
        else:
            self.html.add('<option value="-4">Last Year</option>')

        sql = "SELECT ID, LABEL, START, FINISH FROM DATE_BLOCKS ORDER BY ID DESC;"
        cursor = cndb.execute(sql)
        for row in cursor:
            if dateType == row[0]:
                self.html.add(f'<option value="0" selected="yes">{row[1]}</option>')
                startDate = row[2]
                if row[3] is None:
                    finishDate = datetime.date.today()
                else:
                    finishDate = row[3]
            else:
                self.html.add(f'<option value="{row[0]}">{row[1]}</option>')
        cursor = None

        self.html.add('</select></td><td>')
        self.html.add('<input type="submit" name="update" value="OK" />')
        self.html.addLine('</td></tr>')
        self.html.add(f'<tr style="border: 1px solid black;"><td>Start Date</td><td><input type="date" name="start_date" value="{startDate}" /></td><td style="padding-right: 20px;">{startDate}</td>')
        self.html.add(f'<td style="border-left: 1px solid black; padding-left: 20px;">Finish Date</td><td><input type="date" name="finish_date" value="{finishDate}" /></td><td>{finishDate}</td></tr>')
        self.html.addLine('</table>')
        self.html.addLine('</form>')

        self.html.addLine('</fieldset>')

        # Return the date range.
        return startDate, finishDate



    def showHome(self, parameters):
        '''
        Render the homepage on the html object.

        :param string parametersString: Specify the request parameters as a string. The keys 'firstyear' and 'lastyear' are optional.
        '''
        # print('showHome()')
        # Decode the parameters.
        level = int(parameters['level']) if 'level' in parameters else 0
        seasonIndex = int(parameters['season']) if 'season' in parameters else 1
        # if 'date' in parameters:
        #    print(parameters['date'])
        theDate = datetime.date(*time.strptime(parameters['date'], "%Y-%m-%d")[:3]) if 'date' in parameters else datetime.date.today()
        isRange = True

        # Check the the date is in season range.
        season = self.database.getSeason(seasonIndex)
        if theDate > season.finishDate:
            theDate = None

        self.html.clear()
        # self.displayToolbar(True, None, 'home?firstyear={}&lastyear={}'.format(firstSeason-1, lastSeason-1), 'home?firstyear={}&lastyear={}'.format(firstSeason+1, lastSeason+1), False, True, False)
        toolbar = self.buildToolbarOptions(level, 'level', ((0, 'Default'), (1, 'Combined')), 'app:home', (('date', theDate), ('season', seasonIndex) ))
        if theDate is None:
            self.editTarget = f'edit_date?season={seasonIndex}'
        else:
            self.editTarget = f'edit_date?season={seasonIndex}&date={theDate}'
        if season.getPreviousSeasonIndex() is None:
            previousSeason = None
        else:
            previousSeason = f'home?season={season.getPreviousSeasonIndex()}'
        if season.getNextSeasonIndex() is None:
            nextSeason = None
        else:
            nextSeason = f'home?season={season.getNextSeasonIndex()}'
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, self.editTarget, previousSeason, nextSeason, False, True, False, toolbar)

        self.html.add(f'<p><span class="h1">{season.name}</span>')
        self.html.add(f' <span class="label">from</span> {self.database.formatDate(season.startDate)} <span class="label">to</span> {self.database.formatDate(season.finishDate)}.')
        links = season.getLinks()
        if season.comments is not None or len(links) > 0:
            #self.html.add('<p>')
            if season.comments is not None:
                self.html.add(' {}'.format(team.comments))
            if len(links) > 0:
                self.html.add(' <span class="label">More information at</span>')
                count = 0
                for linkLabel in links:
                    count += 1
                    if count == 1:
                        self.html.add(' ')
                    elif count == len(links):
                        self.html.add(' <span class="label">and</span> ')
                    else:
                        self.html.add('<span class="label">,</span> ')
                    self.html.add('<a href="{}">{}</a>'.format(links[linkLabel], linkLabel))
                self.html.add('. ')
            #self.html.add('</p>')
        self.html.addLine('</p>')

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        self.html.add('<fieldset style="display: inline-block; vertical-align: top;"><legend>')
        if theDate is None:
            self.html.add('Final Table')
        else:
            self.html.add(f'Table to {self.database.formatDate(theDate)}')
        self.html.addLine('</legend>')

        sql = "SELECT TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR FROM ("

        # Summerise all the results.
        sql += "SELECT TEAM_ID, SUM(HOME_WINS) AS HOME_WINS, SUM(HOME_DRAWS) AS HOME_DRAWS, SUM(HOME_LOSES) AS HOME_LOSES, SUM(HOME_FOR) AS HOME_FOR, SUM(HOME_AGAINST) AS HOME_AGAINST, SUM(AWAY_WINS) AS AWAY_WINS, SUM(AWAY_DRAWS) AS AWAY_DRAWS, SUM(AWAY_LOSES) AS AWAY_LOSES, SUM(AWAY_FOR) AS AWAY_FOR, SUM(AWAY_AGAINST) AS AWAY_AGAINST FROM ("

        # Summerise all the home results.
        sql += "SELECT HOME_TEAM_ID AS TEAM_ID, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS HOME_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS HOME_DRAWS, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS HOME_LOSES, SUM(HOME_TEAM_FOR) AS HOME_FOR, SUM(AWAY_TEAM_FOR) AS HOME_AGAINST, 0 AS AWAY_WINS, 0 AS AWAY_DRAWS, 0 AS AWAY_LOSES, 0 AS AWAY_FOR, 0 AS AWAY_AGAINST FROM MATCHES "
        if theDate is None:
            # All season results
            sql += f"WHERE SEASON_ID = {seasonIndex} GROUP BY HOME_TEAM_ID "
        else:
            # Up to the date.
            sql += f"WHERE SEASON_ID = {seasonIndex} AND THE_DATE <= '{theDate}' GROUP BY HOME_TEAM_ID "
        sql += "UNION "
        # Summerise all the away results.
        sql += "SELECT AWAY_TEAM_ID AS TEAM_ID, 0 AS AWAY_WINS, 0 AS AWAY_DRAWS, 0 AS AWAY_LOSES, 0 AS AWAY_FOR, 0 AS AWAY_AGAINST, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS AWAY_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS AWAY_DRAWS, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS AWAY_LOSES, SUM(AWAY_TEAM_FOR) AS AWAY_FOR, SUM(HOME_TEAM_FOR) AS AWAY_AGAINST FROM MATCHES "
        if theDate is None:
            # All season results.
            sql += f"WHERE SEASON_ID = {seasonIndex} GROUP BY AWAY_TEAM_ID  "
        else:
            # Update to the date.
            sql += f"WHERE SEASON_ID = {seasonIndex} AND THE_DATE <= '{theDate}' GROUP BY AWAY_TEAM_ID  "
        sql += ") GROUP BY TEAM_ID) "
        sql += "ORDER BY PTS DESC, DIFF DESC, FOR DESC; "

        # print(sql)

        self.displayTable(cndb, sql, level == 1, True, True, season.finishDate if theDate is None else theDate, 5, False)
        self.html.addLine('</fieldset>')

        self.html.add('<fieldset style="display: inline-block; vertical-align: top;"><legend>')
        if theDate is None:
            self.html.add('Final Matches')
        else:
            self.html.add(f'Matches to {self.database.formatDate(theDate)}')
        self.html.addLine('</legend>')
        self.html.addLine('<table>')
        if theDate is None:
            # All Results.
            sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, REAL_HOME_TEAM_FOR, REAL_AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = ? ORDER BY THE_DATE DESC LIMIT 20;"
            params = (seasonIndex, )
        else:
            # Results up to date.
            sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, REAL_HOME_TEAM_FOR, REAL_AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = ? AND THE_DATE <= ? ORDER BY THE_DATE DESC LIMIT 20;"
            params = (seasonIndex, theDate)

        cursor = cndb.execute(sql, params)
        lastDate = None
        for row in cursor:
            theMatchDate = datetime.date(*time.strptime(row[0], "%Y-%m-%d")[:3])
            formatMatchDate = self.database.formatDate(theMatchDate)
            isDateGuess = row[1] == 1
            if isDateGuess:
                formatMatchDate = f'({row[0]})'
            homeTeam = self.database.getTeam(row[2])
            awayTeam = self.database.getTeam(row[3])

            if lastDate != row[0]:
                if lastDate is None:
                    self.html.add('<tr>')
                else:
                    self.html.add('<tr style="border-top: 1px solid black;">')
                self.html.add(f'<td class="date" style="text-align: center;"><a href="app:home?season={seasonIndex}&date={row[0]}">{formatMatchDate}</a></td>')
                lastDate = row[0]
            else:
                self.html.add('<tr>')
                self.html.add('<td></td>')
            self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
            whatIf = ''
            if row[6] != row[4] or row[7] != row[5]:
                whatIf = ' class="win"'
            self.html.add(f'<td{whatIf}>{row[4]}</td>')
            self.html.add(f'<td{whatIf}>{row[5]}</td>')
            self.html.add(f'<td>{awayTeam.toHtml()}</td>')
            self.html.addLine('</tr>')

        self.html.addLine('</table>')
        self.html.addLine('</fieldset>')

        # Future matches.
        if theDate is not None:
            self.html.add('<fieldset style="display: inline-block; vertical-align: top;"><legend>')
            self.html.add(f'Matches after {self.database.formatDate(theDate)}')
            self.html.addLine('</legend>')
            self.html.addLine('<table>')
            # Results after to date.
            sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, REAL_HOME_TEAM_FOR, REAL_AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = ? AND THE_DATE > ? ORDER BY THE_DATE LIMIT 20;"
            params = (seasonIndex, theDate)

            cursor = cndb.execute(sql, params)
            for row in cursor:
                self.html.add('<tr>')
                theMatchDate = row[0]
                isDateGuess = row[1] == 1
                if isDateGuess:
                    theMatchDate = f'({row[0]})'
                homeTeam = self.database.getTeam(row[2])
                awayTeam = self.database.getTeam(row[3])

                self.html.add(f'<td class="date" style="text-align: center;"><a href="app:home?season={seasonIndex}&date={row[0]}">{theMatchDate}</a></td>')
                self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
                whatIf = ''
                if row[6] != row[4] or row[7] != row[5]:
                    whatIf = ' class="win"'
                self.html.add(f'<td{whatIf}>{row[4]}</td>')
                self.html.add(f'<td{whatIf}>{row[5]}</td>')
                self.html.add(f'<td>{awayTeam.toHtml()}</td>')
                self.html.addLine('</tr>')

            self.html.addLine('</table>')
            self.html.addLine('</fieldset>')

        # Close the database.
        cndb.close()

        self.html.addLine('<fieldset><legend>Administration</legend>')
        self.html.addLine('<ul>')
        self.html.addLine('<li><a href="app:switch_sports">Switch Sports</a></li>')
        self.html.addLine('<li><a href="app:preferences">Preferences</a></li>')
        self.html.addLine('<li><a href="app:configure_sport">Configure Sport</a></li>')
        self.html.addLine('<li><a href="app:country_db">Country Database</a></li>')
        self.html.addLine('</ul>')
        self.html.addLine('</fieldset>')
        self.html.addLine('</td></tr></table>')

        # Set the page flags.
        self.levels = None
        self.clipboardText = None



    def showIndex(self, parameters):
        ''' Render the index on the html object. '''
        self.html.clear()
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, None, None, None, False, False, False)
        self.html.addLine('<h1>Table Database</h1>')

        self.html.addLine('<fieldset>')
        self.html.addLine('<legend>General</legend>')
        self.html.addLine('<ul>')
        self.html.addLine('<li><a href="app:table_teams">All Time Table</a></li>')
        self.html.addLine('<li><a href="app:table_last">Table of last 5 Results</a></li>')
        self.html.addLine('<li><a href="app:table_subset">Table of Subset of teams</a></li>')
        self.html.addLine('</ul>')
        self.html.addLine('</fieldset>')

        self.html.addLine('<fieldset>')
        self.html.addLine('<legend>Administration</legend>')
        self.html.addLine('<ul>')
        self.html.addLine('<li><a href="app:preferences">Preferences</a></li>')
        self.html.addLine('</ul>')

        # Set the page flags
        self.tournamentSelect = False
        self.countrySelect = False
        self.levels = None
        self.clipboardText = None



    def showPreferences(self, parameters):
        '''
        Render the preferences page on the html object.
        Originally this was a GTK dialog.
        '''

        isResetStyleSheets = False
        if 'font_plus' in parameters:
            self.application.configuration.setTextSize(self.application.configuration.textSize + 1)
            isResetStyleSheets = True
        if 'font_minus' in parameters:
            self.application.configuration.setTextSize(self.application.configuration.textSize - 1)
            isResetStyleSheets = True
        if 'colour_scheme' in parameters:
            self.application.configuration.setColourScheme(parameters['colour_scheme'])
            isResetStyleSheets = True
        if 'font' in parameters:
            self.application.configuration.setFont(parameters['font'])
            # isResetStyleSheets = True
        if 'vertical_plus' in parameters:
            self.application.configuration.setSpace(self.application.configuration.verticalSpace + 1, self.application.configuration.horizontalSpace)
            isResetStyleSheets = True
        if 'vertical_minus' in parameters:
            self.application.configuration.setSpace(self.application.configuration.verticalSpace - 1, self.application.configuration.horizontalSpace)
            isResetStyleSheets = True
        if 'horizontal_plus' in parameters:
            self.application.configuration.setSpace(self.application.configuration.verticalSpace, self.application.configuration.horizontalSpace + 1)
            isResetStyleSheets = True
        if 'horizontal_minus' in parameters:
            self.application.configuration.setSpace(self.application.configuration.verticalSpace, self.application.configuration.horizontalSpace - 1)
            isResetStyleSheets = True
        if 'divider' in parameters:
            self.application.configuration.setDivider(parameters['divider'] == "1")

        if isResetStyleSheets:
            self.application.setStyleSheets()

        self.html.clear()
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, None, None, None, False, False, False)
        self.html.addLine('<h1>Preferences</h1>')
        self.html.addLine('<form action="app:preferences">')
        self.html.add('<p>Text size is ')
        self.html.add('<button name="font_minus">-</button>')
        self.html.add('<input type="text" value="{}" style="text-align: center; width: 80px;" />'.format(self.application.configuration.textSize))
        self.html.add('<button name="font_plus">+</button>')
        self.html.addLine('</p>')

        self.html.add('<p>The colour scheme is ')
        self.html.add('<select name="colour_scheme" onchange="this.form.submit();">')
        colourSchemes = ['grey', 'black', 'none']
        for scheme in colourSchemes:
            self.html.add('<option')
            if scheme == self.application.configuration.colourScheme:
                self.html.add(' selected="yes"')
            self.html.add('>{}</option>'.format(scheme))
        self.html.add('</select>')
        self.html.addLine('</p>')

        self.html.add('<p>The font is {} '.format(self.application.configuration.fontName))
        self.html.add('<select name="font" onchange="this.form.submit();">')
        fonts = self.application.getFonts()
        for font in fonts:
            self.html.add('<option')
            if font == self.application.configuration.fontName:
                self.html.add(' selected="yes"')
            self.html.add('>{}</option>'.format(font))
        self.html.add('</select>')
        self.html.addLine('</p>')

        self.html.add('<p>Vertical space is ')
        self.html.add('<button name="vertical_minus">-</button>')
        self.html.add('<input type="text" value="{}" style="text-align: center; width: 80px;" />'.format(self.application.configuration.verticalSpace))
        self.html.add('<button name="vertical_plus">+</button>')
        self.html.addLine('</p>')

        self.html.add('<p>Horizontal space is ')
        self.html.add('<button name="horizontal_minus">-</button>')
        self.html.add('<input type="text" value="{}" style="text-align: center; width: 80px;" />'.format(self.application.configuration.horizontalSpace))
        self.html.add('<button name="horizontal_plus">+</button>')
        self.html.addLine('</p>')

        self.html.add('<p>The divider is ')
        self.html.add('<select name="divider" onchange="this.form.submit();">')
        self.html.add('<option value="1"')
        if self.application.configuration.isDivider:
            self.html.add(' selected="yes"')
        self.html.add('>On</option>')
        self.html.add('<option value="0"')
        if not self.application.configuration.isDivider:
            self.html.add(' selected="yes"')
        self.html.add('>Off</option>')
        self.html.add('</select>')
        self.html.addLine('</p>')

        self.html.addLine('</form>')

        # Set the page flags.
        self.editTarget = None
        self.nextPagePage = None
        self.previousPage = None
        self.showAge = False
        self.tournamentSelect = False
        self.countrySelect = False
        self.yearsSelect = False
        self.levels = None



    def showAbout(self, parameters):
        '''
        Render the about page on the html object.

        :param Dict parameters: Specify the request parameters as a dictionary.
        '''
        # Show the about page.
        self.html.clear()
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, None, None, None, False, False, False)
        self.html.addLine('<h1>Table program</h1>')
        self.html.addLine('<p>by Steve Walton &copy; 2022-2022</p>')

        self.html.addLine("<hr/>")
        self.html.addLine("<table>")
        self.html.addLine("<tr><td>Linux</td><td>Python</td><td>2011-2022</td></tr>")
        self.html.addLine("<tr><td>Windows&trade;</td><td>C#</td><td>2007-2011</td></tr>")
        self.html.addLine("<tr><td>Windows&trade;</td><td>Access</td><td>1995-2007</td></tr>")
        self.html.addLine("<tr><td>Amiga</td><td>GFA Basic</td><td>1990-1995</td></tr>")
        self.html.addLine("</table>")

        self.html.addLine('<hr/>')
        self.html.addLine('<h1>Style Test (h1)</h1>')
        self.html.addLine('<h2>This is h2 style</h2>')
        self.html.addLine('<p>')
        self.html.addLine('This is how <a href="style_test.html">links</a> appear. ')
        self.html.addLine('The following styles can be used in &lt;p&gt; or &lt;span&gt; tags. ')
        self.html.addLine('To split items into columns use &lt;table class="columns"&gt;')
        self.html.addLine('</p>')

        self.html.addLine('<table class="columns"><tr><td>')
        self.html.addLine('<table>')
        self.html.addLine('<tr class="title"><td colspan="3">&lt;tr class="title"&gt;</td></tr>')
        country = self.database.getCountry(1)
        self.html.addLine('<tr><td class="date" style="text-align: right; vertical-align: middle;">&lt;td class="date"&gt;</td><td class="team">&lt;td class="team"&gt; <span class="age">&lt;span class="age"&gt;</span></td><td>{}</td></tr>'.format(country.toHtml()))
        self.html.addLine('<tr><td class="date" style="text-align: right; vertical-align: middle;">&lt;td class="date"&gt;</td><td><span class="team">&lt;span class="team"&gt;</span> <span class="years">&lt;span class="years"&gt;</span></td><td>{}</td></tr>'.format(country.toHtml()))
        self.html.addLine('<tr><td class="date" style="text-align: right; vertical-align: middle;">1982</td><td class="team">John McEnroe <span class="age">(26)</span></td><td>USA</td></tr>')
        self.html.addLine('<tr><td style="text-align: right; vertical-align: middle;"><a href="style_test.html"><span class="date">1982</span></a></td><td class="team"><a href="#">Bjorn Borg</a> <span class="years">(1974-1981)</span></td><td>SWE</td></tr>')
        self.html.addLine('<tr><td colspan="3" style="text-align: center; vertical-align: middle;"><span class="win">&lt;span class="win"&gt;</span> <span class="draw">&lt;span class="draw"&gt;</span> <span class="lost">&lt;span class="lost"&gt;</span></td></tr>')
        self.html.addLine('</table>')
        self.html.addLine('</td><td>')
        self.html.addLine('<p>This is some text in the second column.</p>')
        self.html.addLine('<p class="rank">class="rank" is available now.</p>')
        self.html.addLine('<p class="comment">class="comment" is available now.</p>')
        self.html.addLine('<p class="secondary">class="secondary" is available now.</p>')
        self.html.addLine('<p class="minor">class="minor" is available now.</p>')
        self.html.addLine('</td></tr></table>')

        # self.html.addLine('<p>Here it is: <applet code="file:////home/waltons/Documents/Code/Innoval/AppletTest/HelloWorld.class" WIDTH="200" height="40">This is where HelloWorld.class runs.</applet></p>')
        # self.html.addLine('<p>Here it is: <applet code="HelloWorld.class" WIDTH="200" height="40">This is where HelloWorld.class runs.</applet></p>')
        self.html.addLine('<p>')
        # self.html.addLine('<svg width="100%" height="100%" version="1.1" xmlns="http://www.w3.org/2000/svg" border="1">')
        self.html.addLine('<svg width="100%" height="100px" version="1.1" xmlns="http://www.w3.org/2000/svg" border="1">')
        self.html.addLine('<circle cx="100" cy="50" r="45" stroke="black" stroke-width="2" fill="red"/>')
        self.html.addLine('<rect x="200" y="5" width="100" height="50" style="fill: rgb(0, 0, 255); stroke-width: 1; stroke: rgb(0, 0, 0)"/>')
        self.html.addLine('<text x="210" y="25" style="font-size: 10pt;">Steve Walton</text>')
        self.html.addLine('<rect x="310" y="5" width="100" height="50" rx="2" ry="2" style="fill: rgb(0, 255, 0); stroke-width: 1; stroke: rgb(0, 0, 0)"/>')
        self.html.addLine('<text x="320" y="25" style="font-size: 8pt;">Steve Walton</text>')
        self.html.addLine('</svg>')
        self.html.addLine('</p>')

        self.html.addLine('<p>This is the next line.</p>')

        # Set the page flags.
        self.editTarget = None
        self.nextPagePage = None
        self.previousPage = None
        self.showAge = False
        self.tournamentSelect = False
        self.countrySelect = False
        self.yearsSelect = False
        self.levels = None



    def showTeam(self, parameters):
        '''
        Render the specified team on the html object.

        :param string parametersString: Specify the request parameters as as string. This should include 'id' to identify the actual team.
        '''
        # Decode the paramters.
        teamIndex = int(parameters['id']) if 'id' in parameters else 1
        isShowDates = True if 'show_date' in parameters else False
        theDate = parameters['date'] if 'date' in parameters else f'{datetime.date.today()}'
        level = int(parameters['level']) if 'level' in parameters else 0
        isShowAge = True if 'age' in parameters else False
        firstYear = parameters['firstyear'] if 'firstyear' in parameters else None
        lastYear = parameters['lastyear'] if 'lastyear' in parameters else None
        tournamentIndex = int(parameters['tournamentid']) if 'tournamentid' in parameters else 0
        flags = int(parameters['flags']) if 'flags' in parameters else 0
        startDate = parameters['start_date'] if 'start_date' in parameters else None
        finishDate = parameters['finish_date'] if 'finish_date' in parameters else None

        # Get the team object.
        team = self.database.getTeam(teamIndex)

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        # Initialise the display.
        self.html.clear()
        self.editTarget = f'edit_team?team={teamIndex}'
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, self.editTarget, None, None, True, True, False, '')

        self.html.add(f'<p><span class="h1">{team.name}</span></p>')

        # Optionally display a dates selector.
        if isShowDates:
            startDate, finishDate = self.displaySelectDates('show_team', cndb, parameters)
            self.html.addLine('<br />')

        if startDate is None:
            startDate = datetime.date(1900, 1, 1)
            finishDate = theDate
        else:
            theDate = finishDate

        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;"><legend>Matches</legend>')
        self.html.addLine('<table>')
        sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, SEASON_ID FROM MATCHES WHERE (HOME_TEAM_ID = ? OR AWAY_TEAM_ID = ?) AND THE_DATE >= ? AND THE_DATE <= ? ORDER BY THE_DATE DESC;"
        params = (teamIndex, teamIndex, startDate, finishDate)
        cursor = cndb.execute(sql, params)
        seasonIndex = 1
        for row in cursor:
            theMatchDate = datetime.date(*time.strptime(row[0], "%Y-%m-%d")[:3])
            isDateGuess = row[1] == 1
            if isDateGuess:
                formatMatchDate = f'({row[0]})'
            else:
                formatMatchDate = self.database.formatDate(theMatchDate)
            homeTeam = self.database.getTeam(row[2])
            awayTeam = self.database.getTeam(row[3])
            if teamIndex == homeTeam.index:
                if row[4] > row[5]:
                    className = 'win2'
                elif row[4] < row[5]:
                    className = 'lost2'
                else:
                    className = 'draw2'
            else:
                if row[4] < row[5]:
                    className = 'win2'
                elif row[4] > row[5]:
                    className = 'lost2'
                else:
                    className = 'draw2'

            if row[6] != seasonIndex:
                seasonIndex = row[6]
                self.html.add(f'<tr class="{className}" style="border-top: 3px solid black;">')
            else:
                self.html.add(f'<tr class="{className}">')
            self.html.add(f'<td class="date" style="text-align: center;"><a href="app:show_team?id={teamIndex}&date={row[0]}">{formatMatchDate}</a></td>')
            self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
            self.html.add(f'<td>{row[4]}</td>')
            self.html.add(f'<td>{row[5]}</td>')
            self.html.add(f'<td>{awayTeam.toHtml()}</td>')
            self.html.add(f'<td title="Head to Head"><a href="app:head?team1={teamIndex}&team2={homeTeam.index if homeTeam.index != teamIndex else awayTeam.index}&date={theDate}"><i class="fas fa-user"></i></a></td>')
            self.html.addLine('</tr>')

        self.html.addLine('</table>')
        self.html.addLine('</fieldset>')

        # Start a second column.
        self.html.addLine('<div style="display: inline-block; vertical-align: top;">')

        # Show a future matches.
        sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, SEASON_ID FROM MATCHES WHERE (HOME_TEAM_ID = ? OR AWAY_TEAM_ID = ?) AND THE_DATE > ? ORDER BY THE_DATE LIMIT 5;"
        params = (teamIndex, teamIndex, theDate)
        cursor = cndb.execute(sql, params)
        seasonIndex = 1
        isFirst = True
        for row in cursor:
            if isFirst:
                self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;"><legend>Future Matches</legend>')
                self.html.addLine('<table>')
                isFirst = False
            theMatchDate = datetime.date(*time.strptime(row[0], "%Y-%m-%d")[:3])
            isDateGuess = row[1] == 1
            if isDateGuess:
                formatMatchDate = f'({row[0]})'
            else:
                formatMatchDate = self.database.formatDate(theMatchDate)
            homeTeam = self.database.getTeam(row[2])
            awayTeam = self.database.getTeam(row[3])
            if teamIndex == homeTeam.index:
                if row[4] > row[5]:
                    className = 'win2'
                elif row[4] < row[5]:
                    className = 'lost2'
                else:
                    className = 'draw2'
            else:
                if row[4] < row[5]:
                    className = 'win2'
                elif row[4] > row[5]:
                    className = 'lost2'
                else:
                    className = 'draw2'

            if row[6] != seasonIndex:
                seasonIndex = row[6]
                self.html.add(f'<tr class="{className}" style="border-top: 3px solid black;">')
            else:
                self.html.add(f'<tr class="{className}">')
            self.html.add(f'<td class="date" style="text-align: center;"><a href="app:show_team?id={teamIndex}&date={row[0]}">{formatMatchDate}</a></td>')
            self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
            self.html.add(f'<td>{row[4]}</td>')
            self.html.add(f'<td>{row[5]}</td>')
            self.html.add(f'<td>{awayTeam.toHtml()}</td>')
            self.html.add(f'<td title="Head to Head"><a href="app:head?team1={teamIndex}&team2={homeTeam.index if homeTeam.index != teamIndex else awayTeam.index}&date={row[0]}"><i class="fas fa-user"></i></a></td>')
            self.html.addLine('</tr>')
        if not isFirst:
            self.html.addLine('</table>')
            self.html.addLine('</fieldset>')
            self.html.addLine('<br />')

        # Show a season summary.
        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;"><legend>Season Summary</legend>')
        sql = "SELECT HOME_TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR, HOME_RESULTS.SEASON_ID FROM "
        sql += "(SELECT HOME_TEAM_ID, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS HOME_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS HOME_DRAWS, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS HOME_LOSES, SUM(HOME_TEAM_FOR) AS HOME_FOR, SUM(AWAY_TEAM_FOR) AS HOME_AGAINST, SEASON_ID FROM MATCHES "
        sql += f"WHERE HOME_TEAM_ID = {teamIndex} AND THE_DATE >= '{startDate}' AND THE_DATE <= '{theDate}' GROUP BY SEASON_ID) AS HOME_RESULTS "
        sql += "INNER JOIN "
        sql += "(SELECT AWAY_TEAM_ID, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS AWAY_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS AWAY_DRAWS, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS AWAY_LOSES, SUM(AWAY_TEAM_FOR) AS AWAY_FOR, SUM(HOME_TEAM_FOR) AS AWAY_AGAINST, SEASON_ID FROM MATCHES "
        sql += f"WHERE AWAY_TEAM_ID = {teamIndex} AND THE_DATE >= '{startDate}' AND THE_DATE <= '{theDate}' GROUP BY SEASON_ID) AS AWAY_RESULTS "
        sql += "ON HOME_RESULTS.SEASON_ID = AWAY_RESULTS.SEASON_ID "
        sql += "ORDER BY HOME_RESULTS.SEASON_ID;"

        self.displayTable(cndb, sql, False, False, False, None, 0, True)
        self.html.addLine('</fieldset>')
        self.html.addLine('<br />')

        # summaryType = 2
        for summaryType in range(2):
            if summaryType == 1:
                self.html.addLine('<br />')
                self.html.addLine(f'<fieldset style="display: inline-block; vertical-align: top;"><legend>Summary Points against {team.name}</legend>')
            else:
                self.html.addLine(f'<fieldset style="display: inline-block; vertical-align: top;"><legend>Summary Points for {team.name}</legend>')

            # Points that teams have score against this team.
            sql = "SELECT TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR FROM ("

            if summaryType == 1:
                # Summerise all the results from other teams point of view.
                sql += "SELECT TEAM_ID, SUM(HOME_WINS) AS AWAY_LOSES, SUM(HOME_DRAWS) AS AWAY_DRAWS, SUM(HOME_LOSES) AS AWAY_WINS, SUM(HOME_FOR) AS AWAY_AGAINST, SUM(HOME_AGAINST) AS AWAY_FOR, SUM(AWAY_WINS) AS HOME_LOSES, SUM(AWAY_DRAWS) AS HOME_DRAWS, SUM(AWAY_LOSES) AS HOME_WINS, SUM(AWAY_FOR) AS HOME_AGAINST, SUM(AWAY_AGAINST) AS HOME_FOR FROM ("
            else:
                # Summerise all the results from this teams point of view.
                sql += "SELECT TEAM_ID, SUM(HOME_WINS) AS HOME_WINS, SUM(HOME_DRAWS) AS HOME_DRAWS, SUM(HOME_LOSES) AS HOME_LOSES, SUM(HOME_FOR) AS HOME_FOR, SUM(HOME_AGAINST) AS HOME_AGAINST, SUM(AWAY_WINS) AS AWAY_WINS, SUM(AWAY_DRAWS) AS AWAY_DRAWS, SUM(AWAY_LOSES) AS AWAY_LOSES, SUM(AWAY_FOR) AS AWAY_FOR, SUM(AWAY_AGAINST) AS AWAY_AGAINST FROM ("

            # Summerise all the home results.
            sql += "SELECT AWAY_TEAM_ID AS TEAM_ID, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS HOME_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS HOME_DRAWS, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS HOME_LOSES, SUM(HOME_TEAM_FOR) AS HOME_FOR, SUM(AWAY_TEAM_FOR) AS HOME_AGAINST, 0 AS AWAY_WINS, 0 AS AWAY_DRAWS, 0 AS AWAY_LOSES, 0 AS AWAY_FOR, 0 AS AWAY_AGAINST FROM MATCHES "
            sql += f"WHERE HOME_TEAM_ID = {teamIndex} AND THE_DATE >= '{startDate}' AND THE_DATE <= '{theDate}' "
            sql += "GROUP BY AWAY_TEAM_ID "
            sql += "\nUNION \n"
            # Summerise all the away results.
            sql += "SELECT HOME_TEAM_ID AS TEAM_ID, 0 AS HOME_WINS, 0 AS HOME_DRAWS, 0 AS HOME_LOSES, 0 AS HOME_FOR, 0 AS HOME_AGAINST, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS AWAY_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS AWAY_DRAWS, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS AWAY_LOSES, SUM(AWAY_TEAM_FOR) AS AWAY_FOR, SUM(HOME_TEAM_FOR) AS AWAY_AGAINST FROM MATCHES "
            sql += f"WHERE AWAY_TEAM_ID = {teamIndex} AND THE_DATE >= '{startDate}' AND THE_DATE <= '{theDate}' "
            sql += "GROUP BY HOME_TEAM_ID "
            sql += ") GROUP BY TEAM_ID) "
            sql += "ORDER BY PTS DESC, DIFF DESC, FOR DESC LIMIT 30; "

            self.displayTable(cndb, sql, False, False, False, None, 0, False)
            self.html.addLine('</fieldset>')

        self.html.addLine('</div>')

        # Close the database.
        cndb.close()

        # Set the page flags.
        self.nextPagePage = None
        self.previousPage = None



    def showHeadToHead(self, parameters):
        team1Index = int(parameters['team1'])
        team2Index = int(parameters['team2'])
        theDate = parameters['date'] if 'date' in parameters else f'{datetime.date.today()}'

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        team1 = self.database.getTeam(team1Index)
        team2 = self.database.getTeam(team2Index)

        # Initialise the display.
        self.html.clear()
        self.editTarget = None
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, self.editTarget, None, None, True, True, False, '')

        self.html.add(f'<p><span class="h1">{team1.name} vs {team2.name}</span></p>')

        self.html.addLine('<fieldset><legend>Summary</legend>')
        sql = "SELECT HOME_TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR FROM "
        sql += "(SELECT HOME_TEAM_ID, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS HOME_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS HOME_DRAWS, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS HOME_LOSES, SUM(HOME_TEAM_FOR) AS HOME_FOR, SUM(AWAY_TEAM_FOR) AS HOME_AGAINST FROM MATCHES "
        sql += f"WHERE ((HOME_TEAM_ID = {team1Index} AND AWAY_TEAM_ID = {team2Index}) OR (HOME_TEAM_ID = {team2Index} AND AWAY_TEAM_ID = {team1Index})) AND THE_DATE <= '{theDate}' "
        sql += "GROUP BY HOME_TEAM_ID) AS HOME_RESULTS "
        sql += "INNER JOIN "
        sql += "(SELECT AWAY_TEAM_ID, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS AWAY_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS AWAY_DRAWS, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS AWAY_LOSES, SUM(AWAY_TEAM_FOR) AS AWAY_FOR, SUM(HOME_TEAM_FOR) AS AWAY_AGAINST FROM MATCHES "
        sql += f"WHERE ((HOME_TEAM_ID = {team2Index} AND AWAY_TEAM_ID = {team1Index}) OR (HOME_TEAM_ID = {team1Index} AND AWAY_TEAM_ID = {team2Index})) AND THE_DATE <= '{theDate}' "
        sql += "GROUP BY AWAY_TEAM_ID) AS AWAY_RESULTS "
        sql += "ON HOME_RESULTS.HOME_TEAM_ID = AWAY_RESULTS.AWAY_TEAM_ID "
        sql += "ORDER BY PTS DESC, DIFF DESC, FOR DESC; "
        self.displayTable(cndb, sql, False, False, False, None, 0, False)
        self.html.addLine('</fieldset>')

        self.html.addLine('<fieldset><legend>Matches</legend>')
        self.html.addLine('<table>')
        sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, SEASON_ID FROM MATCHES WHERE ((HOME_TEAM_ID = ? AND AWAY_TEAM_ID = ?) OR (HOME_TEAM_ID = ? AND AWAY_TEAM_ID = ?)) AND THE_DATE <= ? ORDER BY THE_DATE DESC;"
        params = (team1Index, team2Index, team2Index, team1Index, theDate)
        cursor = cndb.execute(sql, params)
        for row in cursor:
            theMatchDate = datetime.date(*time.strptime(row[0], "%Y-%m-%d")[:3])
            formatMatchDate = self.database.formatDate(theMatchDate)
            isDateGuess = row[1] == 1
            if isDateGuess or theMatchDate > datetime.date.today():
                formatMatchDate = f'({row[0]})'
            homeTeam = self.database.getTeam(row[2])
            awayTeam = self.database.getTeam(row[3])
            if team1Index == homeTeam.index:
                if row[4] > row[5]:
                    className = 'win2'
                elif row[4] < row[5]:
                    className = 'lost2'
                else:
                    className = 'draw2'
            else:
                if row[4] < row[5]:
                    className = 'win2'
                elif row[4] > row[5]:
                    className = 'lost2'
                else:
                    className = 'draw2'

            self.html.add(f'<tr class="{className}">')
            self.html.add(f'<td class="date" style="text-align: center;"><a href="app:head?team1={team1Index}&team2={team2Index}&date={row[0]}">{formatMatchDate}</a></td>')
            self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
            self.html.add(f'<td>{row[4]}</td>')
            self.html.add(f'<td>{row[5]}</td>')
            self.html.add(f'<td>{awayTeam.toHtml()}</td>')
            self.html.addLine('</tr>')

        self.html.addLine('</table>')
        self.html.addLine('</fieldset>')

        # Close the database.
        cndb.close()

        # Set the page flags.
        self.nextPagePage = None
        self.previousPage = None



    def showTableTeams(self, parameters):
        ''' Show a table of teams for all time or between two specified dates. '''
        level = int(parameters['level']) if 'level' in parameters else 0
        # startDate = parameters['start_date'] if 'start_date' in parameters else None
        # finishDate = parameters['finish_date'] if 'finish_date' in parameters else None

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        # Initialise the display.
        self.html.clear()
        self.editTarget = None
        toolbar = self.buildToolbarOptions(level, 'level', ((0, 'Default'), (1, 'Combined')), 'app:table_teams', None)
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, self.editTarget, None, None, True, True, False, toolbar)

        self.html.add('<p><span class="h1">Table of Teams</span></p>')

        # Display a dates selector.
        startDate, finishDate = self.displaySelectDates('table_teams', cndb, parameters)

        self.html.add('<fieldset style="display: inline-block; vertical-align: top;"><legend>')
        if startDate is None or finishDate is None:
            self.html.add('All Time Table')
        else:
            self.html.add(f'Between {startDate} and {finishDate}')
        self.html.addLine('</legend>')

        sql = "SELECT TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR FROM ("

        # Summerise all the results.
        sql += "SELECT HOME_TEAM_ID AS TEAM_ID, SUM(HOME_WINS) AS HOME_WINS, SUM(HOME_DRAWS) AS HOME_DRAWS, SUM(HOME_LOSES) AS HOME_LOSES, SUM(HOME_FOR) AS HOME_FOR, SUM(HOME_AGAINST) AS HOME_AGAINST, SUM(AWAY_WINS) AS AWAY_WINS, SUM(AWAY_DRAWS) AS AWAY_DRAWS, SUM(AWAY_LOSES) AS AWAY_LOSES, SUM(AWAY_FOR) AS AWAY_FOR, SUM(AWAY_AGAINST) AS AWAY_AGAINST FROM ("

        # Summerise the home results.
        sql += "SELECT HOME_TEAM_ID, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS HOME_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS HOME_DRAWS, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS HOME_LOSES, SUM(HOME_TEAM_FOR) AS HOME_FOR, SUM(AWAY_TEAM_FOR) AS HOME_AGAINST, 0 AS AWAY_WINS, 0 AS AWAY_DRAWS, 0 AS AWAY_LOSES, 0 AS AWAY_FOR, 0 AS AWAY_AGAINST FROM MATCHES "
        if startDate is None or finishDate is None:
            pass
        else:
            # Between dates.
            sql += f"WHERE THE_DATE >= '{startDate}' AND THE_DATE <= '{finishDate}' "
        sql += "GROUP BY HOME_TEAM_ID "
        sql += "UNION "
        # Summeries the away results.
        sql += "SELECT AWAY_TEAM_ID, 0, 0, 0, 0, 0, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS AWAY_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS AWAY_DRAWS, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS AWAY_LOSES, SUM(AWAY_TEAM_FOR) AS AWAY_FOR, SUM(HOME_TEAM_FOR) AS AWAY_AGAINST FROM MATCHES "
        if startDate is None or finishDate is None:
            pass
        else:
            # Between dates.
            sql += f"WHERE THE_DATE >= '{startDate}' AND THE_DATE <= '{finishDate}' "
        sql += "GROUP BY AWAY_TEAM_ID) "
        sql += "GROUP BY HOME_TEAM_ID) "
        sql += "ORDER BY PTS DESC, DIFF DESC, FOR DESC; "
        # print(sql)

        self.displayTable(cndb, sql, level == 1, False, False, None, 0, False)
        self.html.addLine('</fieldset>')

        # Close the database.
        cndb.close()

        # Set the page flags.
        self.nextPagePage = None
        self.previousPage = None



    def showTableLast(self, parameters):
        ''' Show a table of team last (5) results. '''
        lastResults = int(parameters['last']) if 'last' in parameters else 5
        seasonIndex = int(parameters['season']) if 'season' in parameters else 1
        theDate = datetime.date(*time.strptime(parameters['date'], "%Y-%m-%d")[:3]) if 'date' in parameters else datetime.date.today()
        level = int(parameters['level']) if 'level' in parameters else 0

        # Check the the date is in season range.
        season = self.database.getSeason(seasonIndex)
        if theDate > season.finishDate:
            theDate = season.finishDate
        self.html.clear()
        toolbar = self.buildToolbarOptions(level, 'level', ((0, 'Default'), (1, 'Combined')), 'app:table_last', (('date', theDate), ('season', seasonIndex) ))
        if theDate is None:
            self.editTarget = f'edit_date?season={seasonIndex}'
        else:
            self.editTarget = f'edit_date?season={seasonIndex}&date={theDate}'
        if season.getPreviousSeasonIndex() is None:
            previousSeason = None
        else:
            previousSeason = f'table_last?season={season.getPreviousSeasonIndex()}'
        if season.getNextSeasonIndex() is None:
            nextSeason = None
        else:
            nextSeason = f'table_last?season={season.getNextSeasonIndex()}'
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, self.editTarget, previousSeason, nextSeason, False, True, False, toolbar)

        self.html.add(f'<p><span class="h1">{season.name} Last {lastResults} Results</span>')
        self.html.add(f' <span class="label">from</span> {self.database.formatDate(season.startDate)} <span class="label">to</span> {self.database.formatDate(season.finishDate)}.')
        links = season.getLinks()
        if season.comments is not None or len(links) > 0:
            #self.html.add('<p>')
            if season.comments is not None:
                self.html.add(' {}'.format(team.comments))
            if len(links) > 0:
                self.html.add(' <span class="label">More information at</span>')
                count = 0
                for linkLabel in links:
                    count += 1
                    if count == 1:
                        self.html.add(' ')
                    elif count == len(links):
                        self.html.add(' <span class="label">and</span> ')
                    else:
                        self.html.add('<span class="label">,</span> ')
                    self.html.add('<a href="{}">{}</a>'.format(links[linkLabel], linkLabel))
                self.html.add('. ')
            #self.html.add('</p>')
        self.html.addLine('</p>')

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        # Build a temporary table with the last results for each team.
        cndb.execute("DROP TABLE IF EXISTS temp.LAST_RESULTS;")
        cndb.execute("CREATE TEMP TABLE LAST_RESULTS (TEAM_ID INTEGER, HOME_WIN INTEGER, HOME_DRAW INTEGER, HOME_LOSE INTEGER, HOME_FOR INTEGER, HOME_AGN INTEGER, AWAY_WIN INTEGER, AWAY_DRAW INTEGER, AWAY_LOSE INTEGER, AWAY_FOR INTEGER, AWAY_AGN INTEGER);")

        # Find the teams in the season.
        sql = f"SELECT HOME_TEAM_ID FROM MATCHES WHERE SEASON_ID = {seasonIndex} GROUP BY HOME_TEAM_ID;"
        cursor = cndb.execute(sql)
        teams = []
        for row in cursor:
            teams.append(row[0])
        cursor.close()

        for teamIndex in teams:
            homeWins = 0
            homeDraw = 0
            homeLost = 0
            homeFor = 0
            homeAgn = 0
            awayWins = 0
            awayDraw = 0
            awayLost = 0
            awayFor = 0
            awayAgn = 0

            sql = f"SELECT HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE (HOME_TEAM_ID = {teamIndex} OR AWAY_TEAM_ID = {teamIndex}) AND THE_DATE <= '{theDate}' ORDER BY THE_DATE DESC LIMIT 5;";
            # print(sql)
            cursor = cndb.execute(sql)
            count = 0
            pts = 0
            for row in cursor:
                if row[0] == teamIndex:
                    # Home Match.
                    homeFor += row[2]
                    homeAgn += row[3]
                    if row[2] == row[3]:
                        homeDraw += 1
                    elif row[2] > row[3]:
                        homeWins += 1
                    else:
                        homeLost += 1
                else:
                    # Away Match.
                    awayFor += row[3]
                    awayAgn += row[2]
                    if row[2] == row[3]:
                        awayDraw += 1
                    elif row[2] < row[3]:
                        awayWins += 1
                    else:
                        awayLost += 1
            cursor.close()

            sql = f"INSERT INTO temp.LAST_RESULTS (TEAM_ID, HOME_WIN, HOME_DRAW, HOME_LOSE, HOME_FOR, HOME_AGN, AWAY_WIN, AWAY_DRAW, AWAY_LOSE, AWAY_FOR, AWAY_AGN) VALUES({teamIndex}, {homeWins}, {homeDraw}, {homeLost}, {homeFor}, {homeAgn}, {awayWins}, {awayDraw}, {awayLost}, {awayFor}, {awayAgn});"
            # print(sql)
            cndb.execute(sql)
            cndb.commit()

        self.html.add('<fieldset style="display: inline-block; vertical-align: top;"><legend>')
        if theDate is None:
            self.html.add('Final Table')
        else:
            self.html.add(f'Table to {self.database.formatDate(theDate)}')
        self.html.addLine('</legend>')

        sql = "SELECT TEAM_ID, HOME_WIN, HOME_DRAW, HOME_LOSE, HOME_FOR, HOME_AGN, AWAY_WIN, AWAY_DRAW, AWAY_LOSE, AWAY_FOR, AWAY_AGN, 3 * (HOME_WIN + AWAY_WIN) + (HOME_DRAW + AWAY_DRAW) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGN - AWAY_AGN AS DIFF FROM temp.LAST_RESULTS ORDER BY PTS DESC, DIFF DESC;"

        #sql = "SELECT HOME_TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR FROM "
        #sql += "(SELECT HOME_TEAM_ID, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS HOME_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS HOME_DRAWS, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS HOME_LOSES, SUM(HOME_TEAM_FOR) AS HOME_FOR, SUM(AWAY_TEAM_FOR) AS HOME_AGAINST FROM MATCHES "
        #if theDate is None:
        #    # All Results
        #    sql += f"WHERE SEASON_ID = {seasonIndex} GROUP BY HOME_TEAM_ID) AS HOME_RESULTS "
        #else:
        #    # Up to the date.
        #    sql += f"WHERE SEASON_ID = {seasonIndex} AND THE_DATE <= '{theDate}' GROUP BY HOME_TEAM_ID) AS HOME_RESULTS "
        #sql += "INNER JOIN "
        #sql += "(SELECT AWAY_TEAM_ID, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS AWAY_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS AWAY_DRAWS, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS AWAY_LOSES, SUM(AWAY_TEAM_FOR) AS AWAY_FOR, SUM(HOME_TEAM_FOR) AS AWAY_AGAINST FROM MATCHES "
        #if theDate is None:
        #    # All Results.
        #    sql += f"WHERE SEASON_ID = {seasonIndex} GROUP BY AWAY_TEAM_ID) AS AWAY_RESULTS "
        #else:
        #    # Update to the date.
        #    sql += f"WHERE SEASON_ID = {seasonIndex} AND THE_DATE <= '{theDate}' GROUP BY AWAY_TEAM_ID) AS AWAY_RESULTS "
        #sql += "ON HOME_RESULTS.HOME_TEAM_ID = AWAY_RESULTS.AWAY_TEAM_ID "
        #sql += "ORDER BY PTS DESC, DIFF DESC, FOR DESC; "
        # print(sql)
        # sql .= "USING (TEAM_ID);"

        self.displayTable(cndb, sql, level == 1, False, False, season.finishDate if theDate is None else theDate, 5, False)
        self.html.addLine('</fieldset>')

        self.html.add('<fieldset style="display: inline-block; vertical-align: top;"><legend>')
        if theDate is None:
            self.html.add('Final Matches')
        else:
            self.html.add(f'Matches to {self.database.formatDate(theDate)}')
        self.html.addLine('</legend>')
        self.html.addLine('<table>')
        if theDate is None:
            # All Results.
            sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, REAL_HOME_TEAM_FOR, REAL_AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = ? ORDER BY THE_DATE DESC LIMIT 20;"
            params = (seasonIndex, )
        else:
            # Results up to date.
            sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, REAL_HOME_TEAM_FOR, REAL_AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = ? AND THE_DATE <= ? ORDER BY THE_DATE DESC LIMIT 20;"
            params = (seasonIndex, theDate)

        cursor = cndb.execute(sql, params)
        lastDate = None
        for row in cursor:
            theMatchDate = datetime.date(*time.strptime(row[0], "%Y-%m-%d")[:3])
            formatMatchDate = self.database.formatDate(theMatchDate)
            isDateGuess = row[1] == 1
            if isDateGuess:
                formatMatchDate = f'({row[0]})'
            homeTeam = self.database.getTeam(row[2])
            awayTeam = self.database.getTeam(row[3])

            if lastDate != row[0]:
                if lastDate is None:
                    self.html.add('<tr>')
                else:
                    self.html.add('<tr style="border-top: 1px solid black;">')
                self.html.add(f'<td class="date" style="text-align: center;"><a href="app:table_last?season={seasonIndex}&date={row[0]}">{formatMatchDate}</a></td>')
                lastDate = row[0]
            else:
                self.html.add('<tr>')
                self.html.add('<td></td>')
            self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
            whatIf = ''
            if row[6] != row[4] or row[7] != row[5]:
                whatIf = ' class="win"'
            self.html.add(f'<td{whatIf}>{row[4]}</td>')
            self.html.add(f'<td{whatIf}>{row[5]}</td>')
            self.html.add(f'<td>{awayTeam.toHtml()}</td>')
            self.html.addLine('</tr>')

        self.html.addLine('</table>')
        self.html.addLine('</fieldset>')

        # Future matches.
        if theDate is not None:
            self.html.add('<fieldset style="display: inline-block; vertical-align: top;"><legend>')
            self.html.add(f'Matches after {self.database.formatDate(theDate)}')
            self.html.addLine('</legend>')
            self.html.addLine('<table>')
            # Results after to date.
            sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, REAL_HOME_TEAM_FOR, REAL_AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = ? AND THE_DATE > ? ORDER BY THE_DATE LIMIT 20;"
            params = (seasonIndex, theDate)

            cursor = cndb.execute(sql, params)
            for row in cursor:
                self.html.add('<tr>')
                theMatchDate = row[0]
                isDateGuess = row[1] == 1
                if isDateGuess:
                    theMatchDate = f'({row[0]})'
                homeTeam = self.database.getTeam(row[2])
                awayTeam = self.database.getTeam(row[3])

                self.html.add(f'<td class="date" style="text-align: center;"><a href="app:table_last?season={seasonIndex}&date={row[0]}">{theMatchDate}</a></td>')
                self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
                whatIf = ''
                if row[6] != row[4] or row[7] != row[5]:
                    whatIf = ' class="win"'
                self.html.add(f'<td{whatIf}>{row[4]}</td>')
                self.html.add(f'<td{whatIf}>{row[5]}</td>')
                self.html.add(f'<td>{awayTeam.toHtml()}</td>')
                self.html.addLine('</tr>')

            self.html.addLine('</table>')
            self.html.addLine('</fieldset>')

        # Close the database.
        cndb.close()

        # Set the page flags.
        self.levels = None
        self.clipboardText = None



    def showTableSubset(self, parameters):
        ''' Show a table of a subset of the teams. '''
        #seasonIndex = int(parameters['season']) if 'season' in parameters else 1
        #theDate = datetime.date(*time.strptime(parameters['date'], "%Y-%m-%d")[:3]) if 'date' in parameters else datetime.date.today()

        #season = self.database.getSeason(seasonIndex)

        #if season.getPreviousSeasonIndex() is None:
        #    previousSeason = None
        #else:
        #    previousSeason = f'table_subset?season={season.getPreviousSeasonIndex()}'
        #if season.getNextSeasonIndex() is None:
        #    nextSeason = None
        #else:
        #    nextSeason = f'table_subset?season={season.getNextSeasonIndex()}'

        self.html.clear()
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, None, None, None, False, False, False)
        self.html.add(f'<p><span class="h1">Subset of Teams</span></p>')

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        # Display a dates selector.
        if not 'date_type' in parameters:
            parameters['date_type'] = -1
        startDate, finishDate = self.displaySelectDates('table_subset', cndb, parameters)
        self.html.addLine('<br />')
        if startDate is None:
            startDate = '2022-08-06'
        if finishDate is None:
            finishDate = datetime.date.today()

        if 'exclude' in parameters:
            sql = f"UPDATE TEAMS SET SUB_GROUP = 0 WHERE ID = {parameters['exclude']}"
            cndb.execute(sql)
            cndb.commit()
        if 'include' in parameters:
            sql = f"UPDATE TEAMS SET SUB_GROUP = 1 WHERE ID = {parameters['include']}"
            cndb.execute(sql)
            cndb.commit()

        self.html.add('<fieldset style="display: inline-block; vertical-align: top;"><legend>')
        self.html.add(f'Table between {startDate} and {finishDate}')
        self.html.addLine('</legend>')

        sql = "SELECT TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR FROM ("

        # Summerise all the results.
        sql += "SELECT TEAM_ID, SUM(HOME_WINS) AS HOME_WINS, SUM(HOME_DRAWS) AS HOME_DRAWS, SUM(HOME_LOSES) AS HOME_LOSES, SUM(HOME_FOR) AS HOME_FOR, SUM(HOME_AGAINST) AS HOME_AGAINST, SUM(AWAY_WINS) AS AWAY_WINS, SUM(AWAY_DRAWS) AS AWAY_DRAWS, SUM(AWAY_LOSES) AS AWAY_LOSES, SUM(AWAY_FOR) AS AWAY_FOR, SUM(AWAY_AGAINST) AS AWAY_AGAINST FROM ("

        # Summerise all the home results.
        sql += "SELECT HOME_TEAM_ID AS TEAM_ID, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS HOME_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS HOME_DRAWS, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS HOME_LOSES, SUM(HOME_TEAM_FOR) AS HOME_FOR, SUM(AWAY_TEAM_FOR) AS HOME_AGAINST, 0 AS AWAY_WINS, 0 AS AWAY_DRAWS, 0 AS AWAY_LOSES, 0 AS AWAY_FOR, 0 AS AWAY_AGAINST FROM MATCHES INNER JOIN TEAMS AS HOME_TEAM ON MATCHES.HOME_TEAM_ID = HOME_TEAM.ID  INNER JOIN TEAMS AS AWAY_TEAM ON MATCHES.AWAY_TEAM_ID = AWAY_TEAM.ID "

        sql += f"WHERE THE_DATE >= '{startDate}' AND THE_DATE <= '{finishDate}' AND HOME_TEAM.SUB_GROUP = 1 AND AWAY_TEAM.SUB_GROUP = 1 GROUP BY HOME_TEAM_ID "

        sql += "UNION "
        # Summerise all the away results.
        sql += "SELECT AWAY_TEAM_ID AS TEAM_ID, 0 AS AWAY_WINS, 0 AS AWAY_DRAWS, 0 AS AWAY_LOSES, 0 AS AWAY_FOR, 0 AS AWAY_AGAINST, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS AWAY_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS AWAY_DRAWS, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS AWAY_LOSES, SUM(AWAY_TEAM_FOR) AS AWAY_FOR, SUM(HOME_TEAM_FOR) AS AWAY_AGAINST FROM MATCHES INNER JOIN TEAMS AS HOME_TEAM ON MATCHES.HOME_TEAM_ID = HOME_TEAM.ID  INNER JOIN TEAMS AS AWAY_TEAM ON MATCHES.AWAY_TEAM_ID = AWAY_TEAM.ID "

        sql += f"WHERE THE_DATE >= '{startDate}' AND THE_DATE <= '{finishDate}' AND HOME_TEAM.SUB_GROUP = 1 AND AWAY_TEAM.SUB_GROUP = 1 GROUP BY AWAY_TEAM_ID "

        sql += ") GROUP BY TEAM_ID) "
        sql += "ORDER BY PTS DESC, DIFF DESC, FOR DESC; "

        # print(sql)

        self.displayTable(cndb, sql, False, False, False, None, 0, False)
        self.html.addLine('</fieldset>')

        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;">')
        self.html.addLine('<legend>Included</legend>')
        sql = "SELECT ID, LABEL FROM TEAMS WHERE SUB_GROUP = 1 ORDER BY LABEL;"
        cursor = cndb.execute(sql)
        for row in cursor:
            self.html.addLine(f'<p><a href="app:table_subset?start_date={startDate}&finish_date={finishDate}&exclude={row[0]}">{row[1]}</a></p>')
        self.html.addLine('</fieldset>')

        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;">')
        self.html.addLine('<legend>Excluded</legend>')
        sql = "SELECT ID, LABEL FROM TEAMS WHERE SUB_GROUP = 0 ORDER BY LABEL;"
        cursor = cndb.execute(sql)
        for row in cursor:
            self.html.addLine(f'<p><a href="app:table_subset?start_date={startDate}&finish_date={finishDate}&&include={row[0]}">{row[1]}</a></p>')
        self.html.addLine('</fieldset>')

        # Close the database.
        cndb.close()

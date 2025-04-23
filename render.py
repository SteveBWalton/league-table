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
        # A default height for the distribution graph.
        self.maxDistributionCount = 10

        # Define the actions this module can handle and the function to handle the action.
        self.actions = {
            'home'              : self.showHome,
            'index'             : self.showIndex,
            'preferences'       : self.showPreferences,
            'show_team'         : self.showTeam,
            'head'              : self.showHeadToHead,
            'table_teams'       : self.showTableTeams,
            'table_last'        : self.showTableLast,
            'table_subset'      : self.showTableSubset,
            'show_team_season'  : self.showTeamSeason
        }

        # Indentify the current last season.
        # TODO: Calculate this!
        self.lastSeasonIndex = 6



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



    def drawPossiblePointsBox(self, width, height, scaleMin, scaleMax, actualPoints, pointsEarned, gamesPlayed, remainingGames, safePoints, requiredPoints):
        '''
        Draws a svg graphical box to display the expected range of possible points.

        :param int width: Specifies the width of the box.  Default to 200.
        :param int height: Specifies the height of the box.  Default to 18.
        :param int scaleMin: Specifies the miniumn number of points on the scale.
        :param int scaleMax: Specifies the maximum number of points on the scale.
        :param int actualPoints: Specifies the number of points that the team actually has.
        :param int pointsEarned: Specifies the number of points that the team has earned.
        :param int gamesPlayed: Specifies the number games played.
        :param int remainingGames: Specifies the number of games to be played.
        :param real safePoints: Specifies the expected miniumn numbers of points to be safe.
        :param real requirePoints: Specifies the expected miniumn number of points required.
        '''
        # print(f'{actualPoints} {pointsEarned}')
        pointsPerGame = pointsEarned / gamesPlayed

        # Start a svg control.
        self.html.add(f'<svg class="wdlbox" width="{width}" height="{height}" style="vertical-align: middle;">')

        # Draw the possible points in yellow.
        if False:
            pixMinimum = int(round(width * (actualPoints - scaleMin) / (scaleMax - scaleMin), 0))
            pixMaximum = int(round(width * (actualPoints + 3 * remainingGames - scaleMin) / (scaleMax - scaleMin), 0))
            self.html.add(f'<rect class="wdlbox_draw" x="{pixMinimum}" y="0" width="{pixMaximum - pixMinimum}" height="{height}" style="stroke-width: 0; stroke: rgb(0, 0, 0);" />')

        # Draw the confidence interval points in green.
        if False:
            # System One.
            lowerPointsPerGame = pointsPerGame / 2
            upperPointsPerGame = (3 + pointsPerGame) / 2
            confidenceMinPoints = actualPoints + lowerPointsPerGame * remainingGames
            confidenceMaxPoints = actualPoints + upperPointsPerGame * remainingGames
        elif False:
            # System Two
            if remainingGames <= 2:
                confidenceMinPoints = actualPoints
                confidenceMaxPoints = actualPoints + remainingGames * 3
            else:
                lowerPointsPerGame = max(0, pointsPerGame - 0.5)
                upperPointsPerGame = min(3, pointsPerGame + 0.5)
                confidenceMinPoints = actualPoints + lowerPointsPerGame  * (remainingGames - 2)
                confidenceMaxPoints = actualPoints + 6 + upperPointsPerGame * (remainingGames - 2)
        else:
            # System Three.
            if remainingGames <= 2:
                confidenceMinPoints = actualPoints
                confidenceMaxPoints = actualPoints + remainingGames * 3
            else:
                lowerPointsPerGame = pointsPerGame / 2
                upperPointsPerGame = (3 + pointsPerGame) / 2
                confidenceMinPoints = actualPoints + lowerPointsPerGame  * (remainingGames - 2)
                confidenceMaxPoints = actualPoints + 6 + upperPointsPerGame * (remainingGames - 2)
        pixMinimum = int(round(width * (confidenceMinPoints - scaleMin) / (scaleMax - scaleMin), 0))
        pixMaximum = int(round(width * (confidenceMaxPoints - scaleMin) / (scaleMax - scaleMin), 0))
        self.html.add(f'<rect class="wdlbox_win" x="{pixMinimum}" y="0" width="{pixMaximum - pixMinimum}" height="{height}" style="stroke-width: 0; stroke: rgb(0, 0, 0);" />')

        # Border.
        self.html.add('<rect class="wdlbox" width="{}" height="{}" style="fill: none; stroke-width: 2;" />'.format(width, height))
        # Draw a tick mark at safe point points.
        if safePoints > 0:
            tickPos = int(round(width * (safePoints - scaleMin) / (scaleMax - scaleMin), 0))
            self.html.add(f'<line class="wdlbox" x1="{tickPos}" y1="0" x2="{tickPos}" y2="4" style="stroke-width: 1;" />')
            self.html.add(f'<line class="wdlbox" x1="{tickPos}" y1="{height}" x2="{tickPos}" y2="{height - 4}" style="stroke-width: 1;" />')
        # Draw a tick mark at required points.
        if requiredPoints > 0:
            tickPos = int(round(width * (requiredPoints - scaleMin) / (scaleMax - scaleMin), 0))
            self.html.add(f'<line class="wdlbox" x1="{tickPos}" y1="0" x2="{tickPos}" y2="4" style="stroke-width: 1;" />')
            self.html.add(f'<line class="wdlbox" x1="{tickPos}" y1="{height}" x2="{tickPos}" y2="{height - 4}" style="stroke-width: 1;" />')
        # Draw a line at expected points.
        expectedPoints = actualPoints + pointsPerGame * remainingGames
        # tickPos = int(round(width * ((gamesPlayed + remainingGames) * (pointsEarned / gamesPlayed) - scaleMin) / (scaleMax - scaleMin), 0))
        tickPos = int(round(width * (expectedPoints - scaleMin) / (scaleMax - scaleMin), 0))
        self.html.add(f'<line class="wdlbox" x1="{tickPos}" y1="0" x2="{tickPos}" y2="{height}" style="stroke-width: 2;" />')

        if True:
            # Draw error bars not yellow zone.
            pixAbsMinimum = int(round(width * (actualPoints - scaleMin) / (scaleMax - scaleMin), 0))
            pixAbsMaximum = int(round(width * (actualPoints + 3 * remainingGames - scaleMin) / (scaleMax - scaleMin), 0))
            # self.html.add(f'<rect class="wdlbox_draw" x="{pixMinimum}" y="0" width="{pixMaximum - pixMinimum}" height="{height}" style="stroke-width: 0; stroke: rgb(0, 0, 0);" />')
            minY = int(round(height / 2, 0))
            self.html.add(f'<line class="wdlbox" x1="{pixAbsMinimum}" y1="{height / 4}" x2="{pixAbsMinimum}" y2="{height * 3 / 4}" style="stroke-width: 2;" />')
            self.html.add(f'<line class="wdlbox" x1="{pixAbsMinimum}" y1="{minY}" x2="{pixMinimum}" y2="{minY}" style="stroke-width: 2;" />')
            self.html.add(f'<line class="wdlbox" x1="{pixMinimum}" y1="{0}" x2="{pixMinimum}" y2="{height}" style="stroke-width: 2;" />')

            self.html.add(f'<line class="wdlbox" x1="{pixAbsMaximum}" y1="{height / 4}" x2="{pixAbsMaximum}" y2="{height * 3 / 4}" style="stroke-width: 2;" />')
            self.html.add(f'<line class="wdlbox" x1="{pixAbsMaximum}" y1="{minY}" x2="{pixMaximum}" y2="{minY}" style="stroke-width: 2;" />')
            self.html.add(f'<line class="wdlbox" x1="{pixMaximum}" y1="{0}" x2="{pixMaximum}" y2="{height}" style="stroke-width: 2;" />')

        self.html.addLine('</svg>')



    def displayTable(self, cndb, sql, season, isCombinedHomeAway, isAddColour, isShowRange, theDate, lastResults, isBySeason, extraInfo=0):
        '''
        Display a table on the html object.
        The fields from the sql should be
         0 Team Name
         1 Home Wins
         2 Home Draws
         3 Home Loses
         4 Home For
         5 Home Against
         6 Away Wins
         7 Away Draws
         8 Away Loses
         9 Away For
        10 Away Against
        11 Pts (including bonus pts)
        12 Goal Difference
        13 Goals For
        14 Bonus Pts
        15 Season ID
        '''
        if isShowRange:
            isShowPossiblePoints = False
            cursor = cndb.execute(sql)
            count = 0
            minPoints = 0
            maxPoints = 0
            safePoints = 0
            requiredPoints = 0
            arrayPoints = []
            for row in cursor:
                count += 1
                played = row[1] + row[2] + row[3] + row[6] + row[7] + row[8]
                if played < season.numMatches:
                    isShowPossiblePoints = True
                teamMinPoints = row[11]
                remainingMatches = season.numMatches - played
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
                if count == season.badPos:
                    safePoints = (int)(math.ceil(season.numMatches * row[11] / played))
                elif count == season.badPos + 1:
                    safePoints = (int)(math.ceil((safePoints + (int)(math.ceil(season.numMatches * row[11] / played))) / 2))
                if count == season.goodPos:
                    requiredPoints = (int)(math.ceil(season.numMatches * row[11] / played))
                if count == season.goodPos + 1:
                    requiredPoints = (int)(math.ceil((requiredPoints + (int)(math.ceil(season.numMatches * row[11] / played))) / 2))
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
            if isAddColour and count < season.goodPos:
                self.html.add('<tr class="win2">')
            elif isAddColour and count < season.positivePos:
                self.html.add('<tr class="win3">')
            elif isAddColour and count >= season.badPos:
                self.html.add('<tr class="lost2">')
            else:
                self.html.add('<tr>')

            if isBySeason:
                season = self.database.getSeason(row[15])
                self.html.add(f'<td colspan="2" style="text-align: right;"><a href="app:show_team_season?team={extraInfo}&season={season.index}">{season.name}</a></td>')
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
                teamMaxPoints = teamMinPoints + (season.numMatches - played) * 3
                if teamMaxPoints > maxPoints:
                    maxPoints = teamMaxPoints
                # self.html.add(f'<td class="minor" style="text-align: right;">{teamMaxPoints}</td>')
                if count >= season.badPos:
                    self.html.add(f'<td title="Expected safe points are {safePoints}.">')
                elif count <= season.goodPos:
                    self.html.add(f'<td title="Expected required points are {requiredPoints}.">')
                else:
                    self.html.add('<td style="white-space: nowrap;">')

                # Debuging test the 2 box styles.
                if False:
                    self.drawPossiblePointsBox1(300, 18, teamMinPoints, teamMaxPoints, minPoints, maxPoints, season.numMatches * row[11] / played, safePoints, requiredPoints)
                else:
                    self.drawPossiblePointsBox(300, 18, minPoints, maxPoints, teamMinPoints, row[11] - row[14], played, (season.numMatches - played), safePoints, requiredPoints)

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
            lastSeason = self.database.getSeason(self.lastSeasonIndex)
            startDate = lastSeason.startDate
            finishDate = datetime.date.today()
        else:
            self.html.add('<option value="-1">This Season</option>')
        if dateType == -2:
            lastSeason = self.database.getSeason(self.lastSeasonIndex)
            previousSeason = self.database.getSeason(lastSeason.getPreviousSeasonIndex())
            self.html.add('<option value="0" selected="yes">Last Season</option>')
            startDate = previousSeason.startDate
            finishDate = previousSeason.finishDate
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
        seasonIndex = int(parameters['season']) if 'season' in parameters else self.lastSeasonIndex
        # if 'date' in parameters:
        #    print(parameters['date'])
        theDate = datetime.date(*time.strptime(parameters['date'], "%Y-%m-%d")[:3]) if 'date' in parameters else datetime.date.today()
        isRange = True
        # print(f'seasonIndex = {seasonIndex}, date = {theDate}')

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
                self.html.add(' {}'.format(season.comments))
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

        sql = "SELECT TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) + BONUS_PTS AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR, BONUS_PTS FROM ("

        # Summerise all the results.
        sql += "SELECT TEAM_ID, SUM(HOME_WINS) AS HOME_WINS, SUM(HOME_DRAWS) AS HOME_DRAWS, SUM(HOME_LOSES) AS HOME_LOSES, SUM(HOME_FOR) AS HOME_FOR, SUM(HOME_AGAINST) AS HOME_AGAINST, SUM(AWAY_WINS) AS AWAY_WINS, SUM(AWAY_DRAWS) AS AWAY_DRAWS, SUM(AWAY_LOSES) AS AWAY_LOSES, SUM(AWAY_FOR) AS AWAY_FOR, SUM(AWAY_AGAINST) AS AWAY_AGAINST, SUM(BONUS_PTS) AS BONUS_PTS FROM ("

        # Summerise all the home results.
        sql += "SELECT HOME_TEAM_ID AS TEAM_ID, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS HOME_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS HOME_DRAWS, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS HOME_LOSES, SUM(HOME_TEAM_FOR) AS HOME_FOR, SUM(AWAY_TEAM_FOR) AS HOME_AGAINST, 0 AS AWAY_WINS, 0 AS AWAY_DRAWS, 0 AS AWAY_LOSES, 0 AS AWAY_FOR, 0 AS AWAY_AGAINST, SUM(HOME_BONUS_PTS) AS BONUS_PTS FROM MATCHES "
        if theDate is None:
            # All season results
            sql += f"WHERE SEASON_ID = {seasonIndex} GROUP BY HOME_TEAM_ID "
        else:
            # Up to the date.
            sql += f"WHERE SEASON_ID = {seasonIndex} AND THE_DATE <= '{theDate}' GROUP BY HOME_TEAM_ID "
        sql += "UNION "
        # Summerise all the away results.
        sql += "SELECT AWAY_TEAM_ID AS TEAM_ID, 0 AS AWAY_WINS, 0 AS AWAY_DRAWS, 0 AS AWAY_LOSES, 0 AS AWAY_FOR, 0 AS AWAY_AGAINST, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS AWAY_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS AWAY_DRAWS, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS AWAY_LOSES, SUM(AWAY_TEAM_FOR) AS AWAY_FOR, SUM(HOME_TEAM_FOR) AS AWAY_AGAINST, SUM(AWAY_BONUS_PTS) AS BONUS_PTS FROM MATCHES "
        if theDate is None:
            # All season results.
            sql += f"WHERE SEASON_ID = {seasonIndex} GROUP BY AWAY_TEAM_ID  "
        else:
            # Update to the date.
            sql += f"WHERE SEASON_ID = {seasonIndex} AND THE_DATE <= '{theDate}' GROUP BY AWAY_TEAM_ID  "
        sql += ") GROUP BY TEAM_ID) "
        sql += "ORDER BY PTS DESC, DIFF DESC, FOR DESC; "

        # print(sql)

        self.displayTable(cndb, sql, season, level == 1, True, True, season.finishDate if theDate is None else theDate, 5, False)
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
            whatIf = ' class="goals"'
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
        self.html.addLine('<li><a href="app:preferences">Preferences</a></li>')
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
        self.html.addLine('<li><a href="app:table_subset">Table of Subset of Teams</a></li>')
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

        self.html.addLine('<div style="display: inline-block; vertical-align: top;">')

        # Show a season summary.
        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;"><legend>Seasons</legend>')
        sql = "SELECT HOME_TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) + HOME_BONUS_PTS + AWAY_BONUS_PTS AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR, HOME_BONUS_PTS + AWAY_BONUS_PTS AS TOTAL_BONUS_PTS, HOME_RESULTS.SEASON_ID, HOME_RESULTS.MAX_DATE FROM "
        sql += "(SELECT HOME_TEAM_ID, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS HOME_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS HOME_DRAWS, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS HOME_LOSES, SUM(HOME_TEAM_FOR) AS HOME_FOR, SUM(AWAY_TEAM_FOR) AS HOME_AGAINST, SEASON_ID, MAX(THE_DATE) AS MAX_DATE, SUM(HOME_BONUS_PTS) AS HOME_BONUS_PTS FROM MATCHES "
        sql += f"WHERE HOME_TEAM_ID = {teamIndex} AND THE_DATE >= '{startDate}' AND THE_DATE <= '{theDate}' GROUP BY SEASON_ID) AS HOME_RESULTS "
        sql += "INNER JOIN "
        sql += "(SELECT AWAY_TEAM_ID, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS AWAY_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS AWAY_DRAWS, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS AWAY_LOSES, SUM(AWAY_TEAM_FOR) AS AWAY_FOR, SUM(HOME_TEAM_FOR) AS AWAY_AGAINST, SEASON_ID, MAX(THE_DATE) AS MAX_DATE, SUM(AWAY_BONUS_PTS) AS AWAY_BONUS_PTS FROM MATCHES "
        sql += f"WHERE AWAY_TEAM_ID = {teamIndex} AND THE_DATE >= '{startDate}' AND THE_DATE <= '{theDate}' GROUP BY SEASON_ID) AS AWAY_RESULTS "
        sql += "ON HOME_RESULTS.SEASON_ID = AWAY_RESULTS.SEASON_ID "
        # sql += "ORDER BY HOME_RESULTS.SEASON_ID DESC;"
        sql += "ORDER BY HOME_RESULTS.MAX_DATE DESC;"

        self.displayTable(cndb, sql, None, False, False, False, None, 0, True, teamIndex)
        self.html.addLine('</fieldset>')
        self.html.addLine('<br />')

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
            self.html.add(f'<td class="goals">{row[4]}</td>')
            self.html.add(f'<td class="goals">{row[5]}</td>')
            self.html.add(f'<td>{awayTeam.toHtml()}</td>')
            self.html.add(f'<td title="Head to Head"><a href="app:head?team1={teamIndex}&team2={homeTeam.index if homeTeam.index != teamIndex else awayTeam.index}&date={theMatchDate}"><i class="fas fa-user"></i></a></td>')

            # Don't really want this here.  It is confusing.
            self.html.add(f'<td title="League Table"><a href="app:home?season={row[6]}&date={theMatchDate}"><i class="fas fa-chart-line"></i></i></td>')

            self.html.addLine('</tr>')

        self.html.addLine('</table>')
        self.html.addLine('</fieldset>')

        # Start a second column.
        self.html.addLine('</div>')
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

        # summaryType = 2
        for summaryType in range(2):
            if summaryType == 1:
                self.html.addLine('<br />')
                self.html.addLine(f'<fieldset style="display: inline-block; vertical-align: top;"><legend>Summary Points against {team.name}</legend>')
            else:
                self.html.addLine(f'<fieldset style="display: inline-block; vertical-align: top;"><legend>Summary Points for {team.name}</legend>')

            # Points that teams have score against this team.
            sql = "SELECT TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR, 0 AS BONUS_PTS FROM ("

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

            self.displayTable(cndb, sql, None, False, False, False, None, 0, False)
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
        sql = "SELECT HOME_TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR, 0 AS BONUS_PTS FROM "
        sql += "(SELECT HOME_TEAM_ID, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS HOME_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS HOME_DRAWS, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS HOME_LOSES, SUM(HOME_TEAM_FOR) AS HOME_FOR, SUM(AWAY_TEAM_FOR) AS HOME_AGAINST FROM MATCHES "
        sql += f"WHERE ((HOME_TEAM_ID = {team1Index} AND AWAY_TEAM_ID = {team2Index}) OR (HOME_TEAM_ID = {team2Index} AND AWAY_TEAM_ID = {team1Index})) AND THE_DATE <= '{theDate}' "
        sql += "GROUP BY HOME_TEAM_ID) AS HOME_RESULTS "
        sql += "INNER JOIN "
        sql += "(SELECT AWAY_TEAM_ID, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS AWAY_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS AWAY_DRAWS, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS AWAY_LOSES, SUM(AWAY_TEAM_FOR) AS AWAY_FOR, SUM(HOME_TEAM_FOR) AS AWAY_AGAINST FROM MATCHES "
        sql += f"WHERE ((HOME_TEAM_ID = {team2Index} AND AWAY_TEAM_ID = {team1Index}) OR (HOME_TEAM_ID = {team1Index} AND AWAY_TEAM_ID = {team2Index})) AND THE_DATE <= '{theDate}' "
        sql += "GROUP BY AWAY_TEAM_ID) AS AWAY_RESULTS "
        sql += "ON HOME_RESULTS.HOME_TEAM_ID = AWAY_RESULTS.AWAY_TEAM_ID "
        sql += "ORDER BY PTS DESC, DIFF DESC, FOR DESC; "
        self.displayTable(cndb, sql, None, False, False, False, None, 0, False)
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
            season = self.database.getSeason(row[6])
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
            self.html.add(f'<td class="date" style="white-space: nowrap;">{season.toHtml()}</td>')
            self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
            self.html.add(f'<td class="goals">{row[4]}</td>')
            self.html.add(f'<td class="goals">{row[5]}</td>')
            self.html.add(f'<td>{awayTeam.toHtml()}</td>')
            self.html.addLine('</tr>')

        self.html.addLine('</table>')
        self.html.addLine('</fieldset>')

        # Show future matches.
        isFirst = True
        sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, SEASON_ID FROM MATCHES WHERE ((HOME_TEAM_ID = ? AND AWAY_TEAM_ID = ?) OR (HOME_TEAM_ID = ? AND AWAY_TEAM_ID = ?)) AND THE_DATE > ? ORDER BY THE_DATE DESC;"
        params = (team1Index, team2Index, team2Index, team1Index, theDate)
        cursor = cndb.execute(sql, params)
        for row in cursor:
            if isFirst:
                self.html.addLine('<fieldset><legend>Future Matches</legend>')
                self.html.addLine('<table>')
                isFirst = False
            theMatchDate = datetime.date(*time.strptime(row[0], "%Y-%m-%d")[:3])
            formatMatchDate = self.database.formatDate(theMatchDate)
            isDateGuess = row[1] == 1
            if isDateGuess or theMatchDate > datetime.date.today():
                formatMatchDate = f'({row[0]})'
            homeTeam = self.database.getTeam(row[2])
            awayTeam = self.database.getTeam(row[3])
            season = self.database.getSeason(row[6])
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
            self.html.add(f'<td class="date" style="white-space: nowrap;">{season.toHtml()}</td>')
            self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
            self.html.add(f'<td class="goals">{row[4]}</td>')
            self.html.add(f'<td class="goals">{row[5]}</td>')
            self.html.add(f'<td>{awayTeam.toHtml()}</td>')
            self.html.addLine('</tr>')
        if not isFirst:
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

        sql = "SELECT TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR, 0 AS BONUS_PTS FROM ("

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

        self.displayTable(cndb, sql, None, level == 1, False, False, None, 0, False)
        self.html.addLine('</fieldset>')

        # Close the database.
        cndb.close()

        # Set the page flags.
        self.nextPagePage = None
        self.previousPage = None



    def showTableLast(self, parameters):
        ''' Show a table of team last (5) results. '''
        lastResults = int(parameters['last']) if 'last' in parameters else 5
        seasonIndex = int(parameters['season']) if 'season' in parameters else 6
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
                self.html.add(' {}'.format(season.comments))
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

        sql = "SELECT TEAM_ID, HOME_WIN, HOME_DRAW, HOME_LOSE, HOME_FOR, HOME_AGN, AWAY_WIN, AWAY_DRAW, AWAY_LOSE, AWAY_FOR, AWAY_AGN, 3 * (HOME_WIN + AWAY_WIN) + (HOME_DRAW + AWAY_DRAW) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGN - AWAY_AGN AS DIFF, 0 AS BONUS_PTS FROM temp.LAST_RESULTS ORDER BY PTS DESC, DIFF DESC;"

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

        self.displayTable(cndb, sql, season, level == 1, False, False, season.finishDate if theDate is None else theDate, 5, False)
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
        self.html.clear()
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, None, None, None, False, False, False)
        self.html.add(f'<p><span class="h1">Subset of Teams</span></p>')

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        # Group the date selector and table.
        self.html.addLine('<div style="display: inline-block; vertical-align: top;">')

        # Display a dates selector.
        if not 'date_type' in parameters:
            parameters['date_type'] = -1
        startDate, finishDate = self.displaySelectDates('table_subset', cndb, parameters)
        self.html.addLine('<br />')
        if startDate is None:
            lastSeason = self.db.getSeason(self.lastSeasonIndex)
            startDate = lastSeason.startDate
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

        sql = "SELECT TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR, 0 AS BONUS_PTS FROM ("

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

        self.displayTable(cndb, sql, None, False, False, False, None, 0, False)
        self.html.addLine('</fieldset>')

        self.html.addLine('</div>')

        # Show the total points progress of the teams.
        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;">')
        self.html.addLine('<legend>Total Points</legend>')

        # Identify the teams.
        sql = "SELECT ID, LABEL FROM TEAMS WHERE SUB_GROUP = 1 ORDER BY LABEL;"
        includedTeams = []
        cursor = cndb.execute(sql)
        for row in cursor:
            includedTeams.append([row[0], row[1]])

        # Fetch their points.
        maxMatches = 1
        maxPoints = 1
        for team in includedTeams:


            '''
            sql = f"SELECT HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE (HOME_TEAM_ID = {team[0]} OR AWAY_TEAM_ID = {team[0]}) AND (THE_DATE >= '{startDate}' AND THE_DATE <= '{finishDate}') ORDER BY THE_DATE;"
            cursor = cndb.execute(sql)
            listPts = []
            totalPts = 0
            for row in cursor:
                if row[2] == row[3]:
                    pts = 1
                else:
                    if row[0] == team[0]:
                        if row[2] > row[3]:
                            pts = 3
                        else:
                            pts = 0
                    else:
                        if row[2] > row[3]:
                            pts = 0
                        else:
                            pts = 3
                totalPts += pts
                listPts.append(totalPts)
            '''
            listPts = self.database.getArrayTeamPts(team[0], startDate, finishDate)
            team.append(listPts)

            if len(listPts) > 0:
                if len(listPts) > maxMatches:
                    maxMatches = len(listPts)
                finalPoints = listPts[len(listPts) - 1]
                if finalPoints > maxPoints:
                    maxPoints = finalPoints

        # Sort teams into points order.
        includedTeams.sort(key=sortTeamsByFinalPoints, reverse=True)

        # Draw a graph.
        svgWidth = 700
        svgHeight = 500
        self.html.addLine(f'<svg width="{svgWidth}" height="{svgHeight}" style="vertical-align: top; border: 1px solid black;" xmlns="http://www.w3.org/2000/svg" version="1.1">')

        # Graph Area.
        top = 15
        bottom = 30
        left = 50
        right = 10

        width = svgWidth - left - right
        height = svgHeight - top - bottom

        self.html.addLine(f'<rect x="{left}" y="{top}" width="{width}" height="{height}" style="fill: white; stroke: black; stroke-width: 1;" />')

        # X Axis.
        xScale = width / maxMatches

        # Y Axis.
        yScale = height / (maxPoints + 0.5)

        # Draw the points.
        lineColours = ['red', 'blue', 'green', 'orange', 'hotpink', 'gray', 'brown', 'brown']
        teamCount = 0
        for team in includedTeams:
            x = left
            self.html.add(f'<polyline points="{x},{top + height} ')
            for pts in team[2]:
                x += xScale
                y = top + height - yScale * pts
                self.html.add(f'{x},{y} ')
            self.html.addLine(f'" style="fill: none; stroke: {lineColours[teamCount]}; stroke-width: 2;" />') # clip-path="url(#graph-area)"

            # Label the lines.
            y = top + 6 + 12 * teamCount
            self.html.addLine(f'<line x1="{left}" y1="{y}" x2="{left + 10}" y2="{y}" stroke="{lineColours[teamCount]}" />')
            self.html.addLine(f'<text text-anchor="start" font-size="8pt" x="{left + 12}" y="{y + 4}">{team[1]}</text>')

            teamCount += 1

        self.html.addLine('</svg>')
        self.html.addLine('</fieldset>')

        self.html.addLine('<br/>')

        # Calculate the max count across all the result type histograms.
        maxCount = 5
        for team in includedTeams:
            ignore, maxCount = self.getTypeResultsData(cndb, team[0], startDate, finishDate, -4, +4, maxCount)

        # Draw a graph of the type of results.
        for team in includedTeams:
            self.html.addLine(f'<fieldset style="display: inline-block; vertical-align: top;"><legend>{team[1]} Distribution</legend>')
            self.displayGraphTypeResults(cndb, team[0], startDate, finishDate, -4, +4, maxCount)
            self.html.addLine('</fieldset>')

        # Show the included teams and allow them to be removed.
        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;">')
        self.html.addLine('<legend>Included</legend>')
        for team in includedTeams:
            self.html.addLine(f'<p><a href="app:table_subset?start_date={startDate}&finish_date={finishDate}&exclude={team[0]}">{team[1]}</a></p>')
        self.html.addLine('</fieldset>')

        # Show the excluded teams and allow them to be added.
        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;">')
        self.html.addLine('<legend>Excluded</legend>')
        self.html.add('<p>')
        sql = "SELECT ID, LABEL FROM TEAMS WHERE SUB_GROUP = 0 ORDER BY LABEL;"
        sql = "SELECT ID, LABEL FROM TEAMS ORDER BY LABEL;"
        cursor = cndb.execute(sql)
        for row in cursor:
            self.html.add(f'<a href="app:table_subset?start_date={startDate}&finish_date={finishDate}&&include={row[0]}">{row[1]}</a>, ')
        self.html.addLine('<p>')
        self.html.addLine('</fieldset>')

        # Close the database.
        cndb.close()



    def showTeamSeason(self, parameters):
        '''
        Render the specified team in the specified season on the html object.
        '''
        # Decode the parameters.
        teamIndex = int(parameters['team']) if 'team' in parameters else 1
        seasonIndex = int(parameters['season']) if 'season' in parameters else self.lastSeasonIndex

        # Get the team object.
        team = self.database.getTeam(teamIndex)

        # Get the season object.
        season = self.database.getSeason(seasonIndex)

        # Initialise the display.
        self.html.clear()
        self.editTarget = ''
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, self.editTarget, None, None, True, True, False, '')

        self.html.add(f'<p><span class="h1">{team.name} in {season.name}</span></p>')

        # Decide the finish date.
        if datetime.date.today() < season.finishDate:
            finishDate = datetime.date.today()
        else:
            finishDate = season.finishDate

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        # Show the matches.
        lastTeamPlayedIdx = None
        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;"><legend>Matches</legend>')
        self.html.addLine('<table>')
        sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR, SEASON_ID FROM MATCHES WHERE (HOME_TEAM_ID = ? OR AWAY_TEAM_ID = ?) AND THE_DATE >= ? AND THE_DATE <= ? ORDER BY THE_DATE DESC;"
        params = (teamIndex, teamIndex, season.startDate, finishDate)
        cursor = cndb.execute(sql, params)
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
                lastTeamPlayedIdx = awayTeam.index
            else:
                if row[4] < row[5]:
                    className = 'win2'
                elif row[4] > row[5]:
                    className = 'lost2'
                else:
                    className = 'draw2'
                lastTeamPlayedIdx = homeTeam.index

            self.html.add(f'<tr class="{className}">')
            self.html.add(f'<td class="date" style="text-align: center;"><a href="app:show_team?id={teamIndex}&date={row[0]}">{formatMatchDate}</a></td>')
            self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
            self.html.add(f'<td class="goals">{row[4]}</td>')
            self.html.add(f'<td class="goals">{row[5]}</td>')
            self.html.add(f'<td>{awayTeam.toHtml()}</td>')
            self.html.add(f'<td title="Head to Head"><a href="app:head?team1={teamIndex}&team2={homeTeam.index if homeTeam.index != teamIndex else awayTeam.index}&date={theMatchDate}"><i class="fas fa-user"></i></a></td>')

            # Don't really want this here.  It is confusing.
            self.html.add(f'<td title="League Table"><a href="app:home?season={row[6]}&date={theMatchDate}"><i class="fas fa-chart-line"></i></i></td>')

            self.html.addLine('</tr>')

        self.html.addLine('</table>')
        self.html.addLine('</fieldset>')

        # Get the list of points for this team.
        listPts = self.database.getArrayTeamPts(teamIndex, season.startDate, finishDate)

        # Get the points for the other teams in the league.
        listTeams = self.database.getListTeams(season.startDate, finishDate)

        otherTeams = []
        for otherTeamIndex in listTeams:
            if otherTeamIndex != teamIndex:
                otherTeamListPts = self.database.getArrayTeamPts(otherTeamIndex, season.startDate, finishDate)
                otherTeams.append([otherTeamIndex, '', otherTeamListPts])

        numMatches = len(listPts)
        numPositions = len(listTeams)

        # Keep nonagram away from matches.
        self.html.addLine('<div style="display: inline-block; vertical-align: top;">')

        # Keep league position and match results in line.
        self.html.addLine('<div style="display: inline-block; vertical-align: top;">')

        # Draw a graph of league position.
        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;"><legend>League Position</legend>')

        # Draw a graph.
        boxWidth = 14
        boxHeight = 14
        svgWidth = season.numMatches * boxWidth
        svgHeight = numPositions * boxHeight
        self.html.addLine(f'<svg width="{svgWidth}" height="{svgHeight}" style="vertical-align: top; border: 1px solid black;" xmlns="http://www.w3.org/2000/svg" version="1.1">')

        width = svgWidth
        height = svgHeight
        # self.html.addLine(f'<rect x="{0}" y="{0}" width="{width}" height="{height}" style="fill: white; stroke: black; stroke-width: 1;" />')

        for matchIndex in range(numMatches):
            # Count the better positions.
            count = 1
            for otherTeam in otherTeams:
                otherTeamListPts = otherTeam[2]
                if len(otherTeamListPts) > matchIndex:
                    otherTeamMatchIndex = matchIndex
                else:
                    otherTeamMatchIndex = len(otherTeamListPts) - 1
                if otherTeamListPts[otherTeamMatchIndex] > listPts[matchIndex]:
                    count += 1
                    #otherTeam = self.database.getTeam(otherTeam[0])
                    #print(f'{otherTeam.name} {otherTeamListPts[matchIndex]} > {listPts[matchIndex]}')
                elif otherTeamListPts[otherTeamMatchIndex] == listPts[matchIndex]:
                    count += 0.5
                    #otherTeam = self.database.getTeam(otherTeam[0])
                    #print(f'{otherTeam.name} {otherTeamListPts[matchIndex]} == {listPts[matchIndex]}')
            # print (f'matchIndex = {matchIndex}, count = {count}')
            # Draw the box.
            x = matchIndex * boxWidth
            # y = math.floor(count - 1) * boxHeight
            for boxIndex in range(math.floor(count - 1), numPositions):
                y = boxIndex * boxHeight
                colour = 'yellow'
                if season.goodPos is not None and boxIndex < season.goodPos:
                    colour = 'green'
                elif season.positivePos is not None and boxIndex < season.positivePos:
                    colour = '#CCFFCC;'
                elif season.badPos is not None and boxIndex >= season.badPos:
                    colour = 'red'
                self.html.addLine(f'<rect x="{x}" y="{y}" width="{boxWidth}" height="{boxHeight}" style="fill: {colour};" />')

        # Draw a grid.
        for i in range(season.numMatches + 1):
            x = i * boxWidth
            self.html.addLine(f'<line x1="{x}" y1="{0}" x2="{x}" y2="{height}" style="stroke: black; stroke-width: 1;" />')

        for i in range(numPositions + 1):
            y = i * boxHeight
            self.html.addLine(f'<line x1="{0}" y1="{y}" x2="{width}" y2="{y}" style="stroke: black; stroke-width: 1;" />')

        self.html.addLine('</svg>')
        self.html.addLine('</fieldset>')
        self.html.addLine('<br />')

        # Draw a graph of match Results.
        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;"><legend>Match Results</legend>')

        svgWidth = season.numMatches * boxWidth
        svgHeight = boxHeight
        self.html.addLine(f'<svg width="{svgWidth}" height="{svgHeight}" style="vertical-align: top; border: 1px solid black;" xmlns="http://www.w3.org/2000/svg" version="1.1">')

        # This was originally based on point changes, but that does not work with point deductions.
        # Now based on goal difference change.
        y = 0
        # previousPts = 0
        previousGoalDiff = 0
        for boxIndex in range(len(listPts)):
            x = boxIndex * boxWidth
            goalDiff = getGoalDifference(listPts[boxIndex])
            colour = 'yellow'
            # if listPts[boxIndex] > previousPts + 1.1:
            if goalDiff > previousGoalDiff + 0.1:
                colour = 'green'
            # elif listPts[boxIndex] < previousPts + 0.9:
            elif goalDiff < previousGoalDiff - 0.1:
                colour = 'red'
            self.html.addLine(f'<rect x="{x}" y="{y}" width="{boxWidth}" height="{boxHeight}" style="fill: {colour};" />')
            # previousPts = listPts[boxIndex]
            # print(f'{boxIndex} {listPts[boxIndex]:0.3f} {goalDiff:0.1f} {previousGoalDiff:0.1f} {colour}')
            previousGoalDiff = goalDiff

        # Draw a grid.
        for i in range(season.numMatches + 1):
            x = i * boxWidth
            self.html.addLine(f'<line x1="{x}" y1="{0}" x2="{x}" y2="{height}" style="stroke: black; stroke-width: 1;" />')
        # self.html.addLine(f'<rect x1="{0}" y1="{0}" width="{width}" height="{height}" style="stroke: black; stroke-width: 1;" />')

        self.html.addLine('</svg>')
        self.html.addLine('</fieldset>')
        self.html.addLine('</div>')

        # Keep points and compare to in line.
        self.html.addLine('<div style="display: inline-block; vertical-align: top;">')

        # otherTeams.sort(key=sortTeamsByFinalPointsCompareTo, reverse=True)
        otherTeams.sort(key=sortTeamsByFinalPoints, reverse=True)

        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;"><legend>Compared To</legend>')
        self.html.addLine('<form action="app:show_team_season" method="get">')
        self.html.addLine(f'<input type="hidden" name="team" value="{teamIndex}" />')
        self.html.addLine(f'<input type="hidden" name="season" value="{seasonIndex}" />')
        opponentIndex = int(parameters['opponent']) if 'opponent' in parameters else count - 1

        self.html.add('<select name="opponent" onchange="this.form.submit();">')
        if opponentIndex >= len(otherTeams):
            opponentIndex = len(otherTeams) - 1
        for index in range(len(otherTeams)):
            otherTeam = self.database.getTeam(otherTeams[index][0])
            self.html.add(f'<option value="{index}"')
            if index == opponentIndex:
                self.html.add(' selected="yes"')
            self.html.add(f'>{otherTeam.name}</option>')
        self.html.addLine('</select>')
        otherTeam = self.database.getTeam(otherTeams[opponentIndex][0])
        self.html.addLine(otherTeam.toHtml())
        self.html.addLine('</form>')
        self.html.addLine('</fieldset>')
        self.html.addLine('<br/>')

        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;"><legend>Points</legend>')
        maxMatches = 1
        maxPoints = 3
        if len(listPts) > 0:
            if len(listPts) > maxMatches:
                maxMatches = len(listPts)
            finalPoints = listPts[len(listPts) - 1]
            if finalPoints > maxPoints:
                maxPoints = finalPoints
        otherTeamListPts = otherTeams[opponentIndex][2]
        if len(otherTeamListPts) > 0:
            if len(otherTeamListPts) > maxMatches:
                maxMatches = len(otherTeamListPts)
            finalPoints = otherTeamListPts[len(otherTeamListPts) - 1]
            if finalPoints > maxPoints:
                maxPoints = finalPoints

        # Draw a graph.
        # svgWidth = 500
        svgWidth = len(listPts) * boxWidth
        svgHeight = 300
        self.html.addLine(f'<svg width="{svgWidth}" height="{svgHeight}" style="vertical-align: top; border: 1px solid black;" xmlns="http://www.w3.org/2000/svg" version="1.1">')

        # Graph Area.
        top = 0
        bottom = 0
        left = 0
        right = 0

        width = svgWidth - left - right
        height = svgHeight - top - bottom

        self.html.addLine(f'<rect x="{left}" y="{top}" width="{width}" height="{height}" style="fill: white; stroke: black; stroke-width: 1;" />')

        # X Axis.
        xScale = width / maxMatches

        # Y Axis.
        yScale = height / maxPoints

        # Draw a Y axis scale.
        pts = 0
        for i in range(math.floor(maxPoints / 15)):
            pts = (i + 1) * 15
            if pts < maxPoints:
                y = top + height - yScale * pts
                self.html.addLine(f'<line x1="{left}" y1="{y}" x2="{left + width}" y2="{y}" style="stroke: grey; stroke-width: 1;" />')

        # Draw a X axis scale. ???
        # print(f'maxMatches = {maxMatches}')
        for i in range(math.floor(maxMatches / 5)):
            match = (i + 1) * 5
            # print(f'match = {match}')
            if pts < maxPoints:
                x = left + xScale * match
                self.html.addLine(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + height}" style="stroke: grey; stroke-width: 1;" />')

        # Draw the 5 game moving average as a green bar.
        x = left
        for index in range(0, len(listPts)):
            if index >= 5:
                movingAveragePts = listPts[index] - listPts[index-5]
            else:
                movingAveragePts = listPts[index]
            barHeight = yScale * movingAveragePts - 1
            if barHeight > 1:
                self.html.addLine(f'"<rect x={x} y={top + height - barHeight - 1} width={xScale - 1} height={barHeight} style="fill: moccasin;" />') # clip-path="url(#graph-area)"
            x += xScale

        # Draw the points.
        x = left
        self.html.add(f'<polyline points="{x},{top + height} ')
        for pts in listPts:
            x += xScale
            y = top + height - yScale * pts
            self.html.add(f'{x},{y} ')
        self.html.addLine(f'" style="fill: none; stroke: green; stroke-width: 2;" />') # clip-path="url(#graph-area)"

        # Draw the 5 game moving average as a green line.
        #if len(listPts) >= 5:
        #    x = left + 5 * xScale
        #    y = top + height - yScale * listPts[4]
        #    self.html.add(f'<polyline points="{x},{y} ')
        #    for index in range(5, len(listPts)):
        #        movingAveragePts = listPts[index] - listPts[index-5]
        #        x += xScale
        #        y = top + height - yScale * movingAveragePts
        #        self.html.add(f'{x},{y} ')
        #    self.html.addLine(f'" style="fill: none; stroke: green; stroke-width: 2;" />') # clip-path="url(#graph-area)"

        # Draw the opponent points.
        x = left
        self.html.add(f'<polyline points="{x},{top + height} ')
        for pts in otherTeamListPts:
            x += xScale
            y = top + height - yScale * pts
            self.html.add(f'{x},{y} ')
        self.html.addLine(f'" style="fill: none; stroke: red; stroke-width: 1;" />') # clip-path="url(#graph-area)"

        self.html.addLine('</svg>')
        self.html.addLine('</fieldset>')
        self.html.addLine('<br />')

        # Draw a graph of the points difference to the other team.
        self.html.addLine('<fieldset style="display: inline-block; vertical-align: top;"><legend>Difference</legend>')

        svgWidth = len(listPts) * boxWidth
        yScale = 4
        baseLine = 15 * yScale
        svgHeight = 2 * baseLine
        self.html.addLine(f'<svg width="{svgWidth}" height="{svgHeight}" style="vertical-align: top; border: 1px solid black;" xmlns="http://www.w3.org/2000/svg" version="1.1">')

        # Draw the difference bar.
        for matchIndex in range(len(listPts)):
            x = matchIndex * boxWidth
            if len(otherTeamListPts) > matchIndex:
                otherTeamMatchIndex = matchIndex
            else:
                otherTeamMatchIndex = len(otherTeamListPts) - 1

            # print(f'matchIndex = {matchIndex}, difference = {listPts[matchIndex] - otherTeamListPts[otherTeamMatchIndex]}, otherTeamMatchIndex = {otherTeamMatchIndex}')

            if listPts[matchIndex] > otherTeamListPts[otherTeamMatchIndex]:
                difference = listPts[matchIndex] - otherTeamListPts[otherTeamMatchIndex]
                if difference > 3.1:
                    colour = 'green'
                else:
                    colour = 'yellow'
                difference *= yScale
                self.html.addLine(f'<rect x="{x}" y="{baseLine-difference}" width="{boxWidth}" height="{difference}" style="fill: {colour};" />')
            else:
                difference = otherTeamListPts[otherTeamMatchIndex] - listPts[matchIndex]
                if difference > 3.1:
                    colour = 'red'
                else:
                    colour = 'yellow'
                difference *= yScale
                self.html.addLine(f'<rect x="{x}" y="{baseLine}" width="{boxWidth}" height="{difference}" style="fill: {colour};" />')

        # Draw a grid.
        for i in range(5):
            pts = (i + 1) * 3
            pts *= yScale
            self.html.addLine(f'<line x1="0" y1="{baseLine + pts}" x2="{svgWidth}" y2="{baseLine + pts}" style="stroke: grey; stroke-width: 1;" />')
            self.html.addLine(f'<line x1="0" y1="{baseLine - pts}" x2="{svgWidth}" y2="{baseLine - pts}" style="stroke: grey; stroke-width: 1;" />')

        for matchIndex in range(len(listPts)):
            x = matchIndex * boxWidth
            self.html.addLine(f'<line x1="{x}" y1="{0}" x2="{x}" y2="{svgHeight}" style="stroke: grey; stroke-width: 1;" />')

        # Draw the base line.
        self.html.addLine(f'<line x1="0" y1="{baseLine}" x2="{svgWidth}" y2="{baseLine}" style="stroke: black; stroke-width: 1;" />')

        self.html.addLine('</svg>')
        self.html.addLine('</fieldset>')
        self.html.addLine('</div>')
        self.html.addLine('<br />')

        # Draw the nonogram of results against all the other teams.
        self.html.addLine(f'<fieldset style="display: inline-block; vertical-align: top;"><legend>{team.name} Nonogram</legend>')
        xScale = 14
        svgWidth = 300
        svgHeight = boxHeight * (1 + len(otherTeams))

        self.html.addLine(f'<svg width="{svgWidth}" height="{svgHeight}" style="vertical-align: top; border: 1px solid black;" xmlns="http://www.w3.org/2000/svg" version="1.1">')

        # Label the rows.
        for index in range(len(otherTeams)):
            otherTeam = self.database.getTeam(otherTeams[index][0])
            x = 12 * xScale + 2
            y = (index + 1) * boxHeight - 3
            self.html.addLine(f'<a xlink:href="app:show_team_season?team={otherTeam.index}&season={seasonIndex}"><text text-anchor="start" x={x} y={y} font-size="8pt">{otherTeam.name}</text></a>')

            goodPts = 0
            availablePts = 0
            badPts = 0

            # Get the home results.
            sql = f"SELECT HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE HOME_TEAM_ID = {team.index} AND AWAY_TEAM_ID = {otherTeam.index} AND THE_DATE >= '{season.startDate}' AND THE_DATE <= '{finishDate}';"
            cursor = cndb.execute(sql)
            row = cursor.fetchone()
            cursor.close()

            if row is None:
                availablePts += 3
            elif row[0] == row[1]:
                goodPts += 1
                badPts += 1
            elif row[0] > row[1]:
                goodPts += 3
            else:
                badPts += 3

            # Get the away results.
            sql = f"SELECT HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE HOME_TEAM_ID = {otherTeam.index} AND AWAY_TEAM_ID = {team.index} AND THE_DATE >= '{season.startDate}' AND THE_DATE <= '{finishDate}';"
            cursor = cndb.execute(sql)
            row = cursor.fetchone()
            cursor.close()

            if row is None:
                availablePts += 3
            elif row[0] == row[1]:
                goodPts += 1
                badPts += 1
            elif row[0] > row[1]:
                badPts += 3
            else:
                goodPts += 3

            # Draw the bar.
            y = index * boxHeight
            x = 6 * xScale - (badPts + (availablePts / 2)) * xScale
            if badPts > 0:
                self.html.addLine(f'<rect x="{x}" y="{y}" width="{badPts * xScale}" height="{boxHeight}" style="fill: red;" />')
                x += badPts * xScale
            if availablePts > 0:
                self.html.addLine(f'<rect x="{x}" y="{y}" width="{availablePts * xScale}" height="{boxHeight}" style="fill: yellow;" />')
                x += availablePts * xScale
            if goodPts > 0:
                self.html.addLine(f'<rect x="{x}" y="{y}" width="{goodPts * xScale}" height="{boxHeight}" style="fill: green;" />')
                x += goodPts * xScale

        # Draw a grid over the nonograph.
        for i in range(12):
            x = (i + 1) * xScale
            y = boxHeight * len(otherTeams)
            self.html.addLine(f'<line x1="{x}" y1="0" x2="{x}" y2="{y}" style="stroke: grey; stroke-width: 1;" />')
        for i in range(len(otherTeams)):
            x = 12 * xScale
            y = boxHeight * (i + 1)
            self.html.addLine(f'<line x1="0" y1="{y}" x2="{x}" y2="{y}" style="stroke: grey; stroke-width: 1;" />')
        x = 6 * xScale
        y = boxHeight * len(otherTeams)
        self.html.addLine(f'<line x1="{x}" y1="0" x2="{x}" y2="{y}" style="stroke: black; stroke-width: 1;" />')

        self.html.addLine('</svg>')
        self.html.addLine('</fieldset>')

        # Get the list of points for this team without bonus points.
        listPts = self.database.getArrayTeamPts(teamIndex, season.startDate, finishDate, False)

        # Draw a graph of the points prediction.
        self.html.addLine(f'<fieldset style="display: inline-block; vertical-align: top;"><legend>Points Prediction</legend>')
        self.html.addLine('<table>')
        count = 0
        previousPts = 0
        for pts in listPts:
            count += 1
            self.html.add('<tr><td>')
            self.html.addLine(f'<svg class="wdlbox" width="{boxWidth}" height="{boxHeight}" style="vertical-align: top; border: 1px solid black; margin: 4px 1px 0px 1px;" xmlns="http://www.w3.org/2000/svg" version="1.1">')

            colour = 'yellow'
            if pts > previousPts + 1.1:
                colour = 'green'
            elif pts < previousPts + 0.9:
                colour = 'red'
            self.html.addLine(f'<rect x="0" y="0" width="{boxWidth}" height="{boxHeight}" style="fill: {colour};" />')
            previousPts = pts
            self.html.addLine('</svg>') # </td><td>')

            self.drawPossiblePointsBox(600, boxHeight, 0, season.numMatches * 3, pts, pts, count, season.numMatches - count, season.numMatches, 2 * season.numMatches)
            self.html.addLine('</td></tr>')
        self.html.addLine('</table>')
        self.html.addLine('</fieldset>')

        # Draw a graph of the type of results.
        self.html.addLine(f'<fieldset style="display: inline-block; vertical-align: top;"><legend>Result Distribution</legend>')
        self.displayGraphTypeResults(cndb, teamIndex, season.startDate, finishDate, -4, +4, 5)
        self.html.addLine('</fieldset>')

        self.html.addLine('</div>')

        # Close the database.
        cndb.close()



    def getTypeResultsData(self, cndb, teamIndex, startDate, finishDate, minScore, maxScore, maxCount):
        ''' Get the data for a type results graph. '''
        resultTypes = {}
        for resultType in range(minScore, maxScore + 1):
            resultTypes[resultType] = 0

        # Get the home results.
        sql = f"SELECT HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE HOME_TEAM_ID = {teamIndex} AND THE_DATE >= '{startDate}' AND THE_DATE <= '{finishDate}';"
        cursor = cndb.execute(sql)
        for row in cursor:
            resultType = row[0] - row[1]
            if resultType < minScore:
                resultType = minScore
            if resultType > maxScore:
                resultType = maxScore
            resultTypes[resultType] += 1
            # print(f'{resultType} = {resultTypes[resultType]}')
        cursor.close()
        # Get the away results.
        sql = f"SELECT HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE AWAY_TEAM_ID = {teamIndex} AND THE_DATE >= '{startDate}' AND THE_DATE <= '{finishDate}';"
        cursor = cndb.execute(sql)
        for row in cursor:
            resultType = row[1] - row[0]
            if resultType < minScore:
                resultType = minScore
            if resultType > maxScore:
                resultType = maxScore
            resultTypes[resultType] += 1
            #print(f'{resultType} = {resultTypes[resultType]}')
        cursor.close()

        #self.html.addLine('<table>')
        #for resultType in range(MIN_SCORE, MAX_SCORE + 1):
        #    self.html.addLine(f'<tr><td>{resultType}</td><td>{resultTypes[resultType]}</td></tr>')
        #self.html.addLine('</table>')
        for resultType in range(minScore, maxScore + 1):
            if resultTypes[resultType] > maxCount:
                maxCount = resultTypes[resultType]

        return resultTypes, maxCount



    def displayGraphTypeResults(self, cndb, teamIndex, startDate, finishDate, minScore, maxScore, maxCount):
        ''' Display a graph of results types. '''
        # Build an dictionary of the result types.
        resultTypes, maxCount = self.getTypeResultsData(cndb, teamIndex, startDate, finishDate, minScore, maxScore, maxCount)

        # Display the graph of result types.
        maxCount = self.displayHistrogram(resultTypes, minScore, maxScore, maxCount)

        # Return the maximum count on this histrogram.
        return maxCount



    def displayHistrogram(self, resultTypes, minScore, maxScore, maxCount):
        ''' Display a histrogram. '''
        boxWidth = 16
        boxHeight = 16
        svgWidth = (maxScore - minScore + 1) * boxWidth
        svgHeight = maxCount * boxHeight

        self.html.addLine(f'<svg width="{svgWidth}" height="{svgHeight}" style="vertical-align: top; border: 1px solid black;" xmlns="http://www.w3.org/2000/svg" version="1.1">')

        # Draw the grid.
        for resultType in range(minScore, maxScore + 1):
            # print(f'{resultType} = {resultTypes[resultType]}')
            x = (resultType - minScore) * boxWidth
            colour = 'red'
            if resultType == 0:
                colour = 'yellow'
            elif resultType > 0:
                colour = 'green'
            if resultTypes[resultType] > 0:
                 y = resultTypes[resultType] * boxHeight
                 self.html.addLine(f'<rect x="{x}" y="{svgHeight - y}" width="{boxWidth}" height="{y}" style="fill: {colour};" />')
                 # print(f'<rect x="{x}" y="{0}" width="{boxWidth}" height="{y}" style="fill: {colour};" />')

        # Draw a grid over the graph.
        for i in range(minScore, maxScore):
            x = (1 + i - minScore) * boxWidth
            self.html.addLine(f'<line x1="{x}" y1="0" x2="{x}" y2="{svgHeight}" style="stroke: grey; stroke-width: 1;" />')
        for i in range(maxCount - 1):
            y = boxHeight * (i + 1)
            self.html.addLine(f'<line x1="0" y1="{y}" x2="{svgWidth}" y2="{y}" style="stroke: grey; stroke-width: 1;" />')

        self.html.addLine('</svg>')

        return maxCount



def getGoalDifference(points):
    '''
    Returns the goal difference from the number of points.goal_difference value.
    '''
    goalDifference = 1000 * (points % 1)
    if goalDifference > 500:
        goalDifference -= 1000
    return goalDifference



def sortTeamsByFinalPoints(team):
    ''' Team sorting function for the graph in showTableSubset(). '''
    points = team[2]
    if len(points) == 0:
        return 0
    finalPoints = points[len(points)-1]
    return finalPoints

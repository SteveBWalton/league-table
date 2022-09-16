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



    def showHome(self, parameters):
        '''
        Render the homepage on the html object.

        :param string parametersString: Specify the request parameters as a string. The keys 'firstyear' and 'lastyear' are optional.
        '''
        # Decode the parameters.
        level = int(parameters['level']) if 'level' in parameters else 0
        theDate = parameters['date'] if 'date' in parameters else f'{datetime.date.today()}'

        self.html.clear()
        # self.displayToolbar(True, None, 'home?firstyear={}&lastyear={}'.format(firstSeason-1, lastSeason-1), 'home?firstyear={}&lastyear={}'.format(firstSeason+1, lastSeason+1), False, True, False)
        toolbar = self.buildToolbarOptions(level, 'level', ((0, 'Default'), (1, 'Combined')), 'app:home', (('date', theDate), ))
        if theDate is None:
            self.editTarget = 'edit_date'
        else:
            self.editTarget = f'edit_date?date={theDate}'
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, self.editTarget, 'home', 'home', False, True, False, toolbar)
        self.html.addLine('<h1>Home</h1>')

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        self.html.add('<fieldset style="display: inline-block; vertical-align: top;"><legend>')
        if theDate is None:
            self.html.add('Table')
        else:
            self.html.add(f'Table to {theDate}')
        self.html.addLine('</legend>')
        self.html.addLine('<table>')
        if level == 1:
            self.html.addLine('<tr><td colspan="2">Team</td><td>P</td><td>W</td><td>D</td><td>L</td><td>F</td><td>A</td><td>Pts</td><td>Dif</td></tr>')
        else:
            self.html.addLine('<tr><td colspan="2">Team</td><td>P</td><td>W</td><td>D</td><td>L</td><td>F</td><td>A</td><td>W</td><td>D</td><td>L</td><td>F</td><td>A</td><td>Pts</td><td>Dif</td></tr>')

        sql = "SELECT HOME_TEAM_ID, HOME_WINS, HOME_DRAWS, HOME_LOSES, HOME_FOR, HOME_AGAINST, AWAY_WINS, AWAY_DRAWS, AWAY_LOSES, AWAY_FOR, AWAY_AGAINST, 3 * (HOME_WINS + AWAY_WINS) + (HOME_DRAWS + AWAY_DRAWS) AS PTS, HOME_FOR + AWAY_FOR - HOME_AGAINST - AWAY_AGAINST AS DIFF, HOME_FOR + AWAY_FOR AS FOR FROM "
        sql += "(SELECT HOME_TEAM_ID, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS HOME_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS HOME_DRAWS, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS HOME_LOSES, SUM(HOME_TEAM_FOR) AS HOME_FOR, SUM(AWAY_TEAM_FOR) AS HOME_AGAINST FROM MATCHES "
        if theDate is None:
            # All Results
            sql += "WHERE SEASON_ID = 1 GROUP BY HOME_TEAM_ID) AS HOME_RESULTS "
        else:
            # Up to the date.
            sql += f"WHERE SEASON_ID = 1 AND THE_DATE <= '{theDate}' GROUP BY HOME_TEAM_ID) AS HOME_RESULTS "
        sql += "INNER JOIN "
        sql += "(SELECT AWAY_TEAM_ID, SUM(HOME_TEAM_FOR < AWAY_TEAM_FOR) AS AWAY_WINS, SUM(HOME_TEAM_FOR = AWAY_TEAM_FOR) AS AWAY_DRAWS, SUM(HOME_TEAM_FOR > AWAY_TEAM_FOR) AS AWAY_LOSES, SUM(AWAY_TEAM_FOR) AS AWAY_FOR, SUM(HOME_TEAM_FOR) AS AWAY_AGAINST FROM MATCHES "
        if theDate is None:
            # All Results.
            sql += "WHERE SEASON_ID = 1 GROUP BY AWAY_TEAM_ID) AS AWAY_RESULTS "
        else:
            # Update to the date.
            sql += f"WHERE SEASON_ID = 1 AND THE_DATE <= '{theDate}' GROUP BY AWAY_TEAM_ID) AS AWAY_RESULTS "
        sql += "ON HOME_RESULTS.HOME_TEAM_ID = AWAY_RESULTS.AWAY_TEAM_ID "
        sql += "ORDER BY PTS DESC, DIFF DESC, FOR DESC; "
        # print(sql)
        # sql .= "USING (TEAM_ID);"
        cursor = cndb.execute(sql)
        count = 0
        for row in cursor:
            if count <= 3:
                self.html.add('<tr class="win2">')
            elif count >= 17:
                self.html.add('<tr class="lost2">')
            else:
                self.html.add('<tr>')
            team = self.database.getTeam(row[0])

            count += 1
            self.html.add(f'<td class="rank" style="text-align: right; vertical-align: middle;">{count}</td>')
            self.html.add(f'<td style="text-align: right;">{team.toHtml()}</td>')

            self.html.add(f'<td class="secondary" style="text-align: right;">{row[1] + row[2] + row[3] + row[6] + row[7] + row[8]}</td>')

            if level == 1:
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

            self.html.add(f'<td style="text-align: right;">{row[11]}</td>')
            self.html.add(f'<td class="secondary" style="text-align: right;">{row[12]:+}</td>')

            self.html.add('<td>')
            self.drawWinDrawLossBox(200, 18, row[1] + row[6], row[2] + row[7], row[3] + row[8])
            self.html.add('</td>')

            self.html.addLine('</tr>')

        self.html.addLine('</table>')
        self.html.addLine('</fieldset>')

        self.html.add('<fieldset style="display: inline-block; vertical-align: top;"><legend>')
        if theDate is None:
            self.html.add('Recent Matches')
        else:
            self.html.add(f'Recent Matches to {theDate}')
        self.html.addLine('</legend>')
        self.html.addLine('<table>')
        if theDate is None:
            # All Results.
            sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = ? ORDER BY THE_DATE DESC LIMIT 20;"
            params = (1, )
        else:
            # Results up to date.
            sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = ? AND THE_DATE <= ? ORDER BY THE_DATE DESC LIMIT 20;"
            params = (1, theDate)

        cursor = cndb.execute(sql, params)
        for row in cursor:
            self.html.add('<tr>')
            theMatchDate = row[0]
            isDateGuess = row[1] == 1
            if isDateGuess:
                theMatchDate = f'({row[0]})'
            homeTeam = self.database.getTeam(row[2])
            awayTeam = self.database.getTeam(row[3])

            self.html.add(f'<td class="date" style="text-align: center;"><a href="app:home?date={row[0]}">{theMatchDate}</a></td>')
            self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
            self.html.add(f'<td>{row[4]}</td>')
            self.html.add(f'<td>{row[5]}</td>')
            self.html.add(f'<td>{awayTeam.toHtml()}</td>')
            self.html.addLine('</tr>')

        self.html.addLine('</table>')
        self.html.addLine('</fieldset>')

        # Future matches.
        self.html.add('<fieldset style="display: inline-block; vertical-align: top;"><legend>')
        self.html.add(f'Future Matches after {theDate}')
        self.html.addLine('</legend>')
        self.html.addLine('<table>')
        # Results after to date.
        sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = ? AND THE_DATE > ? ORDER BY THE_DATE LIMIT 20;"
        params = (1, theDate)

        cursor = cndb.execute(sql, params)
        for row in cursor:
            self.html.add('<tr>')
            theMatchDate = row[0]
            isDateGuess = row[1] == 1
            if isDateGuess:
                theMatchDate = f'({row[0]})'
            homeTeam = self.database.getTeam(row[2])
            awayTeam = self.database.getTeam(row[3])

            self.html.add(f'<td class="date" style="text-align: center;"><a href="app:home?date={row[0]}">{theMatchDate}</a></td>')
            self.html.add(f'<td style="text-align: right;">{homeTeam.toHtml()}</td>')
            self.html.add(f'<td>{row[4]}</td>')
            self.html.add(f'<td>{row[5]}</td>')
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
        self.html.addLine('<h1>Sports Results Database: {}</h1>'.format(self.database.currentSport.name))

        self.html.addLine('<fieldset>')
        self.html.addLine('<legend>General</legend>')
        self.html.addLine('<ul>')
        self.html.addLine('<li><a href="app:tournament_winners">Tournament Results</a></li>')
        self.html.addLine('<li><a href="app:show_season">Season Results</a></li>')
        self.html.addLine('<li><a href="app:table_teams">Table of {}</a></li>'.format(self.database.currentSport.plural))
        self.html.addLine('<li><a href="app:table_matches">Table of Match Wins</a></li>')
        if self.database.currentSport.tableNations:
            self.html.addLine('<li><a href="app:table_nations">Table of Nations</a></li>')
            self.html.addLine('<li><a href="app:table_nation_matches">Table of Nation Match Wins</a></li>')
        self.html.addLine('<li><a href="app:table_teams?orderby=1">{} by Date of Birth</a></li>'.format(self.database.currentSport.plural))
        self.html.addLine('<li><a href="app:list_matches">List of Matches</a></li>')
        self.html.addLine('<li><a href="app:table_headtohead">Table of Head to Heads</a></li>')
        self.html.addLine('<li><a href="app:table_championage">Table of Age of Champions</a></li>')
        self.html.addLine('<li><a href="app:table_locations">Table of Locations</a></li>')
        self.html.addLine('</ul>')
        self.html.addLine('</fieldset>')

        self.html.addLine('<fieldset>')
        self.html.addLine('<legend>Administration</legend>')
        self.html.addLine('<ul>')
        self.html.addLine('<li><a href="app:switch_sports">Switch Sports</a></li>')
        self.html.addLine('<li><a href="app:preferences">Preferences</a></li>')
        self.html.addLine('<li><a href="app:configure_sport">Configure Sport</a></li>')
        self.html.addLine('<li><a href="app:maintenence">Database Maintenance</a></li>')
        self.html.addLine('<li><a href="app:country_db">Country Database</a></li>')
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
        theDate = parameters['date'] if 'date' in parameters else f'{datetime.date.today()}'
        level = int(parameters['level']) if 'level' in parameters else 0
        isShowAge = True if 'age' in parameters else False
        firstYear = parameters['firstyear'] if 'firstyear' in parameters else None
        lastYear = parameters['lastyear'] if 'lastyear' in parameters else None
        tournamentIndex = int(parameters['tournamentid']) if 'tournamentid' in parameters else 0
        flags = int(parameters['flags']) if 'flags' in parameters else 0

        # Get the team object.
        team = self.database.getTeam(teamIndex)

        # Connect to the database.
        cndb = sqlite3.connect(self.database.filename)

        # Initialise the display.
        self.html.clear()
        self.editTarget = f'edit_team?team={teamIndex}'
        self.displayToolbar(Render.TOOLBAR_INITIAL_SHOW, self.editTarget, None, None, True, True, False, '')

        self.html.add(f'<p><span class="h1">{team.name}</span></p>')

        self.html.addLine('<fieldset><legend>Administration</legend>')
        self.html.addLine('<table>')
        sql = "SELECT THE_DATE, THE_DATE_GUESS, HOME_TEAM_ID, AWAY_TEAM_ID, HOME_TEAM_FOR, AWAY_TEAM_FOR FROM MATCHES WHERE SEASON_ID = ? AND (HOME_TEAM_ID = ? OR AWAY_TEAM_ID = ?) AND THE_DATE <= ? ORDER BY THE_DATE DESC;"
        params = (1, teamIndex, teamIndex, theDate)
        cursor = cndb.execute(sql, params)
        for row in cursor:
            theMatchDate = row[0]
            isDateGuess = row[1] == 1
            if isDateGuess:
                theMatchDate = f'({row[0]})'
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

            self.html.add(f'<tr class="{className}">')
            self.html.add(f'<td class="date" style="text-align: center;">{theMatchDate}</td>')
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

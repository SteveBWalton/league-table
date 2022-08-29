#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Module to run the table program.
'''

# Import system libraries.
import sys
import os
import argparse

# Import application libraries.
import walton.install
import walton.ansi



if __name__ == '__main__':
    # Process the command line arguments.
    # This might end the program (--help).
    argParse = argparse.ArgumentParser(prog='table', description='League tables in various sports.')
    argParse.add_argument('-i', '--install', help='Install the modelling program and desktop link.', action='store_true')
    argParse.add_argument('-u', '--uninstall', help='Uninstall the modelling program.', action='store_true')
    args = argParse.parse_args()

    if args.install:
        # Install the program.

        # Global installation.
        walton.install.makeMenuCategory('waltons', 'Waltons', 'Waltons', False)

        # Local installation.
        if walton.install.isRootUser():
            print('Please run the rest of the installation as a standard user.')
        else:
            walton.install.makeCommandPrompt('table', False, __file__)
            walton.install.makeDesktopFile('walton.table', False, 'Table', __file__, f'{os.path.dirname(__file__)}/glade/soccer_ball.ico', 'League tables in various sports.', 'GNOME;GTK;Waltons;')

            # Add an alias to remove warning messages.
            walton.install.addBashAlias('table')

        sys.exit(0)

    if args.uninstall:
        # Remove the program.
        # Local files.
        if walton.install.isRootUser():
            print('Please run the uninstall as a standard user.')
        else:
            walton.install.removeCommandPrompt('table', False)
            walton.install.removeDesktopFile('walton.table', False)
        sys.exit(0)

    # Welcome message.
    print(f'{walton.ansi.LIGHT_YELLOW}Table{walton.ansi.RESET_ALL} by Steve Walton © 2022-2022.')
    print(f'Python Version {sys.version_info.major}·{sys.version_info.minor}·{sys.version_info.micro}.  Expecting Python 3.')




# Import more system libraries.
import platform
import subprocess

# import urllib

# Application libraries.
from application import Application



def isGraphicsAvailable():
    ''' Returns true if the graphical display is available. '''
    with subprocess.Popen(["xset", "-q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        process.communicate()
        return process.returncode == 0
    return False



if __name__ == '__main__':
    # An initial message.
    print(f'Operating System is {walton.ansi.LIGHT_YELLOW}{platform.system()}{walton.ansi.RESET_ALL}.  Desktop is {walton.ansi.LIGHT_YELLOW}{os.environ.get("DESKTOP_SESSION")}{walton.ansi.RESET_ALL}.')

    # Create an application object to be shared by rendering engines.
    application = Application(args)

    if isGraphicsAvailable():
        # Run via a GTK main window.
        import glade.main_window
        mainWindow = glade.main_window.MainWindow(application, args)
        # application.post_render_page = mainWindow.DisplayCurrentPage
        # application.actions = mainWindow.actions
        # Main GTK loop.
        mainWindow.run()


        # Save the configuration file.
        application.configuration.setCurrentSport(str(application.database.currentSport.index))
        application.configuration.saveConfigurationFile()
    else:
        print('Error - Graphics are not available.')


    print(f'Goodbye from the {walton.ansi.LIGHT_YELLOW}Table{walton.ansi.RESET_ALL} database.')

#!/bin/bash
#
# Script to set the file permissions in the table source code directory.
#

# Make a walton folder for the library modules.
if [ ! -d "walton" ] ; then
    mkdir "walton"
fi
if [ ! -e "walton/__init__.py" ] ; then
    touch "walton/__init__.py"
fi

# Check that the library modules exist.
if [ ! -e "walton/xml.py" ] ; then
    ln -s ../../Library/py3/modXml.py walton/xml.py
fi
if [ ! -e "walton/html.py" ] ; then
    ln -s ../../Library/py3/modHtml.py walton/html.py
fi
if [ ! -e "walton/install.py" ] ; then
    ln -s ../../Library/py3/modInstall.py walton/install.py
fi
if [ ! -e "walton/database.py" ] ; then
    ln -s ../../Library/py3/interfaceDatabase.py walton/database.py
fi
if [ ! -e "walton/toolbar.py" ] ; then
    ln -s ../../Library/py3/interfaceToolbar.py walton/toolbar.py
fi
if [ ! -e "walton/application.py" ] ; then
    ln -s ../../Library/py3/interfaceApplication.py walton/application.py
fi
if [ ! -e "walton/year_range.py" ] ; then
    ln -s ../../Library/py3/modYearRange.py walton/year_range.py
fi
if [ ! -e "walton/ansi.py" ] ; then
    ln -s ../../Library/py3/ansi.py walton/ansi.py
fi
if [ ! -e "walton/configuration.py" ] ; then
    ln -s ../../Library/py3/interface_configuration.py walton/configuration.py
fi

# Make a walton/glade folder for the library dialog modules.
if [ ! -d "walton/glade" ] ; then
    mkdir "walton/glade"
fi
if [ -e "walton/glade/selectcountry.glade" ] ; then
    rm "walton/glade/selectcountry.glade"
fi
if [ ! -e "walton/glade/select_country.py" ] ; then
    ln -s ../../../Library/py3/dialogSelectCountry.py walton/glade/select_country.py
fi
if [ ! -e "walton/glade/select_years.glade" ] ; then
    ln -s ../../../Library/py3/dialogSelectYears.glade walton/glade/select_years.glade
fi
if [ ! -e "walton/glade/select_years.py" ] ; then
    ln -s ../../../Library/py3/dialogSelectYears.py walton/glade/select_years.py
fi
if [ ! -e "walton/glade/edit_country.glade" ] ; then
    ln -s ../../../Library/py3/edit_country.glade walton/glade/edit_country.glade
fi
if [ ! -e "walton/glade/edit_country.py" ] ; then
    ln -s ../../../Library/py3/edit_country.py walton/glade/edit_country.py
fi
if [ ! -e "walton/glade/calendar.py" ] ; then
    ln -s ../../../Library/py3/modEntryCalendar.py walton/glade/calendar.py
fi
if [ ! -e "walton/glade/fullscreen.py" ] ; then
    ln -s ../../../Library/py3/interfaceFullscreen.py walton/glade/fullscreen.py
fi
if [ ! -e "walton/glade/webkit.py" ] ; then
    ln -s ../../../Library/py3/interfaceWebKit2.py walton/glade/webkit.py
fi

# Add links to the glade folder.
if [ ! -e "glade/soccer_ball.ico" ] ; then
    ln -s ../../../../Graphics/Icons/soccer_ball.ico glade/soccer_ball.ico
fi

# Make a docs folder for the documentation.
if [ ! -d "docs" ] ; then
    mkdir "docs"
fi
if [ ! -e "docs/index.html" ] ; then
    ln -s _build/html/index.html docs/index.html
fi

# Make a Styles folder.
if [ ! -e "Styles" ] ; then
    mkdir Styles
fi

# Remove execute permission from everything.
chmod 600 * 2> /dev/null

# Add the execute permissions to directories.
chmod 700 $(ls -d */)

# Add execute permission to thoses files that require it.
chmod 700 *.sh
chmod 700 league-table.py


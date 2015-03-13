# Installation and Usage #

## Prerequisites ##
This plugin has been tested with Python 2.7.3.

I'm using supybot 0.83.4.1. As there are no information about the downward compatibility of supybot I recommend using at least this version.

Supybit needs PySVN installed. My version is 1.7.6.

## Install ##
Simply put the Sourcecode into a directory called `Subversion` into your supybot plugin directory.
You can load the plugin by performing the command
```
load Subversion
```
in your IRC client.

## Usage ##
You can use supybots builtin help system to get detailed information about the plugin. The following is an example of how to use the plugin. Note that my nickname here is 'monsdar' while the Bot is called 'Android':

```
<@monsdar> @load subversion
<@Android> monsdar: The operation succeeded.

<@monsdar> @subversion add #rde MainRepo http://supybot-plugin-subversion.googlecode.com/svn/trunk/
<@Android> monsdar: Adding Subversion Notifier 'MainRepo' to channel #rde with http://supybot-plugin-subversion.googlecode.com/svn/trunk/
<@Android> Subversion Notifier: Detected changes in 'MainRepo'. New Revision: 4
<@Android> 4 - Mar-31 20:17 - monsdar - Fixed: Wrong log output when less than 5 checkins
<@Android> 3 - Mar-31 20:14 - monsdar - Removed: Unnecessary verbose logging
<@Android> 2 - Mar-31 19:08 - monsdar - Initial Checkin
<@Android> 1 - Mar-31 19:03 - Initial directory structure.

<@monsdar> @subversion list
<@Android> #rde - MainRepo - http://supybot-plugin-subversion.googlecode.com/svn/trunk/

<@monsdar> @subversion remove MainRepo
<@Android> monsdar: Removed 'MainRepo'

<@monsdar> @unload Subversion
<@Android> monsdar: The operation succeeded.
```
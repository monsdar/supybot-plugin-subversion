###
# Copyright (c) 2013, Nils Brinkmann
# All rights reserved.
#
#
###

import time

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.schedule as schedule

try:
    import pysvn
except ImportError:
    raise callbacks.Error, 'You need to have PySVN installed to use this ' \
                           'plugin.  Download it at <http://pysvn.tigris.org/>'

    
class Helper(object):
    @staticmethod
    def getHeadRev(url):
        client = pysvn.Client()
        headRev = client.revpropget("revision", url=url)[0]
        return headRev
        
    @staticmethod
    def getHeadRevNum(url):
        return Helper.getHeadRev(url).number
        
    @staticmethod
    def getLogItemsByRange(url, startRevNum, endRevNum):
        #get the revisions and the log for them
        client = pysvn.Client()
        startRev = pysvn.Revision( pysvn.opt_revision_kind.number, startRevNum )
        endRev = pysvn.Revision( pysvn.opt_revision_kind.number, endRevNum )
        log = client.log(url, endRev, startRev)
        return log
        
    @staticmethod
    def getLastLogItems(url, numRevs):
        headRevNum = Helper.getHeadRevNum(url)
        startRevNum = headRevNum - numRevs
        return Helper.getLogItemsByRange(url, headRevNum, startRevNum)
        
    @staticmethod
    def logItemToString(logItem):
        #--> "\x02" for bold
        #--> "\x16" for italic/reverse
        #--> "\x1F" for underlined
        returnStr = ""
        if( 'revision' in logItem.data ):
            returnStr += "\x02" + str(logItem.revision.number) + "\x02" + " - "
        if( 'date' in logItem.data ):
            returnStr += time.strftime("%b-%d %H:%M", time.gmtime((logItem.date))) + " - "
        if( 'author' in logItem.data ):
            returnStr += "\x02" + logItem.author + "\x02" + " - "
        if( 'message' in logItem.data ):
            returnStr += logItem.message
        return returnStr

class Notifier(object):
    def __init__(self, irc, channel, name, url):
        self.irc = irc #needed to write output to IRC
        self.channel = channel
        self.name = name
        self.url = url
        
        #To init the lastRev, check for the current HEAD, then
        # subtract 5 revisions from that, so that something can be shown.
        #That's better than showing nothing or than showing everything
        self.lastRev = Helper.getHeadRevNum(self.url) - 5
        
    def check(self):
        headRev = Helper.getHeadRevNum(self.url)
        if(self.lastRev < headRev):
            message = "\x02Subversion Notifier:\x02 Detected changes in '" + self.name + "'. \x02New Revision: " + str(headRev) + "\x02"
            self.irc.queueMsg( ircmsgs.privmsg(self.channel, message) )
            self.irc.noReply()
            log = Helper.getLogItemsByRange(self.url, self.lastRev, headRev)
            for item in log:
                itemStr = Helper.logItemToString(item)
                self.irc.queueMsg( ircmsgs.privmsg(self.channel, itemStr) )
                self.irc.noReply()
            self.lastRev = headRev
        
class Subversion(callbacks.Plugin):
    """This plugin adds commands to gather information about a specific SVN repository."""
    
    def __init__(self, irc):
        self.__parent = super(Subversion, self)
        self.__parent.__init__(irc)
        
        #a dict is easier to search through
        #first: notifier.name
        #second: notifier
        self.notifiers = {};
        
    def die(self):
        #remove all the notifiers
        for key in self.notifiers.keys():
            schedule.removePeriodicEvent( self.notifiers[key].name )
            del self.notifiers[key]
            
        #kill the rest of the plugin
        self.__parent.die()    
    
    def getheadrev(self, irc, msg, args, url):
        """<url>

        Returns the HEAD revision number of the given <url>
        """
        irc.reply( Helper.getHeadRevNum(url) )
    getheadrev = wrap(getheadrev, ['text'])
        
    def svnlog(self, irc, msg, args, url, range=5):
        """<url> [<range>]

        Returns the last log entries from the Repository of <url>.
        The <range> let's you set a specific range of entries returned, defaults to 5.
        """
        #get the revisions and the log for them
        log = getLastLogItems(url, range)
        
        #output the results
        for item in log:
            itemStr = Helper.logItemToString(item)
            irc.reply( itemStr )        
    svnlog = wrap(svnlog, ['text', additional(('int', 'range'), 5)])
    
    def add(self, irc, msg, args, channel, name, url):
        """<channel> <name> <url>
        
        Adds a notifier with <name> of <url> to the given <channel>
        """
        
        #check if there is a notifier (do not add a second one, the scheduler does not allow that)
        if( name in self.notifiers ):
            irc.reply( "There already is a notifier called '" + name + "'" )
            return
        
        #needs to be printed before registering the event, because it will be executed immediately
        irc.reply( "Adding Subversion Notifier '" + name + "' to channel " + channel + " with " + url )
        
        notifier = Notifier(irc, channel, name, url)
        
        try:
            id = schedule.addPeriodicEvent(notifier.check, 5, name=name)
        except AssertionError:
            irc.reply( "There already is a notifier called '" + name + "'" )
            #this happens when the plugin was unloaded uncleanly
            #do nothing else, but add this event to the notifier list (so the user can remove it)
            
        self.notifiers[name] = notifier
    add = wrap(add, [('checkChannelCapability', 'op'), 'somethingWithoutSpaces', 'somethingWithoutSpaces'])
    
    
    def remove(self, irc, msg, args, name):
        """<name>
        
        Removes the notifier called <name>
        """
        if not(name in self.notifiers):
            irc.reply( "There is no notifier named '" + name + "'")
            return
        
        schedule.removePeriodicEvent(name)
        irc.reply( "Removed '" + name + "'")
        del self.notifiers[name]
    remove = wrap(remove, ['text'])
    
    def list(self, irc, msg, args, channel):
        """[<channel>]
        
        Lists all the Subversion notifiers
        Optionally posts the list in the given <channel>
        """
        for key, notifier in self.notifiers.items():
            output = ""
            output += notifier.channel + " - "
            output += notifier.name + " - "
            output += notifier.url
            irc.queueMsg( ircmsgs.privmsg(channel, output) )
            irc.noReply()
    list = wrap(list, ['channel'])

Class = Subversion


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

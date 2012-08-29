# Calladmin Plugin for BigBrotherBot
# Copyright (C) 2012 Mr.Click
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# CHANGELOG
#
# 29/08/2012 (v1.0 Mr.Click)
#  - initial release

import b3
import b3.plugin
import b3.events
import re

class AdminRequest:
    client = None
    reason = None
    time = None

class CalladminPlugin(b3.plugin.Plugin):
    
    _adminPlugin = None
    _teamspeakPlugin = None
    _mumblePlugin = None
    
    _adminRequest = None
       
    def onStartup(self):
        """\
        Initialize plugin settings
        """
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:    
            self.error('Could not find admin plugin')
            return False
        
        self._teamspeakPlugin = self.console.getPlugin('teamspeak')
        self._mumblePlugin = self.console.getPlugin('mumble')
        
        if self._teamspeakPlugin is None or self._mumblePlugin is None:
            self.error('This plugin need Teamspeak3 Plugin (courgette) or Mumble Plugin (BlackMamba) to work properly')
            return False
        
        #Register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2: cmd, alias = sp

                func = self.getCmd(cmd)
                if func: self._adminPlugin.registerCommand(self, cmd, level, func, alias)
        
        #Register the events needed
        self.registerEvent(b3.events.EVT_GAME_WARMUP)
        self.registerEvent(b3.events.EVT_CLIENT_CONNECT)
        self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)
               
    
    # ------------------------------------- Handle Events ------------------------------------- #        
        

    def onEvent(self, event):
        """\
        Handle intercepted events
        """
        if (event.type == b3.events.EVT_GAME_WARMUP):
            self.onWarmup()
        if (event.type == b3.events.EVT_CLIENT_CONNECT):
            self.onClientConnect(event)
        if (event.type == b3.events.EVT_CLIENT_DISCONNECT):
            self.onClientDisconnect(event)
                    
                           
    # --------------------------------------- Functions -------------------------------------- #
    
    
    def stripColors(self, s):
        """\
        Remove ioq3 color codes from a given string
        """
        return re.sub('\^[0-9]{1}','',s)
    
    
    def getHumanReadableTime(self, timestamp):
        """
        Return a string representing the Human Readable Time of the given timestamp
        """
        if timestamp < 60: 
            if timestamp == 1: return '%d second' % timestamp
            else: return '%d seconds' % timestamp
        elif timestamp >= 60 and timestamp < 3600:
            timestamp = round(timestamp/60)
            if timestamp == 1: return '%d minute' % timestamp
            else: return '%d minutes' % timestamp
        else:
            timestamp = round(timestamp/3600)
            if timestamp == 1: return '%d hour' % timestamp
            else: return '%d hours' % timestamp
     
     
    def getAdminRequest(self, client, reason):
        """
        Return an AdminRequest object
        """
        admReq = AdminRequest()
        admReq.client = client
        admReq.reason = reason
        admReq.time = int(self.console.time())
        return admReq
        
        
    def sendTeamspeakMessage(self, message):
        """\
        Send a message over the Teamspeak 3 server
        """
        self._teamspeakPlugin.tsSendCommand('sendtextmessage', { 'targetmode' : '3', 'target' : '1', 'msg' : message })  
 
 
    def sendMumbleMessage(self, message):
        """\
        Send a message over the Mumble (murmur) server
        """
        self._mumblePlugin.murmur.server.sendMessageChannel(0, False, message)
 
 
    def onWarmup(self):
        """\
        Handle Event Warmup
        """
        # Checking if there was a pending admin request
        # If so broadcast a message on the Teamspeak 3 server
        # and remove the AdminRequest object
        if self._adminRequest is not None:
            self.verbose('An admin request is still active but no admin connected on previous level. Discarding...')
            
            # Sending a message over the Teamspeak 3 server (if any)
            if self._teamspeakPlugin is not None:
                message = '[B][ADMIN REQUEST][/B] An admin request is still active but no admin connected on previous level. Discarding...'
                self.sendTeamspeakMessage(message)
            
            # Sending a message over the Mumble (murmur) server (if any)
            if self._mumblePlugin is not None:
                message = '<b>[ADMIN REQUEST]</b> An admin request is still active but no admin connected on previous level. Discarding...'
                self.sendMumbleMessage(message)
            
            # Removing the AdminRequest object
            self._adminRequest = None
      
      
    def onClientConnect(self, event):
        """\
        Handle Event Client Connect
        """
        # Checking if the connected client is an Admin on this server
        # If so informing the player who requested the admin (if still online)
        # and broadcasting a message on the Teamspeak 3 server
        if self._adminRequest is not None:
            
            if event.client.maxLevel >= self._adminPlugin._admins_level:
               
                # Sending a message over the Teamspeak 3 server (if any)
                if self._teamspeakPlugin is not None:
                    message = '[B][ADMIN REQUEST][/B] [B]%s[%d][/B] connected to server [B]%s[/B]' % (self.stripColors(event.client.name), event.client.maxLevel, self.stripColors(self.console.getCvar('sv_hostname').getString()))
                    self.sendTeamspeakMessage(message)
                
                # Sending a message over the Mumble (murmur) server (if any)
                if self._mumblePlugin is not None:
                    message = '<b>[ADMIN REQUEST]</b> <b>%s[%d]</b> connected to server <b>%s</b>' % (self.stripColors(event.client.name), event.client.maxLevel, self.stripColors(self.console.getCvar('sv_hostname').getString()))
                    self.sendMumbleMessage(message)
                
                # Informing the admin requester that an admin
                # connected to the server (if he is still online)
                if self._adminRequest.client is not None:
                    self._adminRequest.client.message('^2[ADMIN ONLINE] ^3%s ^7[^3%d^7]' % (self.stripColors(event.client.name), event.client.maxLevel))
                   
                # Since an admin connected we can remove this admin request
                # in order to be able to accept a new one
                self._adminRequest = None    
                    
          
    def onClientDisconnect(self, event):
        """\     
        Handle Event Client Disconnect  
        """ 
        # We need to check if the client who just disconnected
        # is the one who sent the Admin Request (if any)
        # If so we are going to remove the client object so no one
        # will get warned when an admin connect to the server
        if self._adminRequest is not None and self._adminRequest.client is not None:
            if self._adminRequest.client.id == event.client.id:
                # The player who issued the admin request
                # disconnected from the server.
                self.verbose('Admin request still active but request client disconnected from the server. No one to warn on admin connect.')
                self._adminRequest.client = None
        
          
    # --------------------------------------- Commands --------------------------------------- #
    
    
    def cmd_calladmin(self, data, client, cmd=None):
        """\
        <reason> - send an admin request
        """
        if not data:
            client.message('^7Missing data, try !help calladmin')
            return False
        
        # Checking if there are already admins online
        admins = self._adminPlugin.getAdmins()
        if len(admins) > 0:
            # Aborting admin request
            # There are already some admins online
            adminsList = []
            for a in admins:
                # Building the admins list
                adminsList.append('%s ^7[^3%s^7]' % (a.exactName, a.maxLevel))
            
            # Display a list of online admins
            cmd.sayLoudOrPM(client, '^3Admin request aborted')
            cmd.sayLoudOrPM(client, self._adminPlugin.getMessage('admins', ', '.join(adminsList)))
            return False
        
        # Checking if someone already submitted an admin request
        if self._adminRequest is not None:
            cmd.sayLoudOrPM(client, '^3Admin request aborted')
            cmd.sayLoudOrPM(client, '^3A request has already been sent ^7%s ^3ago' % self.getHumanReadableTime(int(self.console.time() - self._adminRequest.time())))
            return False
        
        # Building the AdminRequest object
        self._adminRequest = self.getAdminRequest(client, data)
        adminRequestSent = False
        
        # Sending the admin request over the Teamspeak 3 server (if any)
        if self._teamspeakPlugin is not None:
            try:
                message = '[B][ADMIN REQUEST][/B] [B]%s[/B] requested an admin [ SERVER: [B]%s[/B] | REASON: [B]%s[/B] ]' % (self.stripColors(self._adminRequest.client.name), self.stripColors(self.console.getCvar('sv_hostname').getString()), self.stripColors(self._adminRequest.reason))
                self.verbose('Sending an admin request over the Teamspeak 3 server.')
                self.sendTeamspeakMessage(message)
                adminRequestSent = True
            except Exception, e:
                self.debug('Error while broadcasting admin request over the Teamspeak 3 server: %s.' % e)
        
        # Sending the admin request over the Mumble server (if any)
        if self._mumblePlugin is not None:
            try:
                message = '<b>[ADMIN REQUEST]</b> <b>%s</b> requested an admin [ SERVER: <b>%s</b> | REASON: <b>%s</b> ]' % (self.stripColors(self._adminRequest.client.name), self.stripColors(self.console.getCvar('sv_hostname').getString()), self.stripColors(self._adminRequest.reason))
                self.verbose('Sending an admin request over the Mumble (murmur) server.')
                self.sendTeamspeakMessage(message)
                adminRequestSent = True
            except Exception, e:
                self.debug('Error while broadcasting admin request over the Mumble (murmur) server: %s.' % e)
    
        if adminRequestSent:
            # Informing the client of the successful sent request
            client.message('^3Admin request ^2sent^3. An admin will connect as soon as possible')
            return True
        
        # Informing the client of the failure and remove the AdminRequest object
        client.message('^3Admin request ^1failed^3. Try again in few minutes')
        self._adminRequest = None
        return False
        
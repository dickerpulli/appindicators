#!/usr/bin/env python
#
# Copyright 2009 Canonical Ltd.
#
# Authors: Neil Jagdish Patel <neil.patel@canonical.com>
#          Jono Bacon <jono@ubuntu.com>
#
# This program is free software: you can redistribute it and/or modify it 
# under the terms of either or both of the following licenses:
#
# 1) the GNU Lesser General Public License version 3, as published by the 
# Free Software Foundation; and/or
# 2) the GNU Lesser General Public License version 2.1, as published by 
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the applicable version of the GNU Lesser General Public 
# License for more details.
#
# You should have received a copy of both the GNU Lesser General Public 
# License version 3 and version 2.1 along with this program.  If not, see 
# <http://www.gnu.org/licenses/>
#

import gobject
import gtk
import appindicator
import os
import signal
import sys
import threading
import time

class SysTray:
  def __init__(self):
    self.pid = 0
    self.dialog = None
    self.indicator = self.create_indicator()
    menu_items = self.add_menu(self.indicator)
    gtk.timeout_add(1000, self.check_state, self.indicator, menu_items[0], menu_items[1], menu_items[2])
    
  def add_menu(self, indicator):
    # create a menu
    menu = gtk.Menu()

    # state
    menu_item_state = gtk.MenuItem('---')
    menu_item_state.set_sensitive(False)
    menu.append(menu_item_state)

    # separator
    menu.append(gtk.SeparatorMenuItem())
    
    # connect to vpn
    menu_item_connect = gtk.MenuItem('VPN verbinden')
    menu_item_connect.connect("activate", self.menuitem_response, '_connect')
    menu.append(menu_item_connect)
  
    # disconnect to vpn
    menu_item_disconnect = gtk.MenuItem('VPN trennen')
    menu_item_disconnect.connect("activate", self.menuitem_response, '_disconnect')
    menu_item_disconnect.set_sensitive(False)
    menu.append(menu_item_disconnect)
    
    # separator
    menu.append(gtk.SeparatorMenuItem())
    
    # quit indicator
    menu_item_quit = gtk.MenuItem('Beenden')
    menu_item_quit.connect("activate", self.menuitem_response, '_quit')
    menu.append(menu_item_quit)
    
    # show the items
    menu.show_all()
    
    # set menu
    indicator.set_menu(menu)
    return [menu_item_connect, menu_item_disconnect, menu_item_state]

  def create_indicator(self):
    indicator = appindicator.Indicator("example-simple-client",
                                 "nm-signal-0",
                                 appindicator.CATEGORY_APPLICATION_STATUS)
    indicator.set_status(appindicator.STATUS_ACTIVE)
    return indicator

  def responseToDialog(self, entry, dialog, response):
    dialog.response(response)

  def get_user_pw(self, parent, message, title=''):
    """
    Display a dialog with a text entry.
    Returns the text, or None if canceled.
    """
    self.dialog = gtk.MessageDialog(parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          gtk.MESSAGE_QUESTION,
                          gtk.BUTTONS_OK_CANCEL,
                          message)

    label = gtk.Label("Password")
    label.set_alignment(0.9,0)
    label.show()
    
    entry = gtk.Entry()
    entry.set_text(title)
    entry.set_visibility(False)
    entry.set_invisible_char("*")
    entry.show()

    label2 = gtk.Label("Password#2")
    label2.set_alignment(0.9,0)
    label2.show()
    
    entry2 = gtk.Entry()
    entry2.set_text(title)
    entry2.set_visibility(False)
    entry2.set_invisible_char("*")
    entry2.show()
    #allow the user to press enter to do ok
    entry2.connect("activate", self.responseToDialog, self.dialog, gtk.RESPONSE_OK)
    
    table = gtk.Table(2, 2, True)
    table.attach(label, 0, 1, 0, 1)
    table.attach(entry, 1, 2, 0, 1)
    table.attach(label2, 0, 1, 1, 2)
    table.attach(entry2, 1, 2, 1, 2)
    table.show()

    self.dialog.vbox.add(table)

    self.dialog.set_default_response(gtk.RESPONSE_OK)
  
    r = self.dialog.run()
    text = entry.get_text().decode('utf8')
    text2 = entry2.get_text().decode('utf8')
    self.dialog.destroy()
    self.dialog = None
    if r == gtk.RESPONSE_OK and text != '' and text2 != '':
      return [text, text2]
    else:
      return None
    
  def menuitem_response(self, w, item):
    if item == '_quit':
      os.kill(self.pid, signal.SIGTERM)
      self.pid = 0
      sys.exit(0)
    elif item == '_connect':
      if self.dialog == None:
        pwd = self.get_user_pw(None, 'Bitte geben Sie Ihre VPN Passwoerter ein')
        if pwd:
          home = os.environ['HOME']
          os.chdir(home + "/.juniper_networks/jvpn")
          self.pid = os.spawnl(os.P_NOWAIT, 'jvpn.pl', 'jvpn.pl', pwd[0], pwd[1])
          pidWaiter = PidWaiter(self.pid)
          pidWaiter.start()
    elif item == '_disconnect':
      os.kill(self.pid, signal.SIGTERM)
      self.pid = 0
    else:
      print item

  def check_state(self, indicator, menu_item_connect, menu_item_disconnect, menu_item_state):
    if os.path.exists('/tmp/jvpn.state') and self.pid != 0:
      menu_item_connect.set_sensitive(False)
      menu_item_disconnect.set_sensitive(True)
      f = open('/tmp/jvpn.state','r')
      menu_item_state.set_label(f.readline().strip())
      indicator.set_icon("nm-signal-100-secure")
    else:
      menu_item_connect.set_sensitive(True)
      menu_item_disconnect.set_sensitive(False)
      menu_item_state.set_label('---')
      indicator.set_icon("nm-signal-0")
    return True

class PidWaiter(threading.Thread):
  def __init__(self, pid):
    threading.Thread.__init__(self)
    self.pid = pid

  def run(self):
    os.wait4(self.pid, os.WUNTRACED)

if __name__ == "__main__":
  sysTray = SysTray()
  gtk.main()
  

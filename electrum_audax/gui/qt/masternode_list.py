#!/usr/bin/env python
#
# Electrum AUDAX - lightweight Audax client
# Copyright (C) 2019 The Audax Developers
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from enum import IntEnum

from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt5.QtCore import (Qt, QSortFilterProxyModel, QModelIndex, QAbstractItemModel,
                          QVariant, QItemSelectionModel)
from PyQt5.QtWidgets import (QMenu, QHeaderView, QMessageBox)

from electrum_audax.i18n import _
from electrum_audax.util import OrderedDictWithIndex, age, format_time

from .util import MyTreeView, MONOSPACE_FONT, WaitingDialog
from decimal import Decimal
from datetime import datetime, timedelta
from electrum_audax.logging import Logger

import traceback


class MasternodeList(MyTreeView, Logger):

    class Columns(IntEnum):
        ALIAS = 0
        ADDRESS = 1
        PROTOCOL_VERSION = 2
        STATUS = 3
        ACTIVE = 4
        LASTSEEN = 5
        COLLATERAL = 6

    headers = {
        Columns.ALIAS: _('Alias'),
        Columns.ADDRESS: _('Address'),
        Columns.PROTOCOL_VERSION: _('Protocol'),
        Columns.STATUS: _('Status'),
        Columns.ACTIVE: _('Active'),
        Columns.LASTSEEN: _('Last Seen'),
        Columns.COLLATERAL: _('Collateral Tx'),
    }

    def __init__(self, parent):
        super().__init__(parent, self.create_menu,
                         stretch_column=self.Columns.ALIAS,
                         editable_columns=[self.Columns.ALIAS])
        Logger.__init__(self)
        self.manager = None
        self.setModel(QStandardItemModel(self))
        self.setSortingEnabled(True)
        self.setColumnWidth(self.Columns.ALIAS, 180)
        self.header().setMinimumSectionSize(100)

    def create_menu(self, position):
        idx = self.indexAt(position)

        if not idx.isValid():
            return

        alias = self.model().itemFromIndex(
            idx.sibling(idx.row(), self.Columns.ALIAS)).text()
        transaction = self.model().itemFromIndex(idx.sibling(
            idx.row(), self.Columns.COLLATERAL)).text().split(':')[0]

        menu = QMenu()
        menu.addAction(_("Start Masternode"),
                       lambda: self.start_masternode(alias))
        menu.addAction(_("Copy Transaction"),
                       lambda: self.parent.app.clipboard().setText(transaction))
        menu.addSeparator()
        menu.addAction(_("Delete"), lambda: self.delete_masternode(alias))

        menu.addAction("Test", lambda: self.test_masternode(alias))
        menu.exec_(self.viewport().mapToGlobal(position))
        return

    def test_masternode(self, alias):
        # f99f2822b5e19c488eef220d95d8c7214b44ec25779341ae38292d95873020fb
        self.manager.populate_masternode_output(alias)
        self.manager.sign_announce(alias, None)

        mn = self.manager.get_masternode(alias)

        print(mn.private_key)
        print(mn.masternode_pubkey)

        print('01'+mn.serialize())

    def start_masternode(self, alias):
        """Sign an announce for alias. This is called by SignAnnounceWidget."""

        def broadcast_thread():
            return self.manager.send_announce(alias)

        def broadcast_done(result):
            mn = self.manager.get_masternode(alias)

            # TODO: Check broadcast status.
            print(mn.get_hash())

            # force masternode list reload.
            self.manager.send_subscriptions(True)

            QMessageBox.information(self, _('Success'), _(
                'Masternode activated successfully.'))

        def broadcast_error(err):
            self.logger.info(
                'Error sending Masternode Announce message: ' + str(err))
            # Print traceback information to error log.
            self.logger.info(''.join(traceback.format_tb(err[2])))
            self.logger.info(
                ''.join(traceback.format_exception_only(err[0], err[1])))

        pw = None
        if self.manager.wallet.has_password():
            pw = self.parent.password_dialog(
                msg=_('Please enter your password to activate masternode "%s".' % alias))
            if pw is None:
                return

        try:
            self.manager.populate_masternode_output(alias)
            self.manager.sign_announce(alias, pw)
        except Exception as e:
            QMessageBox.information(self, _('Error'), str(e))

        self.logger.info('Sending Masternode Announce message...')
        WaitingDialog(self, _('Broadcasting masternode...'),
                      broadcast_thread, broadcast_done, broadcast_error)

        return

    def delete_masternode(self, alias):
        if QMessageBox.question(self, _('Delete'), _('Do you want to remove the masternode configuration for') + ' %s?' % alias,
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            self.manager.remove_masternode(alias)
            self.update()

    def update(self):
        self.model().clear()
        self.update_headers(self.__class__.headers)

        if not self.manager:
            return

        for idx, mn in enumerate(self.manager.masternodes):
            mn_data = self.manager.masternode_data.get(mn.get_collateral_str())

            status = _('MISSING')
            ip = ''
            protocol_version = 0

            if mn.addr.ip:
                ip = str(mn.addr)

            activetime_str = _('Unknown')
            lastseen_str = _('Unknown')

            if mn_data is not None:
                protocol_version = mn_data['version']
                status = mn_data['status']
                if status == "ACTIVE":
                    activetime_str = _("Pending Activation")
                else:
                    activetime_str = age(
                        int((datetime.now() - timedelta(seconds=mn_data['activetime'])).timestamp()))
                lastseen_str = format_time(mn_data['lastseen'])

            labels = [mn.alias, ip, str(protocol_version), status, activetime_str, lastseen_str, mn.vin.get(
                'prevout_hash')+':'+str(mn.vin.get('prevout_n'))]

            items = [QStandardItem(e) for e in labels]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignVCenter)
                item.setEditable(i in self.editable_columns)

            items[self.Columns.ALIAS].setData(0, Qt.UserRole)

            self.model().insertRow(idx, items)

        self.set_current_idx(0)

        h = self.header()
        h.setStretchLastSection(False)
        for col in self.Columns:
            sm = QHeaderView.Stretch if col == self.stretch_column else QHeaderView.ResizeToContents
            h.setSectionResizeMode(col, sm)

    def on_edited(self, idx, user_role, text):
        item = self.model().itemFromIndex(idx.sibling(
            idx.row(), self.Columns.COLLATERAL)).text()

        for i, mn in enumerate(self.manager.masternodes):
            if item == mn.vin.get('prevout_hash')+':'+str(mn.vin.get('prevout_n')):
                if mn.alias != text:
                    self.manager.masternodes[i].alias = text
                    self.manager.save()
                break

#!/usr/bin/env python
#
# Electrum MUE - lightweight MonetaryUnit client
# Copyright (C) 2019 The MonetaryUnit Developers
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

from PyQt5.QtCore import QRect, QEventLoop, Qt, pyqtSignal
from PyQt5.QtGui import QPalette, QPen, QPainter, QPixmap, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QWidget, QDialog, QLabel, QHBoxLayout, QMessageBox,
                             QVBoxLayout, QLineEdit, QPushButton,
                             QGridLayout, QScrollArea, QFormLayout, QMenu)
from electrum_mue.base_wizard import BaseWizard, GoBack
from electrum_mue.i18n import _
from electrum_mue.util import UserCancelled
from electrum_mue.bitcoin import deserialize_privkey, serialize_privkey
from electrum_mue.masternode import NetworkAddress, MasternodeAnnounce
from .util import (read_QIcon, MessageBoxMixin, Buttons, icon_path, MyTreeView)
from electrum_mue import ecc

import os


class MasternodeWizard(QDialog, MessageBoxMixin, BaseWizard):

    accept_signal = pyqtSignal()

    def __init__(self, config, app, manager, parent):
        BaseWizard.__init__(self, config, None, None)
        QDialog.__init__(self, None)
        self.app = app
        self.gui = parent
        self.manager = manager
        self.setMinimumSize(600, 400)
        self.accept_signal.connect(self.accept)
        self.setWindowTitle('Electrum-MUE  -  ' + _('Masternode Wizard'))

        self.mn = MasternodeAnnounce()

        self.alias_e = None
        self.address_e = None
        self.privkey_e = None
        self.valid_utxo_list = None

        self.title = QLabel()
        self.main_widget = QWidget()
        self.back_button = QPushButton(_("Back"), self)
        self.back_button.setText(
            _('Back') if self.can_go_back() else _('Cancel'))
        self.next_button = QPushButton(_("Next"), self)
        self.next_button.setDefault(True)
        self.logo = QLabel()
        self.icon_filename = None
        self.loop = QEventLoop()
        self.rejected.connect(lambda: self.loop.exit(0))
        self.back_button.clicked.connect(lambda: self.loop.exit(1))
        self.next_button.clicked.connect(lambda: self.loop.exit(2))

        outer_vbox = QVBoxLayout(self)
        inner_vbox = QVBoxLayout()
        inner_vbox.addWidget(self.title)
        inner_vbox.addWidget(self.main_widget)
        inner_vbox.addStretch(1)
        # inner_vbox.addWidget(self.please_wait)
        inner_vbox.addStretch(1)
        scroll_widget = QWidget()
        scroll_widget.setLayout(inner_vbox)
        scroll = QScrollArea()
        scroll.setWidget(scroll_widget)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        icon_vbox = QVBoxLayout()
        icon_vbox.addWidget(self.logo)
        icon_vbox.addStretch(1)
        hbox = QHBoxLayout()
        hbox.addLayout(icon_vbox)
        hbox.addSpacing(5)
        hbox.addWidget(scroll)
        hbox.setStretchFactor(scroll, 1)
        outer_vbox.addLayout(hbox)
        outer_vbox.addLayout(Buttons(self.back_button, self.next_button))
        self.set_icon('electrum.png')
        self.show()
        self.raise_()
        self.refresh_gui()  # Need for QT on MacOSX.  Lame.

    def set_icon(self, filename):
        prior_filename, self.icon_filename = self.icon_filename, filename
        self.logo.setPixmap(QPixmap(icon_path(filename))
                            .scaledToWidth(60, mode=Qt.SmoothTransformation))
        return prior_filename

    def set_layout(self, layout, title=None, next_enabled=True):
        self.title.setText("<b>%s</b>" % title if title else "")
        self.title.setVisible(bool(title))
        # Get rid of any prior layout by assigning it to a temporary widget
        prior_layout = self.main_widget.layout()
        if prior_layout:
            QWidget().setLayout(prior_layout)
        self.main_widget.setLayout(layout)
        self.back_button.setEnabled(True)
        self.next_button.setEnabled(next_enabled)
        if next_enabled:
            self.next_button.setFocus()
        self.main_widget.setVisible(True)

    def exec_layout(self, layout, title=None, raise_on_cancel=True,
                    next_enabled=True):
        self.set_layout(layout, title, next_enabled)
        result = self.loop.exec_()
        if not result and raise_on_cancel:
            raise UserCancelled
        if result == 1:
            raise GoBack from None
        self.title.setVisible(False)
        self.back_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.main_widget.setVisible(False)
        self.please_wait.setVisible(True)
        self.refresh_gui()
        return result

    def refresh_gui(self):
        # For some reason, to refresh the GUI this needs to be called twice
        self.app.processEvents()
        self.app.processEvents()

    def run(self):
        vbox = QVBoxLayout()

        self.alias_e = QLineEdit()
        self.alias_e.setPlaceholderText(_('Choose a name for this masternode'))
        self.address_e = QLineEdit()
        self.address_e.setPlaceholderText(
            _('Address of your masternode (format: ip:port)'))
        self.privkey_e = QLineEdit()
        self.privkey_e.setPlaceholderText(
            _('Enter your masternode private key or generate one'))
        self.privkey_e_action = self.privkey_e.addAction(
            read_QIcon('key.png'), QLineEdit.TrailingPosition)
        self.privkey_e_action.triggered.connect(self.create_private_key)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow(_('Alias:'), self.alias_e)
        form.addRow(_('IP Address:'), self.address_e)
        form.addRow(_('Masternode Private Key:'), self.privkey_e)

        vbox.addLayout(form)

        self.set_layout(vbox, title=_(
            'Electrum-MUE - ' + _('Masternode Configuration')))

        while True:
            result = self.loop.exec_()
            if result != 2:  # 2 = next
                return

            if not self.alias_e.text():
                self.show_error(_("Choose a name for this masternode"))
                self.alias_e.setFocus()
                continue

            # TODO: Alias already exists

            if not self.address_e.text():
                self.show_error(_("Address of your masternode"))
                self.address_e.setFocus()
                continue

            # Check if maternode address is valid
            try:
                addr = NetworkAddress(self.address_e.text())
            except:
                self.show_error(_("Invalid network address"))
                self.address_e.setFocus()
                continue

            # check private key
            if not self.privkey_e.text():
                self.show_error(_("Enter your masternode private key"))
                self.privkey_e.setFocus()
                continue

            try:
                deserialize_privkey('p2pkh:'+self.privkey_e.text())
            except:
                self.show_error(_("Invalid private key"))
                self.privkey_e.setFocus()
                continue

            self.mn.alias = self.alias_e.text()
            self.mn.addr = addr
            self.mn.private_key = self.privkey_e.text()

            txin_type, privkey, compressed = deserialize_privkey(
                'p2pkh:'+self.mn.private_key)
            self.mn.masternode_pubkey = ecc.ECPrivkey(
                privkey).get_public_key_hex(compressed=compressed)

            self.choose_utxo()
            break

        return True

    def choose_utxo(self):
        vbox = QVBoxLayout()

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)

        title = QLabel(
            _('Choose a collateral payment for your masternode. A valid collateral payment is exactly 2500 MUE.'))
        title.setWordWrap(True)
        form.addRow(title)

        self.valid_utxo_list = MasternodeOutputsWidget(self)
        form.addRow(self.valid_utxo_list)

        vbox.addLayout(form)

        self.valid_utxo_list.update()
        self.set_layout(vbox, title=_(
            'Electrum-MUE - ' + _('Choose collateral')))

        while True:
            result = self.loop.exec_()
            if result != 2:  # 2 = next
                return

            idx = self.valid_utxo_list.currentIndex()
            item = self.valid_utxo_list.model().itemFromIndex(
                idx.sibling(idx.row(), self.valid_utxo_list.Columns.TXID))

            if not item:
                continue

            txid = item.text().split(':')

            self.mn.vin = {'prevout_hash': txid[0], 'prevout_n': int(txid[1])}

            self.add_masternode()
            break
        return True

    def add_masternode(self):
        self.manager.add_masternode(self.mn)
        self.manager.wallet.network.trigger_callback('masternodes')

    def terminate(self):
        self.accept_signal.emit()

    def create_private_key(self):
        private_key = serialize_privkey(os.urandom(32), False, 'p2pkh', False)
        self.privkey_e.setText(private_key.split(':')[1])


class MasternodeOutputsWidget(MyTreeView):
    class Columns(IntEnum):
        ADDRESS = 0
        LABEL = 1
        TXID = 2

    def __init__(self, parent):
        super().__init__(parent, self.create_menu,
                         stretch_column=self.Columns.ADDRESS,
                         editable_columns=[])
        self.setModel(QStandardItemModel(self))
        self.setSortingEnabled(True)
        self.setColumnWidth(self.Columns.ADDRESS, 180)

    headers = {
        Columns.ADDRESS: _('Address'),
        Columns.LABEL: _('Label'),
        Columns.TXID: _('Transaction'),
    }

    def create_menu(self, position):
        idx = self.indexAt(position)

        if not idx.isValid():
            return

        address = self.model().itemFromIndex(idx.sibling(idx.row(), self.Columns.ADDRESS))
        transaction = self.model().itemFromIndex(
            idx.sibling(idx.row(), self.Columns.TXID))

        menu = QMenu()
        menu.addAction(
            _("Copy Address"), lambda: self.parent.app.clipboard().setText(address.text()))
        menu.addAction(_("Copy Transaction"), lambda: self.parent.app.clipboard(
        ).setText(transaction.text().split(':')[0]))
        menu.exec_(self.viewport().mapToGlobal(position))

        return

    def update(self):
        self.model().clear()
        self.update_headers(self.__class__.headers)

        available_coins = []
        coins = list(self.parent.manager.get_masternode_outputs())
        if not len(coins):
            return

        # exclude already used UTXOs from configured mn
        used_utxos = []
        for mn in self.parent.manager.masternodes:
            used_utxos.append(mn.vin['prevout_hash'] +
                              ':'+str(mn.vin['prevout_n']))

        for coin in coins:
            if not coin.get('prevout_hash')+':'+str(coin.get('prevout_n')) in used_utxos:
                available_coins.append(coin)

        for idx, coin in enumerate(available_coins):
            label = self.parent.manager.wallet.get_label(
                coin.get('prevout_hash'))

            labels = [coin.get('address'), label, coin.get(
                'prevout_hash')+':'+str(coin.get('prevout_n'))]

            items = [QStandardItem(e) for e in labels]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignVCenter)
                item.setEditable(i in self.editable_columns)
            self.model().insertRow(idx, items)

        self.set_current_idx(0)

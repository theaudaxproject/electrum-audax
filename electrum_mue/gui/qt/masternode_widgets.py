"""Masternode-related widgets."""

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from electrum_mue import bitcoin
from electrum_mue.bitcoin import COIN
from electrum_mue.i18n import _
from electrum_mue.masternode import NetworkAddress, MasternodeAnnounce

from . import util

def masternode_status(status):
    """Get a human-friendly representation of status.

    Returns a 3-tuple of (enabled, one_word_description, description).
    """
    statuses = {
        'PRE_ENABLED': (True, _('Enabling'), _('Waiting for masternode to enable itself.')),
        'ENABLED': (True, _('Enabled'), _('Masternode is enabled.')),
        'EXPIRED': (False, _('Disabled'), _('Masternode failed to ping the network and was disabled.')),
        'VIN_SPENT': (False, _('Disabled'), _('Collateral payment has been spent.')),
        'REMOVE': (False, _('Disabled'), _('Masternode failed to ping the network and was disabled.')),
    }
    if statuses.get(status):
        return statuses[status]
    elif status is False:
        return (False, _('N/A'), _('Masternode has not been seen on the network.'))
    return (False, _('Unknown'), _('Unknown masternode status.'))

class NetworkAddressWidget(QWidget):
    """Widget that represents a network address."""
    def __init__(self, parent=None):
        super(NetworkAddressWidget, self).__init__(parent)
        self.address_e = QLineEdit()

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(QLabel(_('Address:')))
        hbox.addWidget(self.address_e, stretch=1)
        self.setLayout(hbox)

    @pyqtProperty(str)
    def string(self):
        return self.address_e.text()

    @string.setter
    def string(self, value):
        self.address_e.setText(value)

    def get_addr(self):
        """Get a NetworkAddress instance from this widget's data."""
        try:
             return NetworkAddress(self.address_e.text())
        except:
            return NetworkAddress()



class PrevOutWidget(QWidget):
    """Widget that represents a previous outpoint."""
    def __init__(self, parent=None):
        super(PrevOutWidget, self).__init__(parent)
        self.vin = {}
        self.hash_edit = QLineEdit()
        self.hash_edit.setPlaceholderText(_('The TxID of your 2500 MUE output'))
        self.index_edit = QLineEdit()
        self.index_edit.setPlaceholderText(_('The output number of your 2500 MUE output'))
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText(_('The address that 2500 MUE was sent to'))

        # Collection of fields so that it's easier to act on them all at once.
        self.fields = (self.hash_edit, self.index_edit, self.address_edit)
        for i in self.fields:
            i.setFont(QFont(util.MONOSPACE_FONT))

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow(_('TxID:'), self.hash_edit)
        form.addRow(_('Output Index:'), self.index_edit)
        form.addRow(_('Address:'), self.address_edit)
        self.setLayout(form)

    @pyqtProperty(str)
    def string(self):
        return self.get_str()

    @string.setter
    def string(self, value):
        return self.set_str(str(value))

    def get_str(self):
        values = [str(self.hash_edit.text()), str(self.index_edit.text()), str(self.address_edit.text())]
        values.append(str(self.vin.get('value', '')))
        values.append(self.vin.get('scriptSig', ''))
        return ':'.join(values)

    def set_str(self, value):
        s = str(value).split(':')
        values = []
        try:
            values.append(('prevout_hash', s[0]))
            values.append(('prevout_n', int(s[1])))
            values.append(('address', s[2]))
            values.append(('value', int(s[3])))
            values.append(('scriptSig', s[4]))
        # Don't fail if not all values are present.
        except (IndexError, ValueError):
            pass

        vin = {k: v for k, v in values}
        self.set_dict(vin)

    def get_dict(self):
        d = {}
        txid = str(self.hash_edit.text())
        if not txid:
            return d
        index = str(self.index_edit.text())
        if not index:
            index = '0'
        address = str(self.address_edit.text())
        d['prevout_hash'] = txid
        d['prevout_n'] = int(index)
        d['address'] = address
        if self.vin:
            d['value'] = int(self.vin.get('value', '0'))
            d['scriptSig'] = self.vin.get('scriptSig', '')
        return d

    def set_dict(self, d):
        self.hash_edit.setText(d.get('prevout_hash', ''))
        self.index_edit.setText(str(d.get('prevout_n', '')))
        self.address_edit.setText(d.get('address', ''))
        self.vin = dict(d)

    def clear(self):
        for widget in self.fields:
            widget.clear()
        self.vin = {}

    def setReadOnly(self, isreadonly):
        for widget in self.fields:
            widget.setReadOnly(isreadonly)

class MasternodeEditor(QWidget):
    """Editor for masternodes."""
    def __init__(self, parent=None):
        super(MasternodeEditor, self).__init__(parent)

        self.alias_edit = QLineEdit()
        self.alias_edit.setPlaceholderText(_('Enter a name for this masternode'))

        self.vin_edit = PrevOutWidget()

        self.addr_edit = NetworkAddressWidget()
        self.private_key_edit = QLineEdit()
        self.private_key_edit.setFont(QFont(util.MONOSPACE_FONT))
        self.private_key_edit.setPlaceholderText(_('Your masternode\'s private key'))
        self.protocol_version_edit = QLineEdit()
        self.protocol_version_edit.setText('70201')

        self.status_edit = QLineEdit()
        self.status_edit.setPlaceholderText(_('Masternode status'))
        self.status_edit.setReadOnly(True)

        form = QFormLayout()
        form.addRow(_('Alias:'), self.alias_edit)
        form.addRow(_('Status:'), self.status_edit)
        form.addRow(_('Collateral MUE Output:'), self.vin_edit)
        form.addRow(_('Masternode Private Key:'), self.private_key_edit)
        form.addRow(_('Address:'), self.addr_edit)
        form.addRow(_('Protocol Version:'), self.protocol_version_edit)

        self.setLayout(form)

    def get_masternode_args(self):
        """Get MasternodeAnnounce keyword args from this widget's data."""
        kwargs = {}
        kwargs['alias'] = str(self.alias_edit.text())
        kwargs['vin'] = self.vin_edit.get_dict()
        kwargs['addr'] = self.addr_edit.get_addr()
        protocol_version = str(self.protocol_version_edit.text())
        if protocol_version:
            kwargs['protocol_version'] = int(protocol_version)
        return kwargs

class MasternodeOutputsWidget(QListWidget):
    """Widget that displays available masternode outputs."""
    outputSelected = pyqtSignal(dict, name='outputSelected')
    def __init__(self, parent=None):
        super(MasternodeOutputsWidget, self).__init__(parent)
        self.outputs = {}
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def sizeHint(self):
        return QSize(256, 60)

    def add_output(self, d):
        """Add a valid output."""
        label = '%s:%s' % (d['prevout_hash'], d['prevout_n'])
        self.outputs[label] = d
        item = QListWidgetItem(label)
        item.setFont(QFont(util.MONOSPACE_FONT))
        self.addItem(item)

    def add_outputs(self, outputs):
        list(map(self.add_output, outputs))
        self.setCurrentRow(0)

    def clear(self):
        super(MasternodeOutputsWidget, self).clear()
        self.outputs.clear()

    def on_selection_changed(self, selected, deselected):
        """Emit the selected output."""
        items = self.selectedItems()
        if not items:
            return
        self.outputSelected.emit(self.outputs[str(items[0].text())])

class SignAnnounceWidget(QWidget):
    """Widget that displays information about signing a Masternode Announce."""
    def __init__(self, parent):
        super(SignAnnounceWidget, self).__init__(parent)
        self.dialog = parent
        self.manager = parent.manager

        # Displays the status of the masternode.
        self.status_edit = QLineEdit()
        self.status_edit.setReadOnly(True)

        self.alias_edit = QLineEdit()
        self.collateral_edit = PrevOutWidget()
        self.delegate_edit = QLineEdit()
        self.delegate_edit.setFont(QFont(util.MONOSPACE_FONT))

        for i in [self.alias_edit, self.collateral_edit, self.delegate_edit]:
            i.setReadOnly(True)

        self.mapper = QDataWidgetMapper()
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.setModel(self.dialog.masternodes_widget.proxy_model)

        model = self.dialog.masternodes_widget.model
        self.mapper.addMapping(self.alias_edit, model.ALIAS)
        self.mapper.addMapping(self.collateral_edit, model.VIN, b'string')
        self.mapper.addMapping(self.delegate_edit, model.DELEGATE)

        self.sign_button = QPushButton(_('Activate Masternode'))
        self.sign_button.setEnabled(False)
        self.sign_button.clicked.connect(self.sign_announce)

        status_box = QHBoxLayout()
        status_box.setContentsMargins(0, 0, 0, 0)
        status_box.addWidget(QLabel(_('Status:')))
        status_box.addWidget(self.status_edit, stretch=1)

        vbox = QVBoxLayout()
        vbox.addLayout(status_box)

        form = QFormLayout()
        form.addRow(_('Alias:'), self.alias_edit)
        form.addRow(_('Collateral MUE Output:'), self.collateral_edit)
        form.addRow(_('Masternode Private Key:'), self.delegate_edit)
        vbox.addLayout(form)
        vbox.addLayout(util.Buttons(self.sign_button))
        self.setLayout(vbox)

    def set_mapper_index(self, row):
        """Set the row that the data widget mapper should use."""
        self.status_edit.clear()
        self.status_edit.setStyleSheet(util.ColorScheme.DEFAULT.as_stylesheet())
        self.mapper.setCurrentIndex(row)
        mn = self.dialog.masternodes_widget.masternode_for_row(row)

        # Disable the sign button if the masternode can't be signed (for whatever reason).
        status_text = '%s can be activated' % mn.alias
        can_sign = True
        try:
            self.manager.check_can_sign_masternode(mn.alias)
        except Exception as e:
            status_text = str(e)
            can_sign = False

        self.status_edit.setText(_(status_text))
        self.sign_button.setEnabled(can_sign)

    def sign_announce(self):
        """Set the masternode's vin and sign an announcement."""
        self.mapper.submit()
        self.dialog.sign_announce(str(self.alias_edit.text()))


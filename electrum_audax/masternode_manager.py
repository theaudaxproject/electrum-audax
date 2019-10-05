from collections import namedtuple, OrderedDict
import base64
import threading
import asyncio
import time
from decimal import Decimal

from . import bitcoin
from . import ecc
from .blockchain import hash_header
from .masternode import MasternodeAnnounce, NetworkAddress
from .util import AlreadyHaveAddress, bfh
from .util import format_satoshis_plain
from .logging import Logger

# From masternode.h
MASTERNODE_MIN_CONFIRMATIONS = 15

MasternodeConfLine = namedtuple('MasternodeConfLine', ('alias', 'addr',
                                                       'wif', 'txid', 'output_index'))


def parse_masternode_conf(lines):
    """Construct MasternodeConfLine instances from lines of a masternode.conf file."""
    conf_lines = []
    for line in lines:
        # Comment.
        if line.startswith('#'):
            continue

        s = line.split(' ')
        if len(s) < 5:
            continue
        alias = s[0]
        addr_str = s[1]
        masternode_wif = 'p2pkh:'+s[2]
        collateral_txid = s[3]
        collateral_output_n = s[4]

        # Validate input.
        try:
            txin_type, key, is_compressed = bitcoin.deserialize_privkey(
                masternode_wif)
            assert key
        except Exception:
            raise ValueError(
                'Invalid masternode private key of alias "%s"' % alias)

        if len(collateral_txid) != 64:
            raise ValueError(
                'Transaction ID of alias "%s" must be 64 hex characters.' % alias)

        try:
            collateral_output_n = int(collateral_output_n)
        except ValueError:
            raise ValueError(
                'Transaction output index of alias "%s" must be an integer.' % alias)

        conf_lines.append(MasternodeConfLine(
            alias, addr_str, masternode_wif, collateral_txid, collateral_output_n))
    return conf_lines


class MasternodeManager(Logger):
    """Masternode manager.

    Keeps track of masternodes and helps with signing broadcasts.
    """

    def __init__(self, wallet, config):
        Logger.__init__(self)
        self.network_event = threading.Event()
        self.wallet = wallet
        self.config = config
        self.masternode_data = {}
        self.last_check = 0
        self.load()

    def load(self):
        """Load masternodes from wallet storage."""
        masternodes = self.wallet.storage.get('masternodes', {})
        self.masternodes = [MasternodeAnnounce.from_dict(
            d) for d in masternodes.values()]

    def send_subscriptions(self, force=False):

        # Check last pull, prevent multiple pull requests
        if not force and time.time() - self.last_check < 60:
            return
        self.last_check = time.time()

        if not self.wallet.network.is_connected():
            return

        mns = []
        for mn in self.masternodes:
            collateral = mn.get_collateral_str()
            if not '-' in collateral or len(collateral.split('-')[0]) != 64:
                continue

            mns.append(collateral)

        res = self.wallet.network.run_from_another_thread(
            self.wallet.network.list_masternodes(mns))
        self.masternode_subscription_response(res)

    def masternode_subscription_response(self, masternodes):
        """Callback for when a masternode's status changes."""

        for response in masternodes:
            print(response)
            # if self.masternode_data.get(collateral) is None:
            #     res = await self.wallet.network.subscribe_masternode(collateral)
            #     print("RECEIVED RESPONSE: " + res)

            if not response or not 'vin' in response:
                self.wallet.network.trigger_callback('masternodes')
                return

            mn = None
            for masternode in self.masternodes:
                if masternode.get_collateral_str() == response['vin']:
                    mn = masternode
                    break

            if not mn:
                self.wallet.network.trigger_callback('masternodes')
                return

            status = response['status']
            if status is None:
                status = False
            self.masternode_data[response['vin']] = response
        self.wallet.network.trigger_callback('masternodes')

    def get_masternode(self, alias):
        """Get the masternode labelled as alias."""
        for mn in self.masternodes:
            if mn.alias == alias:
                return mn

    def add_masternode(self, mn, save=True):
        """Add a new masternode."""
        if any(i.alias == mn.alias for i in self.masternodes):
            raise Exception(
                'A masternode with alias "%s" already exists' % mn.alias)
        self.masternodes.append(mn)
        if save:
            self.save()

    def remove_masternode(self, alias, save=True):
        """Remove the masternode labelled as alias."""
        mn = self.get_masternode(alias)
        if not mn:
            raise Exception('Nonexistent masternode')

        self.masternodes.remove(mn)
        if save:
            self.save()

    def populate_masternode_output(self, alias):
        """Attempt to populate the masternode's data using its output."""
        mn = self.get_masternode(alias)
        if not mn:
            return
        if mn.announced:
            return
        txid = mn.vin.get('prevout_hash')
        prevout_n = mn.vin.get('prevout_n')
        if not txid or prevout_n is None:
            return
        # Return if it already has the information.
        if mn.collateral_key and mn.vin.get('address') and mn.vin.get('value') == 2500 * bitcoin.COIN:
            return

        tx = self.wallet.transactions.get(txid)
        if not tx:
            return
        if len(tx.outputs()) <= prevout_n:
            return
        _, addr, value = tx.outputs()[prevout_n]
        mn.vin['address'] = addr
        mn.vin['value'] = value
        mn.vin['scriptSig'] = ''

        mn.collateral_key = self.wallet.get_public_keys(addr)[0]
        self.save()
        return True

    def get_masternode_outputs(self, domain=None):
        """Get spendable coins that can be used as masternode collateral."""
        coins = self.wallet.get_utxos(domain,
                                      mature=True, confirmed_only=True, unlocked_only=True)

        used_vins = map(lambda mn: '%s:%d' % (mn.vin.get(
            'prevout_hash'), mn.vin.get('prevout_n', 0xffffffff)), self.masternodes)

        def unused(d): return '%s:%d' % (
            d['prevout_hash'], d['prevout_n']) not in used_vins

        def correct_amount(d): return d['value'] == 2500 * bitcoin.COIN

        # Valid outputs have a value of exactly 2500 AUDAX and
        # are not in use by an existing masternode.
        def is_valid(d): return correct_amount(d) and unused(d)

        coins = filter(is_valid, coins)
        return coins

    def save(self):
        """Save masternodes."""
        masternodes = {}

        for mn in self.masternodes:
            masternodes[mn.alias] = mn.dump()

        self.wallet.storage.put('masternodes', masternodes)

    def check_can_sign_masternode(self, alias):
        """Raise an exception if alias can't be signed and announced to the network."""
        mn = self.get_masternode(alias)
        if not mn:
            raise Exception('Nonexistent masternode')
        if not mn.vin.get('prevout_hash'):
            raise Exception('Collateral payment is not specified')
        if not mn.collateral_key:
            raise Exception('Collateral key is not specified')
        if not mn.private_key:
            raise Exception('Masternode private key is not specified')
        if not mn.addr.ip:
            raise Exception('Masternode has no IP address')

        # Ensure that the collateral payment has >= MASTERNODE_MIN_CONFIRMATIONS.
        tx_height = self.wallet.get_tx_height(mn.vin['prevout_hash'])
        if tx_height.conf < MASTERNODE_MIN_CONFIRMATIONS:
            raise Exception('Collateral payment must have at least %d confirmations (current: %d)' % (
                MASTERNODE_MIN_CONFIRMATIONS, tx_height.conf))

        # Ensure that the masternode's vin is valid.
        if mn.vin.get('value', 0) != bitcoin.COIN * 2500:
            raise Exception(
                'Masternode requires a collateral 2500 AUDAX output.')

        # If the masternode has been announced, it can be announced again if it has been disabled.
        if mn.announced:
            mn_data = self.masternode_data.get(mn.get_collateral_str())
            if mn_data and mn_data['status'] in ['PRE_ENABLED', 'ENABLED']:
                raise Exception('Masternode has already been activated')

    def sign_announce(self, alias, password):
        """Sign a Masternode Announce message for alias."""
        self.check_can_sign_masternode(alias)
        mn = self.get_masternode(alias)

        # Ensure that the masternode's vin is valid.
        if mn.vin.get('scriptSig') is None:
            mn.vin['scriptSig'] = ''
        if mn.vin.get('sequence') is None:
            mn.vin['sequence'] = 0xffffffff

        # Ensure that the masternode's last_ping is current.
        height = self.wallet.get_local_height() - 12
        blockchain = self.wallet.network.blockchain()
        header = blockchain.read_header(height)
        mn.last_ping.block_hash = hash_header(header)
        mn.last_ping.vin = mn.vin

        # Sign ping with private key.
        mn.last_ping.sign(mn.private_key)

        # After creating the Masternode Ping, sign the Masternode Announce.
        address = bitcoin.public_key_to_p2pkh(bfh(mn.collateral_key))
        mn.sig = self.wallet.sign_message(
            address, mn.serialize_for_sig(update_time=True), password)

        return mn

    def send_announce(self, alias):
        """Broadcast a Masternode Announce message for alias to the network.

        Returns a response from server.
        """
        if not self.wallet.network.is_connected():
            raise Exception('Not connected')

        mn = self.get_masternode(alias)

        # Vector-serialize the masternode.
        serialized = '01' + mn.serialize()

        print(serialized)

        return self.wallet.network.run_from_another_thread(self.wallet.network.broadcast_masternode(serialized))

    def broadcast_announce_callback(self, alias, errmsg, r):
        """Callback for when a Masternode Announce message is broadcasted."""
        try:
            self.on_broadcast_announce(alias, r)
        except Exception as e:
            errmsg.append(str(e))
        finally:
            self.save()
            self.network_event.set()

    def on_broadcast_announce(self, alias, r):
        """Validate the server response."""
        err = r.get('error')
        if err:
            raise Exception('Error response: %s' % str(err))

        result = r.get('result')

        mn = self.get_masternode(alias)
        mn_hash = mn.get_hash()
        mn_dict = result.get(mn_hash)
        if not mn_dict:
            raise Exception(
                'No result for expected Masternode Hash. Got %s' % result)

        if mn_dict.get('errorMessage'):
            raise Exception('Announce was rejected: %s' %
                            mn_dict['errorMessage'])
        if mn_dict.get(mn_hash) != 'successful':
            raise Exception(
                'Announce was rejected (no error message specified)')

        mn.announced = True

    def import_masternode_delegate(self, sec):
        """Import a WIF delegate key.

        An exception will not be raised if the key is already imported.
        """
        try:
            pubkey = self.wallet.import_masternode_delegate(sec)
        except AlreadyHaveAddress:
            txin_type, key, is_compressed = bitcoin.deserialize_privkey(sec)
            pubkey = ecc.ECPrivkey(key)\
                .get_public_key_hex(compressed=is_compressed)
        return pubkey

    def import_masternode_conf_lines(self, conf_lines, password):
        """Import a list of MasternodeConfLine."""
        def already_have(line):
            for masternode in self.masternodes:
                # Don't let aliases collide.
                if masternode.alias == line.alias:
                    return True
                # Don't let outputs collide.
                if masternode.vin.get('prevout_hash') == line.txid and masternode.vin.get('prevout_n') == line.output_index:
                    return True
            return False

        num_imported = 0
        for conf_line in conf_lines:
            if already_have(conf_line):
                continue
            # Import delegate WIF key for signing last_ping.
            public_key = self.import_masternode_delegate(conf_line.wif)

            addr = conf_line.addr.split(':')
            addr = NetworkAddress(addr[0]+":"+addr[1])
            vin = {'prevout_hash': conf_line.txid,
                   'prevout_n': conf_line.output_index}
            mn = MasternodeAnnounce(alias=conf_line.alias, vin=vin,
                                    private_key=conf_line.wif, addr=addr)
            self.add_masternode(mn)
            try:
                self.populate_masternode_output(mn.alias)
            except Exception as e:
                self.logger.error(str(e))
            num_imported += 1

        return num_imported

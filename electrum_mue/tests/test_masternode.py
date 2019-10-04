import unittest
import base64

from electrum_mue.masternode import MasternodeAnnounce, MasternodePing, NetworkAddress
from electrum_mue.masternode_manager import parse_masternode_conf, MasternodeConfLine
from electrum_mue import bitcoin
from electrum_mue import ecc
from electrum_mue.util import bfh, to_bytes

raw_announce = '01e644df0b5f7678fc436625c7e230fbd9818dd0f48257eefba8383615e54b0c830000000000ffffffff00000000000000000000ffffc0a80164247521037d9e564410f61decaf396b479d20806f51640793513ddf3b7deaf318f183c4a64104799d9f00e4c566ae529a499adcfd6af07d5396484b957af5dee8107650c75a0449323a2a1ebcdc7595f139c1d04bf8b328d5a48913e369d0a80b56f91c39781641202d0dfaa159ab8e8e25a0568d4cd9460c842c0a84f5d4dd0e0130bd1a6b6de54457c67520421fa874a55dae131944da66d34b6b1390408194fa4f558b9879e86388fe995c0000000002150100e644df0b5f7678fc436625c7e230fbd9818dd0f48257eefba8383615e54b0c830000000000ffffffff0f499079c2b591eb4a94d6c19e2323d47f0810981dd5a5faca6b69a76dc4af6188fe995c00000000411c0389888b5e54a781450cb208696ff8ecc29823e79c0b9f08f5d1336b9fa5e93137a3510ef89426eaec0a3bff98327f5e8ca4d1757e4f439ea2ab7c90e9ef548f0000000000000000'

class TestMasternode(unittest.TestCase):
    def test_serialization(self):
        announce = MasternodeAnnounce.deserialize(raw_announce)

        self.assertEqual('830c4be5153638a8fbee5782f4d08d81d9fb30e2c7256643fc78765f0bdf44e6', announce.vin['prevout_hash'])
        self.assertEqual(0, announce.vin['prevout_n'])
        self.assertEqual('', announce.vin['scriptSig'])
        self.assertEqual(0xffffffff, announce.vin['sequence'])

        self.assertEqual('192.168.1.100:9333', str(announce.addr))

        self.assertEqual('037d9e564410f61decaf396b479d20806f51640793513ddf3b7deaf318f183c4a6', announce.collateral_key)
        self.assertEqual('04799d9f00e4c566ae529a499adcfd6af07d5396484b957af5dee8107650c75a0449323a2a1ebcdc7595f139c1d04bf8b328d5a48913e369d0a80b56f91c397816', announce.masternode_pubkey)
        self.assertEqual('IC0N+qFZq46OJaBWjUzZRgyELAqE9dTdDgEwvRprbeVEV8Z1IEIfqHSlXa4TGUTaZtNLaxOQQIGU+k9Vi5h56GM=', base64.b64encode(announce.sig).decode('utf-8'))
        self.assertEqual(1553596040, announce.sig_time)
        self.assertEqual(70914, announce.protocol_version)

        self.assertEqual('830c4be5153638a8fbee5782f4d08d81d9fb30e2c7256643fc78765f0bdf44e6', announce.last_ping.vin['prevout_hash'])
        self.assertEqual(0, announce.last_ping.vin['prevout_n'])
        self.assertEqual('', announce.last_ping.vin['scriptSig'])
        self.assertEqual(0xffffffff, announce.last_ping.vin['sequence'])
        self.assertEqual('61afc46da7696bcafaa5d51d9810087fd423239ec1d6944aeb91b5c27990490f', announce.last_ping.block_hash)
        self.assertEqual(1553596040, announce.last_ping.sig_time)
        self.assertEqual('HAOJiIteVKeBRQyyCGlv+OzCmCPnnAufCPXRM2ufpekxN6NRDviUJursCjv/mDJ/Xoyk0XV+T0Oeoqt8kOnvVI8=', base64.b64encode(announce.last_ping.sig).decode('utf-8'))

        self.assertEqual(raw_announce, '01'+announce.serialize())

    def test_create_and_sign(self):
        collateral_pub = '02a6eeee0b2ec1bea855d555f8a5c78cb4854fb95d7034d1f0150d69965f8eb866' # GLosAyGUGzvqT4fxpzFCosY8f6ZZdQyXJt
        masternode_pubkey = '03b9c1d8b9d76ee0ff1247d6e36c1b34399c61fa168e65f83ea4c73b5c34e629ce' # GaToqaVr9GDZEUQ8xdxNXesFoiMUntNbSw
        protocol_version = 70914

        ip = '0.0.0.0'
        port = 9333
        addr = NetworkAddress(ip+':'+str(port))

        vin = {'prevout_hash': '00'*32, 'prevout_n': 0, 'scriptSig': '', 'sequence':0xffffffff}

        last_ping = MasternodePing(vin=vin, block_hash='ff'*32)

        announce = MasternodeAnnounce(vin=vin, addr=addr, collateral_key=collateral_pub, masternode_pubkey=masternode_pubkey,
                protocol_version=protocol_version, last_ping=last_ping)

        collateral_wif = 'p2pkh:7usrUZignVHMLXbUTBTViYwKFhCu2T37DPsJSX5YPzmbKcmgBJev'
        masternode_wif = '7sqv1jqC6vbysyLZr2CeECoGa2syaf2T5RRTQGWcRAsN3Ez9RR9h'
        announce.last_ping.sign(masternode_wif, 1461858375)
        sig = announce.sign(collateral_wif, 1461858375)

        address = 'GLosAyGUGzvqT4fxpzFCosY8f6ZZdQyXJt'
        self.assertTrue(announce.verify(address))
        self.assertTrue(ecc.verify_message_with_address
                            (address, sig, announce.serialize_for_sig()))

        # DEBUG information. Uncomment to see serialization.
        # from pprint import pprint
        # pprint(announce.dump())
        # print(' - sig follows - ')
        # print(base64.b64encode(sig))
        # print(base64.b64encode(announce.last_ping.sig))

    def test_get_hash(self):
        announce = MasternodeAnnounce.deserialize(raw_announce)
        expected_hash = '411413026c702d2eb16ec4868b3bc192e0bf974d6b25851b1431f51c5fc42d9a'
        self.assertEqual(expected_hash, announce.get_hash())

    def test_verify(self):
        announce = MasternodeAnnounce.deserialize(raw_announce)
        message = announce.serialize_for_sig()

        pk = bitcoin.public_key_to_p2pkh(bfh(announce.collateral_key))
        self.assertTrue(announce.verify())

class TestMasternodePing(unittest.TestCase):
    def test_serialize_for_sig(self):
        vin = {'prevout_hash': '27c7c43cfde0943d2397b9fd5106d0a1f6927074a5fa6dfcf7fe50a2cb6b8d10',
               'prevout_n': 0, 'scriptSig': '', 'sequence': 0xffffffff}
        block_hash = '0000009784f43ea4c4158631a7b638f452e3ed8783eeac00d995e860de12e69f'
        sig_time = 1460397824
        ping = MasternodePing(vin=vin, block_hash=block_hash, sig_time=sig_time)

        expected = b'CTxIn(COutPoint(27c7c43cfde0943d2397b9fd5106d0a1f6927074a5fa6dfcf7fe50a2cb6b8d10, 0), scriptSig=)0000009784f43ea4c4158631a7b638f452e3ed8783eeac00d995e860de12e69f1460397824'
        self.assertEqual(expected, ping.serialize_for_sig())

    def test_sign(self):
        vin = {'prevout_hash': '00'*32, 'prevout_n': 0, 'scriptSig': '', 'sequence':0xffffffff}
        block_hash = 'ff'*32
        current_time = 1461858375
        ping = MasternodePing(vin=vin, block_hash=block_hash, sig_time=current_time)

        expected_sig = 'H6RJ/CNWtTgLEyHO4W+FY0NtKESt0tpg3kwG9aZJatWPVauwhYq7RfW01+4Ny6NlRJpE5i6ywgA9Ry3XC31BAXs='
        wif = '7sqv1jqC6vbysyLZr2CeECoGa2syaf2T5RRTQGWcRAsN3Ez9RR9h'
        sig = ping.sign(wif, current_time = current_time)
        address = bitcoin.address_from_private_key('p2pkh:'+wif)
        self.assertTrue(ecc.verify_message_with_address
                            (address, sig, ping.serialize_for_sig()))
        self.assertEqual(expected_sig, base64.b64encode(sig).decode('utf-8'))

class TestNetworkAddr(unittest.TestCase):
    def test_serialize(self):
        expected = '00000000000000000000ffffc0a801652475'
        addr = NetworkAddress('192.168.1.101:9333')
        self.assertEqual(expected, addr.serialize())
        self.assertEqual('192.168.1.101:9333', str(addr))

class TestParseMasternodeConf(unittest.TestCase):
    def test_parse(self):
        lines = [
            'MN1 127.0.0.2:9333 7sqv1jqC6vbysyLZr2CeECoGa2syaf2T5RRTQGWcRAsN3Ez9RR9h 830c4be5153638a8fbee5782f4d08d81d9fb30e2c7256643fc78765f0bdf44e6 0',
        ]
        conf_lines = parse_masternode_conf(lines)
        expected = [
            MasternodeConfLine('MN1', '127.0.0.2:9333', 'p2pkh:7sqv1jqC6vbysyLZr2CeECoGa2syaf2T5RRTQGWcRAsN3Ez9RR9h', '830c4be5153638a8fbee5782f4d08d81d9fb30e2c7256643fc78765f0bdf44e6', 0),
        ]

        for i, conf in enumerate(conf_lines):
            self.assertEqual(expected[i], conf)

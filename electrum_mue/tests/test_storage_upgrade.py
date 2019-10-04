import shutil
import tempfile

from electrum_mue.storage import WalletStorage
from electrum_mue.wallet import Wallet
from electrum_mue import constants

from .test_wallet import WalletTestCase


# TODO add other wallet types: 2fa, xpub-only
# TODO hw wallet with client version 2.6.x (single-, and multiacc)
class TestStorageUpgrade(WalletTestCase):
    # Reference: this is the latest Electrum (upstream) upgrade

    # def test_upgrade_from_client_2_9_3_multisig(self):
    #     wallet_str = '{"addr_history":{"31uiqKhw4PQSmZWnCkqpeh6moB8B1jXEt3":[],"32PBjkXmwRoEQt8HBZcAEUbNwaHw5dR5fe":[],"33FQMD675LMRLZDLYLK7QV6TMYA1uYW1sw":[],"33MQEs6TCgxmAJhZvUEXYr6gCkEoEYzUfm":[],"33vuhs2Wor9Xkax66ucDkscPcU6nQHw8LA":[],"35tbMt1qBGmy5RNcsdGZJgs7XVbf5gEgPs":[],"36zhHEtGA33NjHJdxCMjY6DLeU2qxhiLUE":[],"37rZuTsieKVpRXshwrY8qvFBn6me42mYr5":[],"38A2KDXYRmRKZRRCGgazrj19i22kDr8d4V":[],"38GZH5GhxLKi5so9Aka6orY2EDZkvaXdxm":[],"3AEtxrCwiYv5Y5CRmHn1c5nZnV3Hpfh5BM":[],"3AaHWprY1MytygvQVDLp6i63e9o5CwMSN5":[],"3DAD19hHXNxAfZjCtUbWjZVxw1fxQqCbY7":[],"3GK4CBbgwumoeR9wxJjr1QnfnYhGUEzHhN":[],"3H18xmkyX3XAb5MwucqKpEhTnh3qz8V4Mn":[],"3JhkakvHAyFvukJ3cyaVgiyaqjYNo2gmsS":[],"3JtA4x1AKW4BR5YAEeLR5D157Nd92NHArC":[],"3KQosfGFGsUniyqsidE2Y4Bz1y4iZUkGW6":[],"3KXe1z2Lfk22zL6ggQJLpHZfc9dKxYV95p":[],"3KZiENj4VHdUycv9UDts4ojVRsaMk8LC5c":[],"3KeTKHJbkZN1QVkvKnHRqYDYP7UXsUu6va":[],"3L5aZKtDKSd65wPLMRooNtWHkKd5Mz6E3i":[],"3LAPqjqW4C2Se9HNziUhNaJQS46X1r9p3M":[],"3P3JJPoyNFussuyxkDbnYevYim5XnPGmwZ":[],"3PgNdMYSaPRymskby885DgKoTeA1uZr6Gi":[],"3Pm7DaUzaDMxy2mW5WzHp1sE9hVWEpdf7J":[]},"addresses":{"change":["31uiqKhw4PQSmZWnCkqpeh6moB8B1jXEt3","3JhkakvHAyFvukJ3cyaVgiyaqjYNo2gmsS","3GK4CBbgwumoeR9wxJjr1QnfnYhGUEzHhN","3LAPqjqW4C2Se9HNziUhNaJQS46X1r9p3M","33MQEs6TCgxmAJhZvUEXYr6gCkEoEYzUfm","3AEtxrCwiYv5Y5CRmHn1c5nZnV3Hpfh5BM"],"receiving":["3P3JJPoyNFussuyxkDbnYevYim5XnPGmwZ","33FQMD675LMRLZDLYLK7QV6TMYA1uYW1sw","3DAD19hHXNxAfZjCtUbWjZVxw1fxQqCbY7","3AaHWprY1MytygvQVDLp6i63e9o5CwMSN5","3H18xmkyX3XAb5MwucqKpEhTnh3qz8V4Mn","36zhHEtGA33NjHJdxCMjY6DLeU2qxhiLUE","37rZuTsieKVpRXshwrY8qvFBn6me42mYr5","38A2KDXYRmRKZRRCGgazrj19i22kDr8d4V","38GZH5GhxLKi5so9Aka6orY2EDZkvaXdxm","33vuhs2Wor9Xkax66ucDkscPcU6nQHw8LA","3L5aZKtDKSd65wPLMRooNtWHkKd5Mz6E3i","3KXe1z2Lfk22zL6ggQJLpHZfc9dKxYV95p","3KQosfGFGsUniyqsidE2Y4Bz1y4iZUkGW6","3KZiENj4VHdUycv9UDts4ojVRsaMk8LC5c","32PBjkXmwRoEQt8HBZcAEUbNwaHw5dR5fe","3KeTKHJbkZN1QVkvKnHRqYDYP7UXsUu6va","3JtA4x1AKW4BR5YAEeLR5D157Nd92NHArC","3PgNdMYSaPRymskby885DgKoTeA1uZr6Gi","3Pm7DaUzaDMxy2mW5WzHp1sE9hVWEpdf7J","35tbMt1qBGmy5RNcsdGZJgs7XVbf5gEgPs"]},"pruned_txo":{},"seed_version":13,"stored_height":485855,"transactions":{},"tx_fees":{},"txi":{},"txo":{},"use_encryption":false,"verified_tx3":{},"wallet_type":"2of2","winpos-qt":[617,227,840,405],"x1/":{"seed":"speed cruise market wasp ability alarm hold essay grass coconut tissue recipe","type":"bip32","xprv":"xprv9s21ZrQH143K48ig2wcAuZoEKaYdNRaShKFR3hLrgwsNW13QYRhXH6gAG1khxim6dw2RtAzF8RWbQxr1vvWUJFfEu2SJZhYbv6pfreMpuLB","xpub":"xpub661MyMwAqRbcGco98y9BGhjxscP7mtJJ4YB1r5kUFHQMNoNZ5y1mptze7J37JypkbrmBdnqTvSNzxL7cE1FrHg16qoj9S12MUpiYxVbTKQV"},"x2/":{"type":"bip32","xprv":null,"xpub":"xpub661MyMwAqRbcGrCDZaVs9VC7Z6579tsGvpqyDYZEHKg2MXoDkxhrWoukqvwDPXKdxVkYA6Hv9XHLETptfZfNpcJZmsUThdXXkTNGoBjQv1o"}}'
    #     self._upgrade_storage(wallet_str)

    def testnet_wallet(func):
        # note: it's ok to modify global network constants in subclasses of SequentialTestCase
        def wrapper(self, *args, **kwargs):
            constants.set_testnet()
            try:
                return func(self, *args, **kwargs)
            finally:
                constants.set_mainnet()
        return wrapper

##########

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from electrum_mue.plugin import Plugins
        from electrum_mue.simple_config import SimpleConfig

        cls.electrum_path = tempfile.mkdtemp()
        config = SimpleConfig({'electrum_path': cls.electrum_path})

        gui_name = 'cmdline'
        # TODO it's probably wasteful to load all plugins... only need Trezor
        Plugins(config, gui_name)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(cls.electrum_path)

    def _upgrade_storage(self, wallet_json, accounts=1):
        storage = self._load_storage_from_json_string(wallet_json, manual_upgrades=True)

        if accounts == 1:
            self.assertFalse(storage.requires_split())
            if storage.requires_upgrade():
                storage.upgrade()
                self._sanity_check_upgraded_storage(storage)
        else:
            self.assertTrue(storage.requires_split())
            new_paths = storage.split_accounts()
            self.assertEqual(accounts, len(new_paths))
            for new_path in new_paths:
                new_storage = WalletStorage(new_path, manual_upgrades=False)
                self._sanity_check_upgraded_storage(new_storage)

    def _sanity_check_upgraded_storage(self, storage):
        self.assertFalse(storage.requires_split())
        self.assertFalse(storage.requires_upgrade())
        w = Wallet(storage)

    def _load_storage_from_json_string(self, wallet_json, manual_upgrades=True):
        with open(self.wallet_path, "w") as f:
            f.write(wallet_json)
        storage = WalletStorage(self.wallet_path, manual_upgrades=manual_upgrades)
        return storage

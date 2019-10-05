import shutil
import tempfile
import os

from electrum_audax import constants, blockchain
from electrum_audax.simple_config import SimpleConfig
from electrum_audax.blockchain import Blockchain, deserialize_header, hash_header
from electrum_audax.util import bh2u, bfh, make_dir

from . import SequentialTestCase


class TestBlockchain(SequentialTestCase):

    HEADERS = {
        'A': deserialize_header(bfh("010000000000000000000000000000000000000000000000000000000000000000000000cff763175904c6cedff80a31fc686ab943fa58223105ebbba6fb22c8cfcacb07dc766a5af0ff0f1ea1594401"), 0),
        'B': deserialize_header(bfh("040000009bbcf21bc2eb1a0c6c2a74f932edd3de0c38d96aa0de3375589c3a7c4608000044367f6ad89040211ffc15073dcd9cfba581c9fc180f70ecf8a57cefee54cf4208796a5affff7f2001000000"), 1),
        'C': deserialize_header(bfh("0400000018e3d8d068a372ba48812c97d502496f272e24a52654946ae7c43a91633f5b40164db6e005b5025a8df7711ec9ae0d044cc733ad1b3731247eb491c166ad6e4e09796a5affff7f2002000000"), 2),
        'D': deserialize_header(bfh("04000000fd45183180347747148c4fa876c51b2efa98b6110d8db6515fa5c90d967b9c48b190bedd75be9c1acf60026644c2aadf39045ae49db03565deee5c15a4c9eebf09796a5affff7f2000000000"), 3),
        'E': deserialize_header(bfh("04000000c80fc3a0ac596c5614a7e943f2266272e7311c0a73d328fd9db7225c139f5d20e0e8a56ef0d4c211d6be6d1837fa1ab0b518df8678a6bee6e91fad9c4901586c0a796a5affff7f2003000000"), 4),
        'F': deserialize_header(bfh("0400000053be2c392ee32fab388c9946c9cbaaeb195e12dfec836dc32654b36ad2d400421dbac7e495b73abe2a3066270d2596ff348e39a31ae45f8ef15984ceecc1d7dc0a796a5affff7f2002000000"), 5),
        'O': deserialize_header(bfh("04000000502bcb6879eced78622cf6dbe6266dc58429b711962ad707ea6c043c8a03bf4702c86ee53b4081974bf3c9f39ba7a9d1be076ad6caf84977e8630727227762060a796a5affff7f2004000000"), 6),
        'P': deserialize_header(bfh("0400000096660650f67a4a233adcce8d5f0ea38eb742e959bb9e6e598b226dbdc4c4fd5c6e3b30e75e64d29085e661bc4d94a4d069fc460b0d81bd666f8d58e2af8278780a796a5affff7f2000000000"), 7),
        'Q': deserialize_header(bfh("04000000d8d30159ec4eb4d7c2d22d882a21ae6f6d28224eb62ca3aa1c53e20a1f95f00fc3e6f858037dfa0a2142d1804f39426855583e9ea54df6ce6c1cb152540504e80b796a5affff7f2006000000"), 8),
        'R': deserialize_header(bfh("040000005066e73503cde9638ec7bf25c031ce0df1a4f4dae542bf91eeaf4f860237ae21b4142f3528ac80bb24c69557d684f60f4c2c080354e14207364604a0e04709110b796a5affff7f2001000000"), 9),
        'S': deserialize_header(bfh("040000000d444d39e3d536b4942a44c034348c06378ebd1001860ddfe52fecd4fee0e54192a9e54fc1be0bd87fd551abe4302ead154db3b5bf7deb36ca1c7c99e33a22da0b796a5affff7f2001000000"), 10),
        'T': deserialize_header(bfh("04000000cf1e59465b8a6d960dd3951b931c0c031fb710624e4f218f4c720b92bb11dc32826882ff63dbbf8743e1163cdd8ecc3c0a1d139025d93cb8fbb417089daa9ce40b796a5affff7f2002000000"), 11),
        'U': deserialize_header(bfh("0400000053e8b4c1d1d5b9619154fe347b82e6debdd9ad2efd881f6628a1eb88514e775aea0c3cd7305c861118813026e5576d04e7dbff39f533a4b423eaca7175f6ebc50b796a5affff7f2000000000"), 12),
        'G': deserialize_header(bfh("04000000502bcb6879eced78622cf6dbe6266dc58429b711962ad707ea6c043c8a03bf4702c86ee53b4081974bf3c9f39ba7a9d1be076ad6caf84977e86307272277620642796a5affff7f2004000000"), 6),
        'H': deserialize_header(bfh("0400000009197f0912b93a9efb4a3ceb1e3f3b8d9b5695d80dc7b1d53da08be914ce619f6e3b30e75e64d29085e661bc4d94a4d069fc460b0d81bd666f8d58e2af82787843796a5affff7f2000000000"), 7),
        'I': deserialize_header(bfh("040000008fe69cb16b9877ef97325f1c6de2c3780a399021ab3dae458f652b1b9778d128c3e6f858037dfa0a2142d1804f39426855583e9ea54df6ce6c1cb152540504e844796a5affff7f2000000000"), 8),
        'J': deserialize_header(bfh("0400000094bce2f4ddc0b15877f03a16ee26c92e270ca6c1b12b28fe881b565bb999cd47b4142f3528ac80bb24c69557d684f60f4c2c080354e14207364604a0e047091145796a5affff7f2000000000"), 9),
        'K': deserialize_header(bfh("0400000000b947b8614df81b174138009ac6eff4fef03653992edf1eb5df1fcae036506c92a9e54fc1be0bd87fd551abe4302ead154db3b5bf7deb36ca1c7c99e33a22da46796a5affff7f2000000000"), 10),
        'L': deserialize_header(bfh("040000006f43e4a881827e98ead07f02ccaaf1986f2a6a68a1908811d3b2dfe8f49cbe75826882ff63dbbf8743e1163cdd8ecc3c0a1d139025d93cb8fbb417089daa9ce40b796a5affff7f2000000000"), 11),
        'M': deserialize_header(bfh("0400000094bce2f4ddc0b15877f03a16ee26c92e270ca6c1b12b28fe881b565bb999cd4792a9e54fc1be0bd87fd551abe4302ead154db3b5bf7deb36ca1c7c99e33a22da0b796a5affff7f2000000000"), 9),
        'N': deserialize_header(bfh("0400000027bbaae65311ed1a136347b6bfe921852fcfc332b20645f6f72e9bf2b164c025826882ff63dbbf8743e1163cdd8ecc3c0a1d139025d93cb8fbb417089daa9ce40b796a5affff7f2000000000"), 10),
        'X': deserialize_header(bfh("0400000007e75248e8511490ddd9bba846d98422d1ff23436c362267d4c35206b5592953ea0c3cd7305c861118813026e5576d04e7dbff39f533a4b423eaca7175f6ebc50b796a5affff7f2000000000"), 11),
        'Y': deserialize_header(bfh("0400000078f4241fac16e77d8257038ee0936f95117e427e4df50dec152c8d3b202cd76f0b0801f50c02fb749180a623b92c3d56ce6bdc855075da43a212052175ed92b70b796a5affff7f2000000000"), 12),
        'Z': deserialize_header(bfh("040000008f45be059c22c7212b67fb5b4a24831dfd19c9116758a7bdf276b4fc000a23055dd8288eafd27f983e5fd54a9efa2022f80883171e08b45d870eabe402449df00b796a5affff7f2002000000"), 13),
    }
    # tree of headers:
    #                                            - M <- N <- X <- Y <- Z
    #                                          /
    #                             - G <- H <- I <- J <- K <- L
    #                           /
    # A <- B <- C <- D <- E <- F <- O <- P <- Q <- R <- S <- T <- U

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        constants.set_regtest()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        constants.set_mainnet()

    def setUp(self):
        super().setUp()
        self.data_dir = tempfile.mkdtemp()
        make_dir(os.path.join(self.data_dir, 'forks'))
        self.config = SimpleConfig({'electrum_path': self.data_dir})
        blockchain.blockchains = {}

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.data_dir)

    def _append_header(self, chain: Blockchain, header: dict):
        self.assertTrue(chain.can_connect(header))
        chain.save_header(header)

    def test_get_height_of_last_common_block_with_chain(self):
        blockchain.blockchains[constants.net.GENESIS] = chain_u = Blockchain(
            config=self.config, forkpoint=0, parent=None,
            forkpoint_hash=constants.net.GENESIS, prev_hash=None)
        open(chain_u.path(), 'w+').close()
        self._append_header(chain_u, self.HEADERS['A'])
        self._append_header(chain_u, self.HEADERS['B'])
        self._append_header(chain_u, self.HEADERS['C'])
        self._append_header(chain_u, self.HEADERS['D'])
        self._append_header(chain_u, self.HEADERS['E'])
        self._append_header(chain_u, self.HEADERS['F'])
        self._append_header(chain_u, self.HEADERS['O'])
        self._append_header(chain_u, self.HEADERS['P'])
        self._append_header(chain_u, self.HEADERS['Q'])

        chain_l = chain_u.fork(self.HEADERS['G'])
        self._append_header(chain_l, self.HEADERS['H'])
        self._append_header(chain_l, self.HEADERS['I'])
        self._append_header(chain_l, self.HEADERS['J'])
        self._append_header(chain_l, self.HEADERS['K'])
        self._append_header(chain_l, self.HEADERS['L'])

        self.assertEqual({chain_u:  8, chain_l: 5}, chain_u.get_parent_heights())
        self.assertEqual({chain_l: 11},             chain_l.get_parent_heights())

        chain_z = chain_l.fork(self.HEADERS['M'])
        self._append_header(chain_z, self.HEADERS['N'])
        self._append_header(chain_z, self.HEADERS['X'])
        self._append_header(chain_z, self.HEADERS['Y'])
        self._append_header(chain_z, self.HEADERS['Z'])

        self.assertEqual({chain_u:  8, chain_z: 5}, chain_u.get_parent_heights())
        self.assertEqual({chain_l: 11, chain_z: 8}, chain_l.get_parent_heights())
        self.assertEqual({chain_z: 13},             chain_z.get_parent_heights())
        self.assertEqual(5, chain_u.get_height_of_last_common_block_with_chain(chain_l))
        self.assertEqual(5, chain_l.get_height_of_last_common_block_with_chain(chain_u))
        self.assertEqual(5, chain_u.get_height_of_last_common_block_with_chain(chain_z))
        self.assertEqual(5, chain_z.get_height_of_last_common_block_with_chain(chain_u))
        self.assertEqual(8, chain_l.get_height_of_last_common_block_with_chain(chain_z))
        self.assertEqual(8, chain_z.get_height_of_last_common_block_with_chain(chain_l))

        self._append_header(chain_u, self.HEADERS['R'])
        self._append_header(chain_u, self.HEADERS['S'])
        self._append_header(chain_u, self.HEADERS['T'])
        self._append_header(chain_u, self.HEADERS['U'])

        self.assertEqual({chain_u: 12, chain_z: 5}, chain_u.get_parent_heights())
        self.assertEqual({chain_l: 11, chain_z: 8}, chain_l.get_parent_heights())
        self.assertEqual({chain_z: 13},             chain_z.get_parent_heights())
        self.assertEqual(5, chain_u.get_height_of_last_common_block_with_chain(chain_l))
        self.assertEqual(5, chain_l.get_height_of_last_common_block_with_chain(chain_u))
        self.assertEqual(5, chain_u.get_height_of_last_common_block_with_chain(chain_z))
        self.assertEqual(5, chain_z.get_height_of_last_common_block_with_chain(chain_u))
        self.assertEqual(8, chain_l.get_height_of_last_common_block_with_chain(chain_z))
        self.assertEqual(8, chain_z.get_height_of_last_common_block_with_chain(chain_l))

    def test_parents_after_forking(self):
        blockchain.blockchains[constants.net.GENESIS] = chain_u = Blockchain(
            config=self.config, forkpoint=0, parent=None,
            forkpoint_hash=constants.net.GENESIS, prev_hash=None)
        open(chain_u.path(), 'w+').close()
        self._append_header(chain_u, self.HEADERS['A'])
        self._append_header(chain_u, self.HEADERS['B'])
        self._append_header(chain_u, self.HEADERS['C'])
        self._append_header(chain_u, self.HEADERS['D'])
        self._append_header(chain_u, self.HEADERS['E'])
        self._append_header(chain_u, self.HEADERS['F'])
        self._append_header(chain_u, self.HEADERS['O'])
        self._append_header(chain_u, self.HEADERS['P'])
        self._append_header(chain_u, self.HEADERS['Q'])

        self.assertEqual(None, chain_u.parent)

        chain_l = chain_u.fork(self.HEADERS['G'])
        self._append_header(chain_l, self.HEADERS['H'])
        self._append_header(chain_l, self.HEADERS['I'])
        self._append_header(chain_l, self.HEADERS['J'])
        self._append_header(chain_l, self.HEADERS['K'])
        self._append_header(chain_l, self.HEADERS['L'])

        self.assertEqual(None,    chain_l.parent)
        self.assertEqual(chain_l, chain_u.parent)

        chain_z = chain_l.fork(self.HEADERS['M'])
        self._append_header(chain_z, self.HEADERS['N'])
        self._append_header(chain_z, self.HEADERS['X'])
        self._append_header(chain_z, self.HEADERS['Y'])
        self._append_header(chain_z, self.HEADERS['Z'])

        self.assertEqual(chain_z, chain_u.parent)
        self.assertEqual(chain_z, chain_l.parent)
        self.assertEqual(None,    chain_z.parent)

        self._append_header(chain_u, self.HEADERS['R'])
        self._append_header(chain_u, self.HEADERS['S'])
        self._append_header(chain_u, self.HEADERS['T'])
        self._append_header(chain_u, self.HEADERS['U'])

        self.assertEqual(chain_z, chain_u.parent)
        self.assertEqual(chain_z, chain_l.parent)
        self.assertEqual(None,    chain_z.parent)

    def test_forking_and_swapping(self):
        blockchain.blockchains[constants.net.GENESIS] = chain_u = Blockchain(
            config=self.config, forkpoint=0, parent=None,
            forkpoint_hash=constants.net.GENESIS, prev_hash=None)
        open(chain_u.path(), 'w+').close()

        self._append_header(chain_u, self.HEADERS['A'])
        self._append_header(chain_u, self.HEADERS['B'])
        self._append_header(chain_u, self.HEADERS['C'])
        self._append_header(chain_u, self.HEADERS['D'])
        self._append_header(chain_u, self.HEADERS['E'])
        self._append_header(chain_u, self.HEADERS['F'])
        self._append_header(chain_u, self.HEADERS['O'])
        self._append_header(chain_u, self.HEADERS['P'])
        self._append_header(chain_u, self.HEADERS['Q'])
        self._append_header(chain_u, self.HEADERS['R'])

        chain_l = chain_u.fork(self.HEADERS['G'])
        self._append_header(chain_l, self.HEADERS['H'])
        self._append_header(chain_l, self.HEADERS['I'])
        self._append_header(chain_l, self.HEADERS['J'])

        # do checks
        self.assertEqual(2, len(blockchain.blockchains))
        self.assertEqual(1, len(os.listdir(os.path.join(self.data_dir, "forks"))))
        self.assertEqual(0, chain_u.forkpoint)
        self.assertEqual(None, chain_u.parent)
        self.assertEqual(constants.net.GENESIS, chain_u._forkpoint_hash)
        self.assertEqual(None, chain_u._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "blockchain_headers"), chain_u.path())
        self.assertEqual(10 * 80, os.stat(chain_u.path()).st_size)
        self.assertEqual(6, chain_l.forkpoint)
        self.assertEqual(chain_u, chain_l.parent)
        self.assertEqual(hash_header(self.HEADERS['G']), chain_l._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['F']), chain_l._prev_hash)

        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_6_47bf038a3c046cea07d72a9611b72984c56d26e6dbf62c6278edec7968cb2b50_9f61ce14e98ba03dd5b1c70dd895569b8d3b3f1eeb3c4afb9e3ab912097f1909"), chain_l.path())
        self.assertEqual(4 * 80, os.stat(chain_l.path()).st_size)

        self._append_header(chain_l, self.HEADERS['K'])

        # chains were swapped, do checks
        self.assertEqual(2, len(blockchain.blockchains))
        self.assertEqual(1, len(os.listdir(os.path.join(self.data_dir, "forks"))))
        self.assertEqual(6, chain_u.forkpoint)
        self.assertEqual(chain_l, chain_u.parent)
        self.assertEqual(hash_header(self.HEADERS['O']), chain_u._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['F']), chain_u._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_6_47bf038a3c046cea07d72a9611b72984c56d26e6dbf62c6278edec7968cb2b50_5cfdc4c4bd6d228b596e9ebb59e942b78ea30e5f8dcedc3a234a7af650066696"), chain_u.path())
        self.assertEqual(4 * 80, os.stat(chain_u.path()).st_size)
        self.assertEqual(0, chain_l.forkpoint)
        self.assertEqual(None, chain_l.parent)
        self.assertEqual(constants.net.GENESIS, chain_l._forkpoint_hash)
        self.assertEqual(None, chain_l._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "blockchain_headers"), chain_l.path())
        self.assertEqual(11 * 80, os.stat(chain_l.path()).st_size)
        for b in (chain_u, chain_l):
            self.assertTrue(all([b.can_connect(b.read_header(i), False) for i in range(b.height())]))

        self._append_header(chain_u, self.HEADERS['S'])
        self._append_header(chain_u, self.HEADERS['T'])
        self._append_header(chain_u, self.HEADERS['U'])
        self._append_header(chain_l, self.HEADERS['L'])

        chain_z = chain_l.fork(self.HEADERS['M'])
        self._append_header(chain_z, self.HEADERS['N'])
        self._append_header(chain_z, self.HEADERS['X'])
        self._append_header(chain_z, self.HEADERS['Y'])
        self._append_header(chain_z, self.HEADERS['Z'])

        # chain_z became best chain, do checks
        self.assertEqual(3, len(blockchain.blockchains))
        self.assertEqual(2, len(os.listdir(os.path.join(self.data_dir, "forks"))))
        self.assertEqual(0, chain_z.forkpoint)
        self.assertEqual(None, chain_z.parent)
        self.assertEqual(constants.net.GENESIS, chain_z._forkpoint_hash)
        self.assertEqual(None, chain_z._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "blockchain_headers"), chain_z.path())
        self.assertEqual(14 * 80, os.stat(chain_z.path()).st_size)
        self.assertEqual(9, chain_l.forkpoint)
        self.assertEqual(chain_z, chain_l.parent)
        self.assertEqual(hash_header(self.HEADERS['J']), chain_l._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['I']), chain_l._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_9_47cd99b95b561b88fe282bb1c1a60c272ec926ee163af07758b1c0ddf4e2bc94_6c5036e0ca1fdfb51edf2e995336f0fef4efc69a003841171bf84d61b847b900"), chain_l.path())
        self.assertEqual(3 * 80, os.stat(chain_l.path()).st_size)
        self.assertEqual(6, chain_u.forkpoint)
        self.assertEqual(chain_z, chain_u.parent)
        self.assertEqual(hash_header(self.HEADERS['O']), chain_u._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['F']), chain_u._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_6_47bf038a3c046cea07d72a9611b72984c56d26e6dbf62c6278edec7968cb2b50_5cfdc4c4bd6d228b596e9ebb59e942b78ea30e5f8dcedc3a234a7af650066696"), chain_u.path())
        self.assertEqual(7 * 80, os.stat(chain_u.path()).st_size)
        for b in (chain_u, chain_l, chain_z):
            self.assertTrue(all([b.can_connect(b.read_header(i), False) for i in range(b.height())]))

        self.assertEqual(constants.net.GENESIS, chain_z.get_hash(0))
        self.assertEqual(hash_header(self.HEADERS['F']), chain_z.get_hash(5))
        self.assertEqual(hash_header(self.HEADERS['G']), chain_z.get_hash(6))
        self.assertEqual(hash_header(self.HEADERS['I']), chain_z.get_hash(8))
        self.assertEqual(hash_header(self.HEADERS['M']), chain_z.get_hash(9))
        self.assertEqual(hash_header(self.HEADERS['Z']), chain_z.get_hash(13))

    def test_doing_multiple_swaps_after_single_new_header(self):
        blockchain.blockchains[constants.net.GENESIS] = chain_u = Blockchain(
            config=self.config, forkpoint=0, parent=None,
            forkpoint_hash=constants.net.GENESIS, prev_hash=None)
        open(chain_u.path(), 'w+').close()

        self._append_header(chain_u, self.HEADERS['A'])
        self._append_header(chain_u, self.HEADERS['B'])
        self._append_header(chain_u, self.HEADERS['C'])
        self._append_header(chain_u, self.HEADERS['D'])
        self._append_header(chain_u, self.HEADERS['E'])
        self._append_header(chain_u, self.HEADERS['F'])
        self._append_header(chain_u, self.HEADERS['O'])
        self._append_header(chain_u, self.HEADERS['P'])
        self._append_header(chain_u, self.HEADERS['Q'])
        self._append_header(chain_u, self.HEADERS['R'])
        self._append_header(chain_u, self.HEADERS['S'])

        self.assertEqual(1, len(blockchain.blockchains))
        self.assertEqual(0, len(os.listdir(os.path.join(self.data_dir, "forks"))))

        chain_l = chain_u.fork(self.HEADERS['G'])
        self._append_header(chain_l, self.HEADERS['H'])
        self._append_header(chain_l, self.HEADERS['I'])
        self._append_header(chain_l, self.HEADERS['J'])
        self._append_header(chain_l, self.HEADERS['K'])
        # now chain_u is best chain, but it's tied with chain_l

        self.assertEqual(2, len(blockchain.blockchains))
        self.assertEqual(1, len(os.listdir(os.path.join(self.data_dir, "forks"))))

        chain_z = chain_l.fork(self.HEADERS['M'])
        self._append_header(chain_z, self.HEADERS['N'])
        self._append_header(chain_z, self.HEADERS['X'])

        self.assertEqual(3, len(blockchain.blockchains))
        self.assertEqual(2, len(os.listdir(os.path.join(self.data_dir, "forks"))))

        # chain_z became best chain, do checks
        self.assertEqual(0, chain_z.forkpoint)
        self.assertEqual(None, chain_z.parent)
        self.assertEqual(constants.net.GENESIS, chain_z._forkpoint_hash)
        self.assertEqual(None, chain_z._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "blockchain_headers"), chain_z.path())
        self.assertEqual(12 * 80, os.stat(chain_z.path()).st_size)
        self.assertEqual(9, chain_l.forkpoint)
        self.assertEqual(chain_z, chain_l.parent)
        self.assertEqual(hash_header(self.HEADERS['J']), chain_l._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['I']), chain_l._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_9_47cd99b95b561b88fe282bb1c1a60c272ec926ee163af07758b1c0ddf4e2bc94_6c5036e0ca1fdfb51edf2e995336f0fef4efc69a003841171bf84d61b847b900"), chain_l.path())
        self.assertEqual(2 * 80, os.stat(chain_l.path()).st_size)
        self.assertEqual(6, chain_u.forkpoint)
        self.assertEqual(chain_z, chain_u.parent)
        self.assertEqual(hash_header(self.HEADERS['O']), chain_u._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['F']), chain_u._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_6_47bf038a3c046cea07d72a9611b72984c56d26e6dbf62c6278edec7968cb2b50_5cfdc4c4bd6d228b596e9ebb59e942b78ea30e5f8dcedc3a234a7af650066696"), chain_u.path())
        self.assertEqual(5 * 80, os.stat(chain_u.path()).st_size)

        self.assertEqual(constants.net.GENESIS, chain_z.get_hash(0))
        self.assertEqual(hash_header(self.HEADERS['F']), chain_z.get_hash(5))
        self.assertEqual(hash_header(self.HEADERS['G']), chain_z.get_hash(6))
        self.assertEqual(hash_header(self.HEADERS['I']), chain_z.get_hash(8))
        self.assertEqual(hash_header(self.HEADERS['M']), chain_z.get_hash(9))
        self.assertEqual(hash_header(self.HEADERS['X']), chain_z.get_hash(11))

        for b in (chain_u, chain_l, chain_z):
            self.assertTrue(all([b.can_connect(b.read_header(i), False) for i in range(b.height())]))

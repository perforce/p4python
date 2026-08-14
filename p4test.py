# -*- encoding: UTF8 -*-

from __future__ import print_function

import glob, sys, time, stat, platform, os
import contextlib, io
pattern = 'build/lib*'
architecture = platform.architecture()
if 'Windows' in architecture[1]:
    if architecture[0] == '32bit':
        pattern += 'win32*'
    else:
        pattern += 'win-amd64*'

pathToBuild = glob.glob(pattern)
if len(pathToBuild) > 0:
    versionString = "%d.%d" % (sys.version_info[0], sys.version_info[1])
    for i in pathToBuild:
        if versionString in i:
            sys.path.insert(0, os.path.realpath(i))

import P4
from P4 import P4Exception
import P4API
import unittest, os, types, shutil, stat
from subprocess import Popen, PIPE
import sys
import os.path
import re
import platform
import pickle

def onRmTreeError( function, path, exc_info ):
    os.chmod( path, stat.S_IWRITE)
    os.remove( path )

SUPER_PASSWORD = "P4Python!Super1"

class TestP4Python(unittest.TestCase):

    def setUp(self):
        self.setDirectories()
        self.p4d = "p4d"
        self.port = "rsh:%s -r \"%s\" -L log -vserver=3 -i" % ( self.p4d, self.server_root )
        self.p4 = P4.P4()
        self.p4.port = self.port
        self._bootstrapSuperUser()

    def _bootstrapSuperUser(self):
        """On P4 Server 2026.1+, password authentication is enforced from the very
        first connection (binary-level default).  The one unauthenticated operation
        allowed on a fresh server is run_password('', pw) to set the initial password
        for the connecting user.  Immediately log in afterwards so a ticket is stored
        in the ticket file for all subsequent test connections to use.
        """
        import getpass
        super_user = getpass.getuser()

        p4 = P4.P4()
        p4.port = self.port
        p4.user = super_user
        p4.exception_level = P4.P4.RAISE_ERRORS
        p4.connect()
        # On some older server versions the user record must exist before a
        # password can be set.  Attempt to create it now and ignore any errors
        # (e.g. on 2026.1 the server rejects all commands until a password is
        # set, so this will simply fail silently there).
        try:
            user_spec = p4.fetch_user(super_user)
            p4.save_user(user_spec, '-f')
        except P4.P4Exception:
            pass

        p4.run_password('', SUPER_PASSWORD)
        p4.password = SUPER_PASSWORD
        p4.run_login()
        p4.disconnect()

        self.p4.user = super_user
        self.p4.password = SUPER_PASSWORD

    def enableUnicode(self):
        cmd = [self.p4d, "-r", self.server_root, "-L", "log", "-vserver=3", "-xi"]
        p = Popen(cmd, stdout=PIPE)
        f = p.stdout
        for s in f.readlines():
            pass
        p.wait()
        f.close()

    def tearDown(self):
        if self.p4.connected():
            self.p4.disconnect()
        time.sleep( 1 )
        self.cleanupTestTree()

    def setDirectories(self):
        self.startdir = os.getcwd()
        self.server_root = os.path.join(self.startdir, 'testroot')
        self.client_root = os.path.join(self.server_root, 'client')

        self.cleanupTestTree()
        self.ensureDirectory(self.server_root)
        self.ensureDirectory(self.client_root)

    def cleanupTestTree(self):
        os.chdir(self.startdir)
        if os.path.isdir(self.server_root):
            if sys.version_info.minor < 12:
                shutil.rmtree(self.server_root, False, onRmTreeError)
            else:
                shutil.rmtree(self.server_root, False, onexc=onRmTreeError)

    def ensureDirectory(self, directory):
        if not os.path.isdir(directory):
            os.mkdir(directory)

    def getServerPatchLevel(self, info):
        c = re.compile(r"[^/]*/[^/]*/[^/]*/([^/]*)\s\(\d+/\d+/\d+\)")

        serverVersion = info[0]["serverVersion"]
        m = c.match(serverVersion)
        if m:
            serverPatch = m.group(1)
            return int(serverPatch)
        else:
            print("Cannot extract patch level from {0}".format(serverVersion))
            sys.exit(1)

class TestP4(TestP4Python):

    def testInfo(self):
        self.assertTrue(self.p4 != None, "Could not create p4")
        self.p4.connect()
        self.assertTrue(self.p4.connected(), "Not connected")

        info = self.p4.run_info()
        self.assertTrue(isinstance(info, list), "run_info() does not return a list")
        info = info.pop()
        self.assertTrue(isinstance(info, dict), "run_info().pop() is not a dict")
        self.assertEqual(info['serverRoot'], self.server_root, "Server root incorrect")

    def testEnvironment(self):
        self.assertTrue(self.p4 != None, "Could not create p4")

        self.p4.charset         = "iso8859-1"
        self.p4.client          = "myclient"
        self.p4.host            = "myhost"
        self.p4.language        = "german"
        self.p4.maxresults      = 100000
        self.p4.maxscanrows     = 1000000
        self.p4.maxlocktime     = 10000
        self.p4.maxopenfiles    = 1000
        self.p4.maxmemory       = 2000
        self.p4.password        = "mypassword"
        self.p4.port            = "myserver:1666"
        self.p4.prog            = "myprogram"
        self.p4.tagged          = True
        self.p4.ticket_file     = "myticket"
        self.p4.user            = "myuser"

        self.assertEqual( self.p4.charset, "iso8859-1", "charset" )
        self.assertEqual( self.p4.client, "myclient", "client" )
        self.assertEqual( self.p4.host, "myhost", "host" )
        self.assertEqual( self.p4.language, "german", "language" )
        self.assertEqual( self.p4.maxresults, 100000, "maxresults" )
        self.assertEqual( self.p4.maxscanrows, 1000000, "maxscanrows" )
        self.assertEqual( self.p4.maxlocktime, 10000, "maxlocktime" )
        self.assertEqual( self.p4.maxopenfiles, 1000, "maxopenfiles" )
        self.assertEqual( self.p4.maxmemory, 2000, "maxmemory" )
        self.assertEqual( self.p4.password, "mypassword", "password" )
        self.assertEqual( self.p4.port, "myserver:1666", "port" )
        self.assertEqual( self.p4.tagged, 1, "tagged" )
        self.assertEqual( self.p4.ticket_file, "myticket", "ticket_file" )
        self.assertEqual( self.p4.user, "myuser", "user" )

    def testClient(self):
        self.p4.connect()
        self.assertTrue(self.p4.connected(), "Not connected")

        client = self.p4.fetch_client()
        self.assertTrue( isinstance(client, P4.Spec), "Client is not of type P4.Spec")

        client._root = self.client_root
        client._description = 'Some Test Client\n'

        try:
            self.p4.save_client(client)
        except P4.P4Exception:
            self.fail("Saving client caused exception")

        client2 = self.p4.fetch_client()

        self.assertEqual( client._root, client2._root, "Client root differs")
        self.assertEqual( client._description, client2._description, "Client description differs")

        try:
            client3 = self.p4.fetch_client('newtest')
            client3._view = [ '//depot/... //newtest/...']
            self.p4.save_client(client3)
        except P4.P4Exception:
                self.fail("Saving client caused exception")

    def createFiles(self, testDir):
        testAbsoluteDir = os.path.join(self.client_root, testDir)
        os.mkdir(testAbsoluteDir)

        # create a bunch of files
        files = ('foo.txt', 'bar.txt', 'baz.txt')
        for file in files:
            fname = os.path.join(testAbsoluteDir, file)
            f = open(fname, "w")
            f.write("Test Text")
            f.close()
            self.p4.run_add(testDir + "/" + file)

        self.assertEqual(len(self.p4.run_opened()), len(files), "Unexpected number of open files")
        return files

    def testFiles(self):
        self.p4.connect()
        self.assertTrue(self.p4.connected(), "Not connected")
        self._setClient()
        self.assertEqual(len(self.p4.run_opened()), 0, "Shouldn't have open files")

        testDir = 'test_files'
        files = self.createFiles(testDir)

        change = self.p4.fetch_change()
        self.assertTrue( isinstance(change, P4.Spec), "Change spec is not of type P4.Spec")
        change._description = "My Add Test"

        self._doSubmit("Failed to submit the add", change)

        # make sure there are no open files and all files are there

        self.assertEqual( len(self.p4.run_opened()), 0, "Still files in the open list")
        self.assertEqual( len(self.p4.run_files('...')), len(files), "Less files than expected")

        # edit the files

        self.assertEqual( len(self.p4.run_edit('...')), len(files), "Not all files open for edit")
        self.assertEqual( len(self.p4.run_opened()), len(files), "Not enough files open for edit")

        change = self.p4.fetch_change()
        change._description = "My Edit Test"
        self._doSubmit("Failed to submit the edit", change)
        self.assertEqual( len(self.p4.run_opened()), 0, "Still files in the open list")

        # branch testing

        branchDir = 'test_branch'
        try:
            result = self.p4.run_integ(testDir + '/...', branchDir + '/...')
            self.assertEqual(len(result), len(files), "Not all files branched")
        except P4.P4Exception:
            self.fail("Integration failed")

        change = self.p4.fetch_change()
        change._description = "My Branch Test"
        self._doSubmit("Failed to submit branch", change)

        # branch testing again

        branchDir = 'test_branch2'
        try:
            result = self.p4.run_integ(testDir + '/...', branchDir + '/...')
            self.assertEqual(len(result), len(files), "Not all files branched")
        except P4.P4Exception:
            self.fail("Integration failed")

        change = self.p4.fetch_change()
        change._description = "My Branch Test"
        self._doSubmit("Failed to submit branch", change)

        # filelog checks

        filelogs = self.p4.run_filelog( testDir + '/...' )
        self.assertEqual( len(filelogs), len(files) )

        df = filelogs[0]
        self.assertEqual( df.depotFile, "//depot/test_files/bar.txt", "Unexpected file in the filelog" )
        self.assertEqual( len(df.revisions), 2, "Unexpected number of revisions" )

        rev = df.revisions[0]
        self.assertEqual( rev.rev, 2, "Unexpected revision")
        self.assertEqual( len(rev.integrations), 2, "Unexpected number of integrations")
        self.assertEqual( rev.integrations[ 0 ].how, "branch into", "Unexpected how" )
        self.assertEqual( rev.integrations[ 0 ].file, "//depot/test_branch/bar.txt", "Unexpected target file" )

    def testShelves(self):
        self.p4.connect()
        self.assertTrue(self.p4.connected(), "Not connected")
        self._setClient()
        self.assertEqual(len(self.p4.run_opened()), 0, "Shouldn't have open files")

        if self.p4.server_level >= 28:
            testDir = 'test_shelves'
            files = self.createFiles(testDir)

            change = self.p4.fetch_change()
            self.assertTrue( isinstance(change, P4.Spec), "Change spec is not of type P4.Spec")
            change._description = "My Shelve Test"

            s = self.p4.save_shelve(change)
            c = s[0]['change']

            self.p4.run_revert('...');
            self.assertEqual(len(self.p4.run_opened()), 0, "Some files still opened")

            self.p4.run_unshelve('-s', c, '-f')
            self.assertEqual(len(self.p4.run_opened()), len(files), "Files not unshelved")

            self.p4.run_shelve('-d', '-c', c)
            self._doSubmit("Failed to submit after deleting shelve", change)
        else:
            print( "Need Perforce Server 2009.2 or greater to test shelving")

    def testPasswords(self):
        ticketFile = self.client_root + "/.p4tickets"
        password = "P4Test!Pwd99"
        self.p4.ticket_file = ticketFile
        self.assertEqual( self.p4.ticket_file, ticketFile, "Ticket file not set correctly")

        self.p4.connect()
        # Ticket file was swapped to an empty file above; must login explicitly
        # before any authenticated command can succeed.
        self.p4.run_login()
        client = self.p4.fetch_client()
        client._root = self.client_root
        self.p4.save_client(client)

        try:
            self.p4.run_password( SUPER_PASSWORD, password )
        except P4.P4Exception:
            self.fail( "Failed to change the password" )

        self.p4.password = password
        self.assertEqual( self.p4.password, password, "Could not set password" )
        try:
            self.p4.run_login( )
        except P4.P4Exception:
            self.fail( "Failed to log on")
        self.p4.run_login(password=password)

        try:
            self.p4.run_password( "", password)
            self.fail( "Failed to spot illegal password setting" )
        except P4.P4Exception as e:
            # With dm.user.hideinvalid=1 the exact message may be suppressed;
            # just verify that an exception is raised.
            pass

        try:
            self.p4.run_password( password, SUPER_PASSWORD )
        except P4.P4Exception:
            self.fail( "Failed to reset the password" )

        self.assertTrue( os.path.exists(ticketFile), "Ticket file not found")

        tickets = self.p4.run_tickets()
        self.assertEqual(len(tickets), 1, "Expected only one ticket")
        self.assertEqual(len(tickets[0]), 3, "Expected exactly three entries in tickets")

    def testMultiUserExecution(self):
        """Tests that p4.user and p4.password can be set to switch to a different Perforce user,
        and that after calling p4.run_login(), the server recognizes and executes commands
        in the context of the switched user.
        """
        self.p4.connect()
        self._setClient()

        original_user = self.p4.run_info()[0]['userName']
        original_client = self.p4.client

        bot_name = 'testbot'
        bot_password = 'TestBot123!'
        bot_email = 'testbot@example.com'
        bot_fullname = 'Test Bot User'

        try:
            user_spec = self.p4.run_user(['-o', bot_name])[0]
            user_spec['Email'] = bot_email
            user_spec['FullName'] = bot_fullname

            self.p4.save_user(user_spec, '-f')

            # Set password for testbot as super user.
            # p4.password is replaced with the ticket after the first authenticated command;
            # set input directly and call run_passwd as super without run_login.
            self.p4.input = [bot_password, bot_password]
            self.p4.run_passwd([bot_name])

            # Re-save the user spec with -f as super to clear the forced-reset flag
            # set by dm.user.resetpassword=1 so that run_login works for the new user.
            self.p4.save_user(user_spec, '-f')

            # Switch credentials to testbot and authenticate
            self.p4.user = bot_name
            self.p4.password = bot_password
            # Use the password= kwarg so run_login uses the literal value rather than
            # any cached ticket that may have been stored for the previous user.
            self.p4.run_login(password=bot_password)

            # Verify server recognizes the switched user
            info = self.p4.run_info()[0]
            self.assertEqual(info['userName'], bot_name,
                           f"Expected userName='{bot_name}', got '{info['userName']}'")

            # Verify commands execute under the new user context
            clients_result = self.p4.run('clients', '-u', bot_name)
            self.assertIsInstance(clients_result, list,
                                 "p4.run('clients', '-u', bot_name) did not return a list")

            # Create a client for testbot to verify full command execution
            testbot_client = f"{bot_name}_client"
            self.p4.client = testbot_client
            client_spec = self.p4.fetch_client()
            client_spec['Root'] = self.client_root
            client_spec['Owner'] = bot_name
            self.p4.save_client(client_spec)

            created_client = self.p4.fetch_client(testbot_client)
            self.assertEqual(created_client['Owner'], bot_name,
                           f"Client owner should be '{bot_name}', got '{created_client['Owner']}'")

        finally:
            self.p4.user = original_user
            self.p4.password = ''
            self.p4.client = original_client
            try:
                self.p4.run_client(['-d', f"{bot_name}_client"])
            except P4.P4Exception:
                pass
            try:
                self.p4.run_user(['-d', '-f', bot_name])
            except P4.P4Exception:
                pass

    def testGlobalOptionsCredentialSwitch(self):
        """Tests that user, password, and client attributes handle None and empty-string
        values correctly, falling back to environment defaults, and that they are
        independent of other connection attributes.
        """
        self.p4.connect()
        self._setClient()

        original_user = self.p4.run_info()[0]['userName']
        original_client = self.p4.client

        # Verify attribute read-back without a server round-trip
        test_user = "testuser"
        self.p4.user = test_user
        self.assertEqual(self.p4.user, test_user, "Could not read back user value")

        test_password = "testpassword"
        self.p4.password = test_password
        self.assertEqual(self.p4.password, test_password, "Could not read back password value")

        self.p4.client = "testclient_readback"
        self.assertEqual(self.p4.client, "testclient_readback", "Could not read back client value")
        self.p4.client = original_client

        # Setting user to None should fall back to the environment/original user
        self.p4.user = None
        info_after_reset = self.p4.run_info()[0]
        self.assertEqual(info_after_reset['userName'], original_user,
                        "Did not fall back to original user after setting user=None")

        # Setting password to None should still allow commands to succeed
        self.p4.password = None
        info_pwd_reset = self.p4.run_info()[0]
        self.assertEqual(info_pwd_reset['userName'], original_user,
                        "Failed to execute after setting password=None")

        # Empty string should also fall back to the original user
        self.p4.user = ""
        info_empty_user = self.p4.run_info()[0]
        self.assertEqual(info_empty_user['userName'], original_user,
                        "Did not fall back to original user after setting user=''")

        self.p4.password = ""
        info_empty_pwd = self.p4.run_info()[0]
        self.assertEqual(info_empty_pwd['userName'], original_user,
                        "Failed to execute after setting password=''")

        # A wrong password must raise P4Exception
        try:
            self.p4.password = SUPER_PASSWORD
            self.p4.run_login()
            self.p4.run_password(SUPER_PASSWORD, "P4Valid!Pw99")

            # Set wrong password and verify it raises exception
            self.p4.password = "WrongPassword!"
            self.assertRaises(P4.P4Exception, self.p4.run_login)
        finally:
            # Restore: login with correct password, clear server password, reset attribute
            self.p4.password = "P4Valid!Pw99"
            try:
                self.p4.run_login()
            except P4.P4Exception:
                pass  # May fail if already logged in, that's okay
            self.p4.run_password("P4Valid!Pw99", SUPER_PASSWORD)
            self.p4.password = SUPER_PASSWORD

        # Verify that user and password are independent of other connection attributes
        self.p4.user = original_user
        self.p4.password = ""

        original_port = self.p4.port
        test_host = "testhost"
        test_prog = "testprog"
        test_version = "testversion"

        self.p4.host = test_host
        self.assertEqual(self.p4.host, test_host, "Could not set host")

        self.p4.prog = test_prog
        self.assertEqual(self.p4.prog, test_prog, "Could not set prog")

        self.p4.version = test_version
        self.assertEqual(self.p4.version, test_version, "Could not set version")

        self.p4.user = test_user
        self.p4.password = test_password
        self.assertEqual(self.p4.host, test_host, "Setting user affected host")
        self.assertEqual(self.p4.prog, test_prog, "Setting user affected prog")
        self.assertEqual(self.p4.version, test_version, "Setting user affected version")
        self.assertEqual(self.p4.port, original_port, "Setting user affected port")

        # Setting charset must not disturb user or port
        pre_charset_user = self.p4.user
        pre_charset_port = self.p4.port
        try:
            self.p4.charset = "utf8"
        except P4.P4Exception:
            # Non-unicode server, that's okay
            pass
        self.assertEqual(self.p4.user, pre_charset_user, "Setting charset affected user")
        self.assertEqual(self.p4.port, pre_charset_port, "Setting charset affected port")

        # Setting client to None or empty string must clear the override
        self.p4.client = "temp_client_override"
        self.p4.client = None
        self.assertNotEqual(self.p4.client, "temp_client_override",
                           "Setting client=None did not clear override")

        self.p4.client = "temp_client_override"
        self.p4.client = ""
        self.assertNotEqual(self.p4.client, "temp_client_override",
                           "Setting client='' did not clear override")

        # Restore original client
        self.p4.client = original_client

        # Restore to original and verify commands still work correctly
        self.p4.user = original_user
        self.p4.password = ""
        final_info = self.p4.run_info()[0]
        self.assertEqual(final_info['userName'], original_user,
                        "Could not restore to original user")

    def testOutput(self):
        self.p4.connect()
        self._setClient()

        testDir = 'test_output'
        files = self.createFiles(testDir)

        change = self.p4.fetch_change()
        self.assertTrue( isinstance(change, P4.Spec), "Change spec is not of type P4.Spec")
        change._description = "My Output Test"

        s = self.p4.run_submit(change)

        self.p4.exception_level = P4.P4.RAISE_NONE
        self.p4.run_sync();
        self.p4.run_sync();

        self.assertNotEqual( len(self.p4.warnings), 0, "No warnings reported")
        self.assertEqual( len(self.p4.errors), 0, "Errors reported")
        self.assertNotEqual( len(self.p4.messages), 0, "No messages reported")
        self.assertTrue( isinstance(self.p4.warnings[0],str), "Warning is not a string" )

        m = self.p4.messages[0]
        self.assertTrue( isinstance(m, P4API.P4Message), "First object of messages is not a P4Message")
        self.assertEqual( m.severity, P4.P4.E_WARN, "Severity was not E_WARN" )
        self.assertEqual( m.generic, P4.P4.EV_EMPTY, "Wasn't an empty message" )
        self.assertEqual( m.msgid, 6532, "Got the wrong message: %d" % m.msgid )


    def testExceptions(self):
        self.assertRaises(P4.P4Exception, self.p4.run_edit, "foo")

        self.p4.connect()
        self.assertRaises(P4.P4Exception, self.p4.run_edit, "foo")
        self.assertEqual( len(self.p4.errors), 1, "Did not find any errors")

    def testExceptionMessages(self):
        """Test that P4Exception exposes structured error attributes and survives pickle round-trip"""
        self.p4.connect()
        self._setClient()

        testDir = 'test_exception_messages'
        files = self.createFiles(testDir)
        change = self.p4.fetch_change()
        change._description = "Exception messages test"
        self._doSubmit("Failed to submit", change)

        # Warning-level: sync when already up-to-date
        self.p4.exception_level = P4.P4.RAISE_ALL
        try:
            self.p4.run_sync()
            self.fail('Expected P4Exception for up-to-date sync')
        except P4.P4Exception as e:
            # Structured attributes from P4Message
            self.assertGreater(len(e.messages), 0)
            self.assertEqual(e.severity, P4.P4.E_WARN)
            self.assertIsInstance(e.generic, P4Exception.Generic)
            self.assertGreater(len(e.fmt), 0)
            self.assertNotIn('code', e.fmt_args)
            self.assertNotIn('fmt', e.fmt_args)

            # Capture values before pickle
            before_str = str(e)
            before_errors = e.errors
            before_warnings = e.warnings
            before_severity = e.severity
            before_generic = e.generic
            before_msgid = e.msgid
            before_fmt = e.fmt
            before_fmt_args = e.fmt_args
            before_msg_count = len(e.messages)
            before_msg_severity = e.messages[0].severity
            before_msg_generic = e.messages[0].generic
            before_msg_msgid = e.messages[0].msgid
            before_msg_dict = e.messages[0].dict
            before_msg_str = str(e.messages[0])

            # Pickle round-trip
            restored = pickle.loads(pickle.dumps(e))

            # Verify restored exception type
            self.assertIsInstance(restored, P4.P4Exception)

            # Verify messages restored as P4MessageProxy
            self.assertIsInstance(restored.messages[0], P4.P4MessageProxy)

            # Compare after pickle values against before pickle values
            self.assertEqual(str(restored), before_str)
            self.assertEqual(restored.errors, before_errors)
            self.assertEqual(restored.warnings, before_warnings)
            self.assertEqual(restored.severity, before_severity)
            self.assertEqual(restored.generic, before_generic)
            self.assertEqual(restored.msgid, before_msgid)
            self.assertEqual(restored.fmt, before_fmt)
            self.assertEqual(restored.fmt_args, before_fmt_args)
            self.assertEqual(len(restored.messages), before_msg_count)
            self.assertEqual(restored.messages[0].severity, before_msg_severity)
            self.assertEqual(restored.messages[0].generic, before_msg_generic)
            self.assertEqual(restored.messages[0].msgid, before_msg_msgid)
            self.assertEqual(restored.messages[0].dict, before_msg_dict)
            self.assertEqual(str(restored.messages[0]), before_msg_str)


    # father's little helpers

    def _setClient(self):
        """Creates a client and makes sure it is set up"""
        self.assertTrue(self.p4.connected(), "Not connected")
        self.p4.cwd = self.client_root
        self.p4.client = "TestClient"
        client = self.p4.fetch_client()
        client._root = self.client_root
        self.p4.save_client(client)

    def _doSubmit(self, msg, *args):
        """Submits the changes"""
        try:
            result = self.p4.run_submit(*args)
            self.assertTrue( 'submittedChange' in result[-1], msg)
        except P4.P4Exception as inst:
            self.fail("submit failed with exception ")

    def test_set_var_limitmap(self):
        """set_var forwards a per-command server variable to ClientApi::SetVar.

        limitMap entries (limitMap0, limitMap1, ...) restrict sync/files/fstat
        output server-side to the mapped paths.  We submit files under three
        distinct //depot directories, limit a 'files' command to two of them
        via limitMap0/limitMap1, and confirm only those directories' files come
        back.  A subsequent command on the SAME connection must be unfiltered,
        proving the vars did not leak across Runs (the P4 C++ API clears set
        vars after each Run).
        """
        self.p4.connect()
        self.assertTrue(self.p4.connected(), "Not connected")
        self._setClient()

        # Submit one file under each of //depot/dir1, //depot/dir2, //depot/dir3.
        submitted = []
        for subdir in ("dir1", "dir2", "dir3"):
            absDir = os.path.join(self.client_root, subdir)
            os.mkdir(absDir)
            fname = os.path.join(absDir, "file.txt")
            with open(fname, "w") as f:
                f.write("content in %s\n" % subdir)
            self.p4.run_add(subdir + "/file.txt")
            submitted.append("//depot/%s/file.txt" % subdir)
        self.p4.run_submit("-d", "set_var limitMap test")

        # Sanity check: without any limit, all files are visible.
        allFiles = self.p4.run_files("//depot/...")
        allPaths = sorted(f["depotFile"] for f in allFiles)
        self.assertEqual(allPaths, sorted(submitted),
                         "expected all files before applying limitMap")

        # Restrict the very next command to //depot/dir1 and //depot/dir2 via
        # two limitMap entries (limitMap0 and limitMap1).
        self.p4.set_var("limitMap0", "//depot/dir1/...")
        self.p4.set_var("limitMap1", "//depot/dir2/...")
        limited = self.p4.run_files("//depot/...")
        limitedPaths = sorted(f["depotFile"] for f in limited)
        self.assertEqual(limitedPaths,
                         ["//depot/dir1/file.txt", "//depot/dir2/file.txt"],
                         "limitMap0/limitMap1 should restrict output to dir1 and dir2")

        # The var must not leak: the next command on the same connection is
        # unfiltered again.
        after = self.p4.run_files("//depot/...")
        afterPaths = sorted(f["depotFile"] for f in after)
        self.assertEqual(afterPaths, sorted(submitted),
                         "set_var must not leak into the following command")

    def testResolve(self):
        testDir = 'test_resolve'
        testAbsoluteDir = os.path.join(self.client_root, testDir)
        os.mkdir(testAbsoluteDir)

        self.p4.connect()
        self.assertTrue(self.p4.connected(), "Not connected")
        self._setClient()
        self.assertEqual(len(self.p4.run_opened()), 0, "Shouldn't have open files")

        # create the file for testing resolve

        file = "foo"
        fname = os.path.join(testAbsoluteDir, file)
        f = open(fname, "w")
        f.write("First Line")
        f.close()
        textFile = testDir + "/" + file
        self.p4.run_add(textFile)

        file = "bin"
        bname = os.path.join(testAbsoluteDir, file)
        f = open(bname, "w")
        f.write("First Line")
        f.close()
        binFile = testDir + "/" + file
        self.p4.run_add("-tbinary", binFile)

        change = self.p4.fetch_change()
        change._description = "Initial"
        self._doSubmit("Failed to submit initial", change)

        # create a second revision

        self.p4.run_edit(textFile, binFile)
        with open(fname, "a") as f:
            f.write("Second Line")
        with open(bname, "a") as f:
            f.write("Second Line")

        change = self.p4.fetch_change()
        change._description = "Second"
        self._doSubmit("Failed to submit second", change)

        # now sync back to first revision

        self.p4.run_sync(textFile + "#1")

        # edit the first revision, thus setting up the conflict

        self.p4.run_edit(textFile)

        # sync back the head revision, this will schedule the resolve

        self.p4.run_sync(textFile)

        class TextResolver(P4.Resolver):
            def __init__(self, testObject):
                self.t = testObject

            def resolve(self, mergeData):
                self.t.assertEqual(mergeData.your_name, "//TestClient/test_resolve/foo",
                    "Unexpected your_name: %s" % mergeData.your_name)
                self.t.assertEqual(mergeData.their_name, "//depot/test_resolve/foo#2",
                    "Unexpected their_name: %s" % mergeData.their_name)
                self.t.assertEqual(mergeData.base_name, "//depot/test_resolve/foo#1",
                    "Unexpected base_name: %s" % mergeData.base_name)
                self.t.assertEqual(mergeData.merge_hint, "at", "Unexpected merge hint: %s" % mergeData.merge_hint)
                return "at"

        self.p4.run_resolve(resolver = TextResolver(self))

        # test binary file resolve which crashed previous version of P4Python

        self.p4.run_sync(binFile + "#1")
        self.p4.run_edit(binFile)
        self.p4.run_sync(binFile)

        class BinaryResolver(P4.Resolver):
            def __init__(self, testObject):
                self.t = testObject

            def resolve(self, mergeData):
                self.t.assertEqual(mergeData.your_name, "",
                    "Unexpected your_name: %s" % mergeData.your_name)
                self.t.assertEqual(mergeData.their_name, "",
                    "Unexpected their_name: %s" % mergeData.their_name)
                self.t.assertEqual(mergeData.base_name, "",
                    "Unexpected base_name: %s" % mergeData.base_name)
                self.t.assertNotEqual(mergeData.your_path, None,
                    "YourPath is empty")
                self.t.assertNotEqual(mergeData.their_path, None,
                    "TheirPath is empty")
                self.t.assertEqual(mergeData.base_path, None,
                    "BasePath is not empty")
                self.t.assertEqual(mergeData.merge_hint, "at", "Unexpected merge hint: %s" % mergeData.merge_hint)
                return "at"

        self.p4.run_resolve(resolver = BinaryResolver(self))

        change = self.p4.fetch_change()
        change._description = "Third"
        self._doSubmit("Failed to submit third", change)

        if self.p4.server_level >= 31:
            self.p4.run_integrate("//TestClient/test_resolve/foo", "//TestClient/test_resolve/bar")
            self.p4.run_reopen("-t+w", "//TestClient/test_resolve/bar")
            self.p4.run_edit("-t+x", "//TestClient/test_resolve/foo")

            change = self.p4.fetch_change()
            change._description = "Fourth"
            self._doSubmit("Failed to submit fourth", change)

            self.p4.run_integrate("-3", "//TestClient/test_resolve/foo", "//TestClient/test_resolve/bar")
            result = self.p4.run_resolve("-n")

            self.assertEqual(len(result), 2, "No two resolves scheduled")

            class ActionResolver(P4.Resolver):
                def __init__(self, testObject):
                    self.t = testObject

                def resolve(self, mergeData):
                    self.t.assertEqual(mergeData.your_name, "//TestClient/test_resolve/bar",
                        "Unexpected your_name: %s" % mergeData.your_name)
                    self.t.assertEqual(mergeData.their_name, "//depot/test_resolve/foo#4",
                        "Unexpected their_name: %s" % mergeData.their_name)
                    self.t.assertEqual(mergeData.base_name, "//depot/test_resolve/foo#3",
                        "Unexpected base_name: %s" % mergeData.base_name)
                    self.t.assertEqual(mergeData.merge_hint, "at", "Unexpected merge hint: %s" % mergeData.merge_hint)
                    return "at"

                def actionResolve(self, mergeData):
                    self.t.assertEqual(mergeData.merge_action, "(text+Dwx)",
                        "Unexpected mergeAction: '%s'" % mergeData.merge_action  )
                    self.t.assertEqual(mergeData.yours_action, "(text+w)",
                        "Unexpected mergeAction: '%s'" % mergeData.yours_action  )
                    self.t.assertEqual(mergeData.their_action, "(text+x)",
                        "Unexpected mergeAction: '%s'" % mergeData.their_action  )
                    self.t.assertEqual(mergeData.type, "Filetype resolve",
                        "Unexpected type: '%s'" % mergeData.type)

                    # check the info hash values
                    self.t.assertTrue(mergeData.info['clientFile'].endswith(os.path.join('client','test_resolve', 'bar')),
                        "Unexpected clientFile info: '%s'" % mergeData.info['clientFile'])
                    self.t.assertEqual(mergeData.info['fromFile'], '//depot/test_resolve/foo',
                        "Unexpected fromFile info: '%s'" % mergeData.info['fromFile'])
                    self.t.assertEqual(mergeData.info['resolveType'], 'filetype',
                        "Unexpected resolveType info: '%s'" % mergeData.info['resolveType'])

                    return "am"

            self.p4.run_resolve(resolver=ActionResolver(self))

    def testMap(self):
        # don't need connection, simply test all the Map features

        map = P4.Map()
        self.assertEqual(map.count(), 0, "Map does not have count == 0")
        self.assertEqual(map.is_empty(), True, "Map is not empty")

        map.insert("//depot/main/... //ws/...")
        self.assertEqual(map.count(), 1, "Map does not have 1 entry")
        self.assertEqual(map.is_empty(), False, "Map is still empty")

        self.assertEqual(map.includes("//depot/main/foo"), True, "Map does not map //depot/main/foo")
        self.assertEqual(map.includes("//ws/foo", False), True, "Map does not map //ws/foo")

        map.insert("-//depot/main/exclude/... //ws/exclude/...")
        self.assertEqual(map.count(), 2, "Map does not have 2 entries")
        self.assertEqual(map.includes("//depot/main/foo"), True, "Map does not map foo anymore")
        self.assertEqual(map.includes("//depot/main/exclude/foo"), False, "Map still maps foo")
        self.assertEqual(map.includes("//ws/foo", False), True, "Map does not map foo anymore (reverse)")
        self.assertEqual(map.includes("//ws/exclude/foo"), False, "Map still maps foo (reverse)")

        map.clear()
        self.assertEqual(map.count(), 0, "Map has elements after clearing")
        self.assertEqual(map.is_empty(), True, "Map is still not empty after clearing")

        a = [ "//depot/main/... //ws/main/..." ,
              "//depot/main/doc/... //ws/doc/..."]
        map = P4.Map(a)
        self.assertEqual(map.count(), 3, "Map does not contain 3 elements")

        map2 = P4.Map("//ws/...", r"C:\Work\...")
        self.assertEqual(map2.count(), 1, "Map2 does not contain any elements")

        map3 = P4.Map.join(map, map2)
        self.assertEqual(map3.count(), 3, "Join did not produce three entries")

        map.clear()
        map.insert( '"//depot/dir with spaces/..." "//ws/dir with spaces/..."' )
        self.assertEqual( map.includes("//depot/dir with spaces/foo"), True, "Quotes not handled correctly" )

        map.clear()
        map = P4.Map(['//depot/a/... a/...', '+//depot/b/... b/...'])
        self.assertEqual( map.as_array(), ['//depot/a/... a/...', '+//depot/b/... b/...'], "+ mappings not handled appropriatly" )
        self.assertEqual( map.lhs(), ['//depot/a/...', '+//depot/b/...'], "+ mappings not handled appropriatly" )

        # & map test disabled until fixed in P4API
        map.clear()
        map = P4.Map(['//depot/a/... a/...', '&//depot/a/... b/...'])
        self.assertEqual( map.as_array(), ['//depot/a/... a/...', '&//depot/a/... b/...'], "& mappings not handled appropriatly" )
        self.assertEqual( map.lhs(), ['//depot/a/...', '&//depot/a/...'], "& mappings not handled appropriatly" )

        # test P4Map.translate and P4Map.translate_array
        map.clear()
        map = P4.Map(['//depot/a/... a/...', '&//depot/a/... b/...'])
        self.assertEqual( map.translate("//depot/a/foo"), "a/foo", "P4Map.translate not handled correctly")
        self.assertEqual( map.translate("a/foo", 0), "//depot/a/foo", "P4Map.translate not handled correctly")
        self.assertEqual( map.translate_array("//depot/a/foo"), ["b/foo", "a/foo"], "P4Map.translate not handled correctly")

    def testThreads( self ):
            import threading

            class AsyncInfo( threading.Thread ):
                    def __init__( self, port ):
                            threading.Thread.__init__( self )
                            self.p4 = P4.P4()
                            self.p4.port = port

                    def run( self ):
                            self.p4.connect()
                            info = self.p4.run_info()
                            self.p4.disconnect()

            threads = []
            for i in range(1,10):
                    self.ensureDirectory(self.server_root+"/"+ str(i))
                    threads.append( AsyncInfo("rsh:%s -r \"%s\" -L log -vserver=3 -i" % ( self.p4d, self.server_root+"/"+ str(i))))
            for thread in threads:
                    thread.start()
            for thread in threads:
                    thread.join()

    def testArguments( self ):
        p4 = P4.P4(debug=3, port="9999", client="myclient")
        self.assertEqual(p4.debug, 3)
        self.assertEqual(p4.port, "9999")
        self.assertEqual(p4.client, "myclient")

    def testUnicode( self ):
        self.enableUnicode()

        testDir = 'test_files'
        testAbsoluteDir = os.path.join(self.client_root, testDir)
        os.mkdir(testAbsoluteDir)

        self.p4.charset = 'iso8859-1'
        self.p4.connect()
        self._setClient()

        # create a bunch of files
        tf = os.path.join(testDir, "unicode.txt")
        fname = os.path.join(self.client_root, tf)

        if sys.version_info < (3,0):
            with open(fname, "w") as f:
                f.write("This file cost \xa31")
        else:
            with open(fname, "wb") as f:
                f.write("This file cost \xa31".encode('iso8859-1'))

        self.p4.run_add('-t', 'unicode', tf)

        self.p4.run_submit("-d", "Unicode file")

        self.p4.run_sync('...#0')
        self.p4.charset = 'utf8'

        self.p4.run_sync()
        if sys.version_info < (3,0):
            with open(fname, 'r') as f:
                buf = f.read()
                self.assertTrue(buf == "This file cost \xc2\xa31", "File not found, UNICODE support broken?")
        else:
            with open(fname, 'rb') as f:
                buf = f.read()
                self.assertTrue(buf == "This file cost \xa31".encode('utf-8'), "File not found, UNICODE support broken?")

            ch = self.p4.run_changes(b'-m1')
            self.assertEqual(len(ch), 1, "Byte strings broken")

        self.p4.disconnect()

    def testTrack( self ):
        success = self.p4.track = 1
        self.assertTrue(success, "Failed to set performance tracking")
        self.p4.connect()
        self.assertTrue(self.p4.connected(), "Failed to connect")
        try:
          self.p4.track = 0
          self.assertTrue(self.p4.track, "Changing performance tracking is not allowed")
        except P4Exception:
          pass
        self.p4.run_info()
        self.assertTrue(len(self.p4.track_output), "No performance tracking reported")

    def testOutputHandler( self ):
        self.assertEqual( self.p4.handler, None )

        # create the standard iterator and try to set it
        h = P4.OutputHandler()
        self.p4.handler = h
        self.assertEqual( self.p4.handler, h )

        # test the resetting
        self.p4.handler = None
        self.assertEqual( self.p4.handler, None )

        self.p4.connect()
        self._setClient()

        class MyOutputHandler(P4.OutputHandler):
            def __init__(self):
                P4.OutputHandler.__init__(self)
                self.statOutput = []
                self.infoOutput = []
                self.messageOutput = []

            def outputStat(self, stat):
                self.statOutput.append(stat)
                return P4.OutputHandler.HANDLED

            def outputInfo(self, info):
                self.infoOutput.append(info)
                return P4.OutputHandler.HANDLED

            def outputMessage(self, msg):
                self.messageOutput.append(msg)
                return P4.OutputHandler.HANDLED

        testDir = 'test-handler'
        files = self.createFiles(testDir)

        change = self.p4.fetch_change()
        change._description = "My Handler Test"

        self._doSubmit("Failed to submit the add", change)

        h = MyOutputHandler()
        self.p4.handler = h

        self.assertEqual( len(self.p4.run_files('...')), 0, "p4 does not return empty list")
        self.assertEqual( len(h.statOutput), len(files), "Less files than expected")
        self.assertEqual( len(h.messageOutput), 0, "Messages unexpected")
        self.p4.handler = None

    def testProgress( self ):
        self.p4.connect()
        self._setClient()
        testDir = "progress"

        testAbsoluteDir = os.path.join(self.client_root, testDir)
        os.mkdir(testAbsoluteDir)

        if self.p4.server_level >= 33:
            class TestProgress( P4.Progress ):
                def __init__(self):
                    P4.Progress.__init__(self)
                    self.invoked = 0
                    self.types = []
                    self.descriptions = []
                    self.units = []
                    self.totals = []
                    self.positions = []
                    self.dones = []

                def init(self, type):
                    self.types.append(type)
                def setDescription(self, description, unit):
                    self.descriptions.append(description)
                    self.units.append(unit)
                def setTotal(self, total):
                    self.totals.append(total)
                def update(self, position):
                    self.positions.append(position)
                def done(self, fail):
                    self.dones.append(fail)

            # first, test the submits
            self.p4.progress = TestProgress()

            # create a bunch of files, fill them with content, and add them
            total = 100
            for i in range(total):
                fname = os.path.join(testAbsoluteDir, "file%02d" % i)
                with open(fname, 'w') as f:
                    f.write('A'*1024) # write 1024 'A' characters to create 1K file
                    self.p4.run_add(fname)
            self.p4.run_submit('-dSome files')

            self.assertEqual(len(self.p4.progress.types), total, "Did not receive %d progress initialize calls" % total)
            self.assertEqual(len(self.p4.progress.descriptions), total, "Did not receive %d progress description calls" % total)
            self.assertEqual(len(self.p4.progress.totals), total, "Did not receive %d progress totals calls" % total)
            self.assertEqual(len(self.p4.progress.positions), total, "Did not receive %d progress positions calls" % total)
            self.assertEqual(len(self.p4.progress.dones), total, "Did not receive %d progress dones calls" % total)

            class TestOutputAndProgress( P4.Progress, P4.OutputHandler ):
                def __init__(self):
                    P4.Progress.__init__(self)
                    P4.OutputHandler.__init__(self)
                    self.totalFiles = 0
                    self.totalSizes = 0

                def outputStat(self, stat):
                    if 'totalFileCount' in stat:
                        self.totalFileCount = int(stat['totalFileCount'])
                    if 'totalFileSize' in stat:
                        self.totalFileSize = int(stat['totalFileSize'])
                    return P4.OutputHandler.HANDLED

                def outputInfo(self, info):
                    return P4.OutputHandler.HANDLED

                def outputMessage(self, msg):
                    return P4.OutputHandler.HANDLED

                def init(self, type):
                    self.type = type
                def setDescription(self, description, unit):
                    pass
                def setTotal(self, total):
                    pass
                def update(self, position):
                    self.position = position
                def done(self, fail):
                    self.fail = fail

            callback = TestOutputAndProgress()
            self.p4.run_sync('-f', '-q', '//...', progress=callback, handler=callback)

            self.assertEqual(callback.totalFileCount, callback.position,
                            "Total does not match position %d <> %d" % (callback.totalFileCount, callback.position))
            self.assertEqual(total, callback.position,
                            "Total does not match position %d <> %d" % (total, callback.position))
        else:
            print("Test case testProgress needs a 2012.2+ Perforce Server to run")

    def testStreams( self ):
        self.p4.connect()
        self._setClient()

        if self.p4.server_level >= 30:
            self.assertEqual( self.p4.streams, 1, "Streams are not enabled")

            # Create the streams depot

            d = self.p4.fetch_depot( "streams" )
            d._type = 'stream'
            self.p4.save_depot( d )

            # create a stream

            s = self.p4.fetch_stream( "//streams/main" )
            s._description = 'Main line stream'
            s._type = 'mainline'
            self.p4.save_stream( s )

            # check if stream exists
            # due to a server "feature" we need to disconnect and reconnect first

            self.p4.disconnect()
            self.p4.connect()

            streams = self.p4.run_streams()
            self.assertEqual( len(streams), 1, "Couldn't find any streams")
        else:
            print("Test case testStreams needs a 2010.2+ Perforce Server to run")

    def testGraph( self ):
        self.p4.connect()
        self._setClient()

        if self.p4.server_level >= 43:
            self.assertEqual( self.p4.graph, 1, "Graph is not enabled")

            self.p4.graph = 0
            self.assertEqual( self.p4.graph, 0, "Graph is not disabled")

            self.p4.graph = 1
            self.assertEqual( self.p4.graph, 1, "Graph is not re-enabled")

            # create graph depot

            d = self.p4.fetch_depot( "repo" )
            d._type = 'graph'
            self.p4.save_depot( d )

            r = self.p4.fetch_repo( "//repo/repo" )
            self.p4.save_repo( r )

            # check graph depot is there
            depots = self.p4.run_depots()
            self.assertEqual( len(depots), 2, "Cannot see graph depot" )
        else:
            print("Test case testGraph needs a 2017.1 Perforce Server to run")

    def check_spec( self, spec_name, parameter):
        """Check a single spec.
   Takes the name and a potential parameter as an argument.
   Some specs like change or triggers don't require (or are not even allowed) a parameter.
   Other specs like depot or label require a parameter. Streams are particularly picky.

   First, we pick up the spec definition from the server.
   Then we test whether we can set all fields without error. We need to distinguish
   between single word fields and fields that require a list.

   Finally, use format_spec to create a string and then use an independent P4 instance
   to test whether the compiled job string matches the server-provided spec string.

   This could fail for jobs (because of the jobspec), but since this is a freshly
   created server, it will succeed if all is compiled correctly.
    """

        spec = self.p4.fetch_spec(spec_name)
        fields = spec["Fields"]

        field_names = []
        for field in fields:
            elems = field.split()
            name = elems[1]
            type = elems[2]
            field_names.append( (name, type) )

        args = [ spec_name, "-o" ]
        if parameter:
            args.append(parameter)
        trial_spec = self.p4.run(args)[0]
        for name, tp in field_names:
            if "list" in tp:
                arg = [ name ]
            else:
                arg = name
            trial_spec[name] = arg

        spec_string = self.p4.format_spec(spec_name, trial_spec)

        p4_2 = P4.P4()
        try:
            reparsed = p4_2.parse_spec(spec_name, spec_string)
        except P4.P4Exception as e:
            self.fail("Spec '{0}' failed with {1}".format(spec_name, e))
        del p4_2

    def testAllSpecs( self ):
        self.p4.connect()

        # create a bunch of specs
        # try to iterate through them afterwards

        self._setClient() #
        depot = self.p4.fetch_depot("stream")
        depot._type = 'stream'
        self.p4.save_depot(depot)

        specs = {
            'branch'   : "test_branch",
            'change'   : None,
            'client'   : "test_client",
            'depot'    : "test_depot",
            'group'    : "test_group",
            'job'      : "test_job",
            'label'    : "test_label",
            'ldap'     : "test_ldap",
            'protect'  : None,
            'remote'   : "test_remote",
            'repo'     : "//repo/repo",
            'server'   : "test_server",
            'stream'   : "//stream/main",
            'spec'     : "job", # this is the only spec I am allowed to overwrite
            'triggers' : None,
            'typemap'  : None,
            'user'     : "test_user"
        }

        for spec, parameter in specs.items():
            self.check_spec(spec, parameter)

    def testSpecs( self ):
        self.p4.connect()

        clients = []
        c = self.p4.fetch_client('client1')
        self.p4.save_client(c)
        clients.append(c._client)
        c = self.p4.fetch_client('client2')
        self.p4.save_client(c)
        clients.append(c._client)

        for c in self.p4.iterate_clients():
            self.assertTrue(c._client in clients, "Cannot find client in iteration")

        labels = []
        l = self.p4.fetch_label('label1')
        self.p4.save_label(l)
        labels.append(l._label)
        l = self.p4.fetch_label('label2')
        self.p4.save_label(l)
        labels.append(l._label)

        for l in self.p4.iterate_labels():
            self.assertTrue(l._label in labels, "Cannot find labels in iteration")

        groups = []
        g = self.p4.fetch_group('group1')
        g._users = [self.p4.user, 'user2']
        self.p4.save_group(g)
        groups.append(g._group)

        g = self.p4.fetch_group('group2')
        g._users = [self.p4.user]
        self.p4.save_group(g)
        groups.append(g._group)

        group_rows = []
        group_names = []
        for g in self.p4.iterate_groups():
            group_rows.append(g)
            name = g.get('Group') if isinstance(g, dict) else None
            self.assertTrue(name in groups, "Cannot find group in iteration")
            group_names.append(name)

        self.assertEqual(len(group_names), len(set(group_names)), "iterate_groups returned duplicate groups")

    # P4.encoding is only available (and undoc'd) in Python 3
    # Something in Python 3.7 prevents writing filenames that aren't valid UTF8

    if sys.version_info[0] == 3 and sys.version_info[1] < 7:
        def testEncoding( self ):
            self.p4.connect()
            self.p4.encoding = 'raw'

            self.assertEqual(self.p4.encoding, 'raw', "Encoding is not raw")
            info = self.p4.run_info()[0]
            self.assertEqual(type(info['serverVersion']), bytes, "Type of string is not bytes")

            self._setClient()

            testDir = "testDir"
            testAbsoluteDir = os.path.join(self.client_root, testDir)
            os.mkdir(testAbsoluteDir)

            self.p4.encoding = 'iso8859-1'
            # create a file with windows encoding for its filename
            uname = platform.uname()
            if uname.system == 'Darwin':
                comp = re.compile(r'(\d+)\.(\d+)\.(\d+)')
                match = comp.match(uname.release)
                major = int(match.group(1))
                if major >= 16: # macos Sierra or higher
                    self.p4.encoding = 'utf-8'

            filename = 'öäüÖÄÜß.txt'
            fname = os.path.join(testAbsoluteDir, filename)
            encodedName = fname.encode(self.p4.encoding)
            with open(encodedName, "w") as f:
                f.write("Test Text")

            self.p4.run_add(fname)
            self.p4.run_submit('-dAdded file')


    def testIgnore( self ):
        P4IGNORE = ".myignore"
        self.p4.connect()

        os.environ["P4IGNORE"] = P4IGNORE
        self.assertEqual(self.p4.env("P4IGNORE"), P4IGNORE, "Could not set environment for P4IGNORE")

        self.assertEqual(self.p4.ignore_file, P4IGNORE, "Environment set ignore_file incorrect")

        ignoreFile = os.path.join( self.server_root, ".testignore" )
        self.p4.ignore_file = ignoreFile
        self.assertEqual(self.p4.ignore_file, ignoreFile , "P4 set ignore_file incorrect")

        with open(self.p4.ignore_file, "w") as f:
            f.write("add.txt")

        self.assertTrue(self.p4.is_ignored("add.txt"), "File 'add.txt' is not ignored")
        self.assertFalse(self.p4.is_ignored("something.else"), "File 'something.else' is ignored")

    def testUntaggedSpecs( self ):
        self.p4.connect()

        label = self.p4.fetch_label("label")
        label._description = "Client for testing specs"
        self.p4.save_label(label)
        label = self.p4.fetch_label("label")

        untagged = self.p4.fetch_label("label", tagged=False)
        untagged_direct = self.p4.run_label("-o", "label", tagged=False)[0]

        self.assertEqual(untagged, untagged_direct, "fetch and direct do not match")

        parsed = self.p4.parse_label(untagged)

        self.assertEqual(parsed, label, "parsed and fetched do not match")

    def testEnviro( self ):
        self.p4.connect()

        TEST_P4ENVIRO = '.test_p4enviro'
        # save in case we want to reset it later
        enviro = self.p4.p4enviro_file
        self.p4.p4enviro_file = TEST_P4ENVIRO

        self.assertEqual(self.p4.p4enviro_file, TEST_P4ENVIRO, "Did not set P4ENVIRO correctly")

    def testLogger( self ):
        import logging
        try:
            from StringIO import StringIO
        except ImportError:
            from io import StringIO

        self.p4.connect()

        # set up a String stream for log testing
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        format = logging.Formatter('%(levelname)s:%(message)s')
        handler.formatter = format

        self.p4.logger = logging.getLogger('TestP4Logger')
        self.p4.logger.setLevel(logging.INFO)
        self.p4.logger.addHandler(handler)

        self.assertEqual(self.p4.debug, 0, "Debug is not 0")

        # Simple log test with no debug output
        self.p4.run_info()
        self.assertEqual(stream.getvalue(), "INFO:p4 info\n", "Logging stream contains '{0}'".format(stream.getvalue()))

        stream.truncate(0)
        stream.seek(0) # not necessary in Python2, but required for Python3

        # Now with an exception, should raise a WARNING

        self.assertRaises(P4Exception, lambda : self.p4.run_files('//depot/foobar'))

        self.assertEqual(stream.getvalue(),
                         "INFO:p4 files //depot/foobar\n"
                         "WARNING://depot/foobar - no such file(s).\n",
                         "Unexpected {0}".format(stream.getvalue()))

        stream.truncate(0)
        stream.seek(0) # not necessary in Python2, but required for Python3

        # Now without an exception, but still with WARNING output - and now with DEBUG output as well

        self.p4.logger.setLevel(logging.DEBUG)
        self.p4.run_files('//depot/foobar', exception_level=0)

        self.assertEqual(stream.getvalue(),
                         "INFO:p4 files //depot/foobar\n"
                         "WARNING://depot/foobar - no such file(s).\n"
                         "DEBUG:[]\n",
                         "Unexpected {0}".format(stream.getvalue()))

        self.p4.logger = None
        self.assertEqual(self.p4.logger, None, "Logger not reset correctly")

    def testDVCS_init( self ):
        self.p4.connect()
        current_pwd = self.server_root

        if self.p4.server_level >= 39:
            self.assertRaises(Exception, P4.clone, [], directory="cloned")
            # need to reset directory again, P4.clone moves it
            os.chdir(current_pwd)
            os.environ["PWD"] = current_pwd
            try:
                dvcs = P4.init(directory="dvcs",unicode=True,charset="utf8",casesensitive=False)
                dvcs.connect()
                depots = dvcs.run_depots()
                dvcs.disconnect()
                # need to reset directory again, P4.init moves it
                os.chdir(current_pwd)
                os.environ["PWD"] = current_pwd
            except Exception as e:
                self.fail("P4.run_init() raised exception {0}".format(e))

    def testDVCS_clone( self ):
        self.p4.connect()
        current_pwd = self.server_root

        if self.p4.server_level >= 39:
            self._setClient()

            testDir = 'test_files'
            files = self.createFiles(testDir)

            change = self.p4.fetch_change()
            change._description = "My Add Test"

            self._doSubmit("Failed to submit the add", change)

            result = self.p4.run_configure('set','server.allowfetch=3')
            result = self.p4.run_configure('set','server.allowpush=3')

            self.p4.disconnect() # need to disconnect to enable the configure variables
            self.p4.connect()

            result = self.p4.run_configure('show', 'server.allowfetch')
            self.assertEqual(result[0]['Value'], "3", "server.allowfetch not set to 3")

            result = self.p4.run_configure('show', 'server.allowpush')
            self.assertEqual(result[0]['Value'], "3", "server.allowpush not set to 3")

            self.p4.disconnect()

            os.chdir(current_pwd)
            try:
                target_dir = os.path.join(current_pwd, "dvcs")
                dvcs = P4.clone(directory=target_dir, port=self.port, file="//depot/test_files/...")
                dvcs.connect()
                files = dvcs.run_files('//...')
                self.assertNotEqual(len(files),0, "No files found!")
                dvcs.disconnect()
            except Exception as e:
                self.fail("P4.clone() raised exception {0}".format(e))

    def testSpecdefTrigger( self ):
        # need to create trigger
        # save it in the depot
        # link it from the trigger table (sys.executable)
        # update the jobspec
        # then try it out with a job

        self.assertTrue(os.path.exists("job_trigger.py"), "Can't find job_trigger.py")
        with open("job_trigger.py") as f:
            triggerCode = f.read()

        self.p4.connect()
        self._setClient()

        triggerPath = os.path.join(self.client_root, "job_trigger.py")
        with open(triggerPath, "w") as f:
            f.write(triggerCode)
        self.p4.run_add(triggerPath)
        self.p4.run_submit("-d","Added trigger")

        files = self.p4.run_files("//...")
        self.assertEqual(len(files), 1, "Not exactly one file stored")
        self.assertEqual(files[0]["depotFile"], "//depot/job_trigger.py", "File not found where expected")

        jobTrigger = 'jobtest form-out job ' \
                     '"{0} %//depot/job_trigger.py% %specdef% %formname% %formfile%"'.format(sys.executable)

        triggers = self.p4.fetch_triggers()
        triggers._triggers = [ jobTrigger ]
        self.p4.save_triggers(triggers)

        # need to bounce connecting to reload trigger table
        self.p4.disconnect()
        self.p4.connect()

        jobspec = self.p4.fetch_jobspec()
        jobspec._fields.append("110 Project word 32 optional")
        self.p4.save_jobspec(jobspec)

        job = self.p4.fetch_job("myjob")

        self.assertEqual(job._status, "suspended", "Trigger did not change status to suspended")
        job._description = "Testing jobspec and job triggers"
        job._project = "NewProject"
        self.p4.save_job(job)

        job = self.p4.fetch_job("myjob")
        self.assertEqual(job._job, "myjob", "Job name not correct")
        self.assertEqual(job._project, "NewProject", "Job project name not set")

    def testProtectionWithComment( self ):
        # create protection table with comments
        # save protection table
        # reload protection table
        # verify it works

        protectionView = ["## First line",
                          "write user * * //... ## standard",
                          "admin user tom 127.0.0.1 //... ## special admin user"
                          "## Super entry following",
                          "super user {0} * //... ## standard super user".format(self.p4.user)
                         ]

        self.p4.connect()
        current_pwd = self.server_root

        if self.p4.server_level >= 41: # 2016.1
            # double check we have the right patch level
            if self.getServerPatchLevel(self.p4.run_info()) >= 1398982:
                protect = self.p4.fetch_protect()
                protect._protections = protectionView
                self.p4.save_protect(protect)

                protect = self.p4.fetch_protect()

                self.assertEqual(protectionView, protect._protections, "Views are not identical")
            else:
                print("\n*** Please upgrade to at least 2016.1 Patch 2 (1398982) ***")

    def testStringAsListOfOne( self ):
        self.p4.connect()
        client = self.p4.fetch_client()
        altRoots = [ "/tmp/foo", "/tmp/bar" ]
        client._altroots = altRoots
        self.p4.save_client(client)

        client = self.p4.fetch_client()
        self.assertEqual(client._altroots, altRoots, "AltRoots are not identical for list of two")

        altRoots = "/tmp/foo"
        client._altroots = altRoots
        self.p4.save_client(client)

        client = self.p4.fetch_client()
        self.assertEqual(client._altRoots, [ altRoots ], "AltRoots are not identical for string")

        altRoots = ""
        client._altroots = altRoots
        self.p4.save_client(client)

        client = self.p4.fetch_client()
        self.assertEqual( ("AltRoots" not in client), True , "AltRoots have not been deleted")

    def run_saved_context(self):
        with self.p4.saved_context(cwd='/tmp'):
            self.p4.run_files('...') # must fail

    def run_files(self):
        self.p4.run_files('...', cwd='/tmp')

    def testContextHandlers(self):
        self.p4.connect()
        cwd = self.p4.cwd
        self.assertRaises(P4Exception, self.run_saved_context)
        self.assertEqual(self.p4.cwd, cwd, "Context not successfully restored in with statement")

        self.assertRaises(P4Exception, self.run_files)


        self.assertEqual(self.p4.cwd, cwd, "Context not successfully restored in run method")

    def testStreamComments(self):
        self.p4.connect()
        specform = self.p4.run( "depot", "-o", "-t", "stream", "STREAM_TEST", tagged=False )[0]
        d = self.p4.fetch_depot( "STREAM_TEST" )
        d._type = 'stream'
        self.p4.save_depot( d )

        paths = ['## First comment',
            'share ... ## Second comment',
            '## Third comment']

        s = self.p4.fetch_stream( '//STREAM_TEST/TEST' ) 
        s._Paths = paths
        s._description = 'Main line stream'
        s._type = 'mainline'
        self.p4.save_stream ( s )        
        self.assertEqual(self.p4.fetch_stream( "//STREAM_TEST/TEST" )._Paths , ['## First comment', 'share ... ## Second comment', '## Third comment'] )

    
    def testEvilTwin(self):
        self.p4.connect()                
        self.p4.cwd = self.client_root
        self.p4.client = "TestClient"
        client = self.p4.fetch_client()
        client._root = self.client_root
        self.p4.save_client(client)

        # add A1
        # branch A→B
        # move A1→A2
        # readd A1
        # merge A→B

        ############################
        # Prep dirs

        dirA = os.path.join(client._root, "A")
        dirB = os.path.join(client._root, "B")
        os.mkdir(dirA)
        pathA = os.path.join(dirA, "fileA")
        pathA1 = os.path.join(dirA, "fileA1")

        ############################
        # Adding

        fileA = open( pathA, "w" )  
        fileA.write("original file")
        fileA.close()
        self.p4.run_add(pathA)
        self.p4.run("submit", "-d", "adding fileA")

        ############################
        # Branching

        branch_spec = self.p4.run("branch", "-o", "evil-twin-test")[0]
        branch_spec._View = ['//depot/A/... //depot/B/...']
        self.p4.save_branch(branch_spec)
        self.p4.run("integ", "-b", "evil-twin-test")
        self.p4.run("submit", "-d", "integrating")

        ############################
        # Moving

        self.p4.run("edit", pathA)
        self.p4.run("move", "-f", pathA, pathA1)
        self.p4.run("submit", "-d", "moving")

        ############################
        # Re-adding origianl

        fileA = open( pathA, "w" )           
        fileA.write("Re-added A")
        fileA.close()
        self.p4.run("add", pathA)
        self.p4.run("submit", "-d", "re-adding")

        ############################
        # Second merge

        self.p4.run("merge", "-b", "evil-twin-test")

        try:
            self.p4.run("submit", "-d", "integrating")

        except Exception as e:
            error = str(e)
            result = ''.join([i for i in error if not i.isdigit()])           
            expected = "Merges still pending -- use 'resolve' to merge files.\nSubmit failed -- fix problems above then use 'p submit -c '."
            self.assertEqual(result, expected)

    def testLockedClientRemoval(self):

        self.p4.connect()     

        self.p4.client = "UnlockedClient"
        unlockedClient = self.p4.fetch_client()
        unlockedClient._root = self.client_root
        unlockedClient._options = 'noallwrite noclobber nocompress unlocked nomodtime normdir'
        self.p4.save_client(unlockedClient)       
        with self.p4.temp_client("temp", "UnlockedClient"):
            self.p4.run_info()

        self.p4.client = "LockedClient"
        lockedClient = self.p4.fetch_client()
        lockedClient._root = self.client_root
        lockedClient._options = 'noallwrite noclobber nocompress locked nomodtime normdir'
        self.p4.save_client(lockedClient)       
        with self.p4.temp_client("temp", "LockedClient"):
            self.p4.run_info()
            
    def testSetbreak( self ):
        testDir = 'test_setbreak'
        testAbsoluteDir = os.path.join(self.client_root, testDir)
        os.mkdir(testAbsoluteDir)

        self.p4.connect()
        self.assertTrue(self.p4.connected(), "Not connected")
        self._setClient()

        # create the file for testing setbreak
        class MyKeepAlive(P4.PyKeepAlive):
            def __init__(self, total_count):
                P4.PyKeepAlive.__init__(self)
                self.counter = 0
                self.total_count = total_count

            def isAlive(self):
                self.counter += 1
                if self.counter > self.total_count:
                    return 0
                return 1
        
        #create a multiple changelist revision
        for i in range(100):
            file = "foo" + str(i)
            fname = os.path.join(testAbsoluteDir, file)
            line = "This is a test line to create a test file.\n"
            with open(fname, 'w') as file:
                file.write(line)
            testFile = str(fname)
            self.p4.run_add(testFile)
            
            change = self.p4.fetch_change()
            change._description = "Initial changes"
            self.p4.run_submit(change)

        if platform.system() == 'Windows':
            # On Windows with p4d 2026.1 RSH mode, setbreak causes p4d to spin
            # and never send RPC completion. RSH uses inherited pipe handles so
            # ReadFile() never unblocks even after killing p4d. Fix: use TCP
            # mode where we hold the process handle via subprocess.Popen.
            # Popen.wait() guarantees ALL file handles released before we
            # return — so tearDown's cleanupTestTree always succeeds.
            import subprocess, socket, threading, getpass as _gp

            def _start_tcp_p4d():
                """Start a fresh p4d on a free TCP port; return (proc, port)."""
                # Disconnect RSH p4d so the database is free
                if self.p4.connected():
                    self.p4.disconnect()

                # Find a free TCP port
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _s:
                    _s.bind(('localhost', 0))
                    _free_port = _s.getsockname()[1]

                # Start p4d on TCP — we own the process handle directly
                _proc = subprocess.Popen(
                    [self.p4d, '-r', self.server_root, '-L', 'log',
                     '-p', 'localhost:%d' % _free_port],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )

                # Poll until p4d accepts connections (avoids hardcoded sleep)
                for _ in range(20):
                    try:
                        with socket.create_connection(('localhost', _free_port), timeout=0.5):
                            break
                    except OSError:
                        time.sleep(0.25)
                else:
                    _proc.kill()
                    self.fail("p4d did not start on port %d" % _free_port)

                return _proc, _free_port

            def _connect_tcp(port):
                """Return a connected, logged-in P4 object on the given TCP port."""
                _p4 = P4.P4()
                _p4.port = 'localhost:%d' % port
                _p4.user = _gp.getuser()
                _p4.password = SUPER_PASSWORD
                _p4.connect()
                _p4.run_login()
                return _p4

            # --- Case 1: setbreak fires immediately (total_count=0) ---
            _p4d_proc, _free_port = _start_tcp_p4d()
            _p4_tcp = _connect_tcp(_free_port)

            ka = MyKeepAlive(total_count=0)
            _p4_tcp.setbreak(ka)

            _run_result = []
            def _run():
                try:
                    _run_result.extend(_p4_tcp.run("changes"))
                except P4Exception:
                    pass
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            t.join(30)
            self.assertFalse(t.is_alive(), "run() thread blocked for 30 s — setbreak did not fire")

            _p4_tcp.disconnect()
            # Popen.wait() blocks until the OS confirms the process is fully
            # terminated and ALL its file handles are released — guaranteed.
            _p4d_proc.kill()
            _p4d_proc.wait()

            total_files = len(_run_result)
            self.assertGreaterEqual(ka.counter, 1, "isAlive callback was not invoked")
            self.assertGreater(100, total_files, "Setbreak did not terminate the command early")

            # --- Case 2: setbreak never fires (total_count=50) ---
            _p4d_proc2, _free_port2 = _start_tcp_p4d()
            _p4_tcp2 = _connect_tcp(_free_port2)

            ka2 = MyKeepAlive(total_count=50)
            _p4_tcp2.setbreak(ka2)
            total_files2 = len(_p4_tcp2.run("changes"))
            self.assertEqual(100, total_files2, "Setbreak fired early when it should not have")

            _p4_tcp2.disconnect()
            _p4d_proc2.kill()
            _p4d_proc2.wait()

            # Replace self.p4 with fresh unconnected object so tearDown skips
            # disconnect on the stale RSH connection.
            self.p4 = P4.P4()
            self.p4.port = self.port
            self.p4.user = _gp.getuser()
            return
        else:
            ka = MyKeepAlive(total_count=0)
            self.p4.setbreak(ka)
            total_files = len(self.p4.run("changes"))
            self.assertGreater(100, total_files, "Setbreak is not working")
            self.p4.disconnect()

            self.p4.connect()
            self.assertTrue(self.p4.connected(), "Not connected")
            ka = MyKeepAlive(total_count=50)
            self.p4.setbreak(ka)
            total_files = len(self.p4.run("changes"))
            self.assertEqual(100, total_files, "Setbreak is not working")
            self.p4.disconnect()
            return

    def testMergeToolReturnCode(self):
        testDir = 'test_merge_return'
        testAbsoluteDir = os.path.join(self.client_root, testDir)
        os.mkdir(testAbsoluteDir)

        self.p4.connect()
        self.assertTrue(self.p4.connected(), "Not connected")
        self._setClient()

        # Create initial file
        file = "merge_test.txt"
        fname = os.path.join(testAbsoluteDir, file)
        with open(fname, "w") as f:
            f.write("Line 1\n")
        textFile = testDir + "/" + file
        self.p4.run_add(textFile)

        change = self.p4.fetch_change()
        change._description = "Initial version"
        self._doSubmit("Failed to submit initial", change)

        # Create second revision
        self.p4.run_edit(textFile)
        with open(fname, "w") as f:
            f.write("Line 1\nLine 2\n")
        
        change = self.p4.fetch_change()
        change._description = "Second version"
        self._doSubmit("Failed to submit second", change)

        # Sync back and create conflict
        self.p4.run_sync(textFile + "#1")
        self.p4.run_edit(textFile)
        with open(fname, "w") as f:
            f.write("Line 1\nDifferent Line 2\n")
        self.p4.run_sync(textFile)

        # Test with failing merge tool
        import tempfile
        import stat
        
        # Create a fake merge tool that always fails
        failing_merge_script = os.path.join(tempfile.gettempdir(), "failing_merge.sh")
        with open(failing_merge_script, "w") as f:
            f.write("#!/bin/bash\n >&2\nexit 1\n")
        os.chmod(failing_merge_script, stat.S_IRWXU)

        class MergeTestResolver(P4.Resolver):
            def __init__(self, testObject):
                self.t = testObject
                self.merge_result = None

            def resolve(self, mergeData):
                # Set P4MERGE to our failing script
                old_p4merge = os.environ.get('P4MERGE', '')
                os.environ['P4MERGE'] = failing_merge_script
                
                try:
                    # Call run_merge and verify it returns False when merge tool fails
                    self.merge_result = mergeData.run_merge()
                    
                    # Assert that run_merge() correctly detects merge tool failure
                    self.t.assertFalse(self.merge_result, 
                        f"run_merge() should return False when merge tool fails with exit code 1, but returned {self.merge_result}")
                    
                    # Additional assertion to verify the type
                    self.t.assertIsInstance(self.merge_result, bool, 
                        f"run_merge() should return a boolean, but returned {type(self.merge_result)}")
                        
                finally:
                    # Restore original P4MERGE
                    if old_p4merge:
                        os.environ['P4MERGE'] = old_p4merge
                    elif 'P4MERGE' in os.environ:
                        del os.environ['P4MERGE']
                
                return "at"  # Accept theirs to complete the resolve

        resolver = MergeTestResolver(self)
        self.p4.run_resolve(resolver=resolver)
        
        # Clean up
        if os.path.exists(failing_merge_script):
            os.unlink(failing_merge_script)

    def testProperty(self):
        self.p4.connect()
        self.assertTrue(self.p4.connected(), "Not connected")

        # AC-1: Set a property and verify the confirmation message
        result = self.p4.run('property', '-a', '-n', 'TestProp', '-v', 'TestValue')
        self.assertTrue(len(self.p4.messages) > 0, "Expected confirmation message after setting property")
        found_set_message = False
        for msg in self.p4.messages:
            if 'TestProp' in str(msg):
                found_set_message = True
                break
        self.assertTrue(found_set_message, "Expected message confirming property was set")

        # AC-2: List the property and verify the returned dict structure
        result = self.p4.run('property', '-l', '-n', 'TestProp')
        self.assertTrue(isinstance(result, list), "property -l should return a list")
        self.assertTrue(len(result) > 0, "property -l should return at least one dict")
        prop_dict = None
        for item in result:
            if isinstance(item, dict) and item.get('name') == 'TestProp':
                prop_dict = item
                break
        self.assertIsNotNone(prop_dict, "Expected to find property dict with name 'TestProp'")
        self.assertEqual(prop_dict['name'], 'TestProp', "Property name should be 'TestProp'")
        self.assertEqual(prop_dict['value'], 'TestValue', "Property value should be 'TestValue'")

        # AC-3: Delete the property and verify it no longer appears in the listing
        self.p4.run('property', '-d', '-n', 'TestProp')
        result = self.p4.run('property', '-l', '-n', 'TestProp')
        found_deleted = False
        for item in result:
            if isinstance(item, dict) and item.get('name') == 'TestProp':
                found_deleted = True
                break
        self.assertFalse(found_deleted, "Property should no longer appear after deletion")

        # AC-4: Verify exception is raised when -v is missing
        original_level = self.p4.exception_level
        self.p4.exception_level = P4.P4.RAISE_ERRORS
        with self.assertRaises(P4.P4Exception):
            self.p4.run('property', '-a', '-n', 'TestProp')
        self.p4.exception_level = original_level

        self.p4.disconnect()

    def testCallbackExceptions(self):
        """
        Test exception propagation from Python callbacks (P4PYTHON-373).
        Verifies that exceptions raised in OutputHandler, Resolver, and Progress
        callbacks propagate to the caller instead of being swallowed or causing segfaults.
        """
        self.p4.connect()
        self.assertTrue(self.p4.connected(), "Not connected")

        # Set up client for file operations
        client_spec = self.p4.fetch_client()
        client_spec['Root'] = self.client_root
        self.p4.save_client(client_spec)
        self.p4.client = client_spec['Client']

        # AC-1 & AC-2: OutputHandler callbacks (outputStat, outputText) raising
        # should propagate the original exception type (not SystemError)
        class ThrowingOutputHandler(P4.OutputHandler):
            def outputStat(self, stat):
                raise RuntimeError('boom from outputStat')

        handler = ThrowingOutputHandler()
        self.p4.handler = handler
        with self.assertRaises(RuntimeError) as cm:
            self.p4.run('info')
        self.assertEqual(str(cm.exception), 'boom from outputStat')
        self.p4.handler = None

        # Verify connection is still usable
        result = self.p4.run('info')
        self.assertTrue(len(result) > 0, "Connection should remain usable after callback exception")

        # OutputHandler.outputText raising should propagate the exception
        test_file = os.path.join(self.client_root, 'callback_test.txt')
        with open(test_file, 'w') as f:
            f.write('test content\n')

        self.p4.run('add', test_file)
        self.p4.run('submit', '-d', 'initial')

        class ThrowingTextHandler(P4.OutputHandler):
            def outputText(self, text):
                raise ValueError('boom from outputText')

        handler = ThrowingTextHandler()
        self.p4.handler = handler
        with self.assertRaises(ValueError) as cm:
            self.p4.run('print', test_file)
        self.assertEqual(str(cm.exception), 'boom from outputText')
        self.p4.handler = None

        # Verify connection is still usable
        result = self.p4.run('info')
        self.assertTrue(len(result) > 0, "Connection should remain usable after callback exception")

        # AC-1: Resolver.resolve raising should propagate (no segfault on Linux)
        class ThrowingResolver(P4.Resolver):
            def resolve(self, mergeData):
                raise OSError('boom from resolve')

        # Create two versions of a file to integrate
        test_file2 = os.path.join(self.client_root, 'resolve_test.txt')
        with open(test_file2, 'w') as f:
            f.write('line1\n')
        self.p4.run('add', test_file2)
        self.p4.run('submit', '-d', 'add resolve test')

        # Edit it
        self.p4.run('edit', test_file2)
        with open(test_file2, 'w') as f:
            f.write('line1\nline2\n')
        self.p4.run('submit', '-d', 'edit resolve test')

        # Copy it with a different name
        test_file3 = os.path.join(self.client_root, 'resolve_target.txt')
        with open(test_file3, 'w') as f:
            f.write('line1\n')
        self.p4.run('add', test_file3)
        self.p4.run('submit', '-d', 'add target')

        # Integrate latest version to the target
        self.p4.run('integ', '//depot/resolve_test.txt#2', '//depot/resolve_target.txt')

        resolver = ThrowingResolver()
        self.p4.resolver = resolver
        with self.assertRaises(OSError) as cm:
            self.p4.run('resolve')
        self.assertEqual(str(cm.exception), 'boom from resolve')
        self.p4.resolver = None

        # Clean up
        self.p4.run('revert', '//...')

        # AC-4: Verify connection remains usable after callback exception
        result = self.p4.run('info')
        self.assertTrue(len(result) > 0, "Connection should remain usable after callback exception")

        # Note: Progress callback exception handling is implemented in PythonClientProgress.cpp
        # (init, setDescription, setTotal, update, done all capture exceptions via PyErr_Fetch
        # and SetPendingException). Testing Progress callbacks requires operations that invoke
        # progress reporting, which may not be reliably triggered in all test environments.
        # The C++ implementation follows the same pattern as OutputHandler and Resolver.

        self.p4.disconnect()

    # ------------------------------------------------------------------
    # P4PYTHON-617: coverage-raising tests for the pure-Python P4.py layer.
    #
    # Group A - standalone unit tests (no server required).
    # ------------------------------------------------------------------

    def testExceptionStringFormats(self):
        """Drive every branch of P4Exception.__str__/__repr__ and
        P4MessageProxy.__str__/__repr__ by constructing the objects directly.

        Scope: this test validates the pure-Python *unpacking* logic only, by
        hand-constructing the value tuple. The C-layer contract (that the
        extension actually raises P4Exception with this same tuple structure,
        and that e.severity / e.generic / e.fmt come out correct from a live
        server error) is covered separately by testExceptionMessages, which
        triggers a real server warning and asserts those same attributes."""

        # 4-element form with a real error list, fmt supplied as a list.
        # Only this branch (one carrying messages) populates fmt / fmt_args.
        e_err = P4.P4Exception(("top error", ["error one"], [],
                               [{"severity": 3, "generic": 4, "msgid": 17,
                                 "msg_dict": {"fmt": ["error one fmt"],
                                              "code": "123", "extra": "y"},
                                 "msg_str": "error one"}]))
        self.assertEqual(str(e_err), "error one", "errors-list branch of __str__")
        self.assertEqual(e_err.severity, 3, "top severity not picked up")
        self.assertEqual(e_err.generic, P4.P4Exception.Generic.ILLEGAL,
                         "generic not mapped to enum")
        self.assertEqual(e_err.msgid, 17, "msgid not picked up")
        self.assertEqual(e_err.fmt, "error one fmt", "fmt list not unpacked to first element")
        self.assertEqual(e_err.fmt_args, {"extra": "y"},
                         "fmt_args must exclude 'code' and 'fmt'")
        self.assertIn("P4Exception", repr(e_err), "class name missing from repr")
        self.assertIn("error one", repr(e_err), "message missing from repr")

        # warnings-only branch (errors come back empty, warnings populated).
        # With no messages, _set_shortcut_attrs leaves fmt/fmt_args empty.
        e_warn = P4.P4Exception(("top warn", [], ["warn one"], []))
        self.assertEqual(str(e_warn), "warn one", "warnings-list branch of __str__")
        self.assertEqual(e_warn.fmt, "", "no-message branch must leave fmt empty")
        self.assertEqual(e_warn.fmt_args, {}, "no-message branch must leave fmt_args empty")

        # plain (non list/tuple) value -> errors and warnings are None, and the
        # no-message branch again leaves fmt/fmt_args empty.
        e_plain = P4.P4Exception("plain error")
        self.assertIsNone(e_plain.errors, "plain value must leave errors None")
        self.assertIsNone(e_plain.warnings, "plain value must leave warnings None")
        self.assertEqual(str(e_plain), "plain error", "value branch of __str__")
        self.assertEqual(e_plain.fmt, "", "plain value must leave fmt empty")
        self.assertEqual(e_plain.fmt_args, {}, "plain value must leave fmt_args empty")

        # errors set to a bare (non-list) string
        e_str_err = P4.P4Exception("x")
        e_str_err.errors = "single error"
        e_str_err.warnings = None
        self.assertEqual(str(e_str_err), "single error", "non-list errors branch")

        # warnings set to a bare (non-list) string
        e_str_warn = P4.P4Exception("x")
        e_str_warn.errors = None
        e_str_warn.warnings = "single warning"
        self.assertEqual(str(e_str_warn), "single warning", "non-list warnings branch")

        # final fall-through: empty (but not None) errors/warnings, list value
        e_fall = P4.P4Exception("x")
        e_fall.errors = []
        e_fall.warnings = []
        e_fall.value = ["[tag123] hello world"]
        self.assertIn("hello world", str(e_fall), "tagged message text must survive")
        self.assertNotIn("tag123", str(e_fall), "bracketed tag prefix must be stripped")

        # scalar value fall-through: empty (non-None) errors/warnings, plain value
        e_scalar = P4.P4Exception("x")
        e_scalar.errors = []
        e_scalar.warnings = []
        e_scalar.value = "plain scalar value"
        self.assertEqual(str(e_scalar), "plain scalar value",
                         "scalar value fall-through branch of __str__")

        # P4MessageProxy direct
        proxy = P4.P4MessageProxy(severity=2, generic=17, msgid=123,
                                  msg_dict={}, msg_str="a message")
        self.assertEqual(str(proxy), "a message", "proxy __str__ must return the message")
        self.assertEqual(proxy.dict, {}, "proxy dict not stored")
        proxy_repr = repr(proxy)
        self.assertIn("msgid=123", proxy_repr, "proxy repr missing msgid")
        self.assertIn("severity=2", proxy_repr, "proxy repr missing severity")

    def testMapStringAndReverse(self):
        """Exercise P4.Map.__str__, is_empty, reverse and the insert overloads."""
        m = P4.Map()
        self.assertTrue(m.is_empty(), "Fresh map must be empty")

        m.insert("//depot/main/... //ws/...")
        self.assertFalse(m.is_empty(), "Map must not be empty after insert")
        self.assertTrue(m.includes("//depot/main/foo"), "Map should include lhs path")

        s = str(m)
        self.assertIn("//depot/main/... //ws/...", s, "__str__ missing mapping line")
        self.assertTrue(s.endswith("\n"), "__str__ must terminate each line with newline")

        r = m.reverse()
        self.assertIsInstance(r, P4.Map, "reverse() must return a P4.Map")
        self.assertEqual(r.as_array(), ["//ws/... //depot/main/..."],
                         "reverse() did not swap lhs/rhs")

        # two-string (pair) insert form
        pair = P4.Map()
        pair.insert("//a/...", "//b/...")
        self.assertEqual(pair.count(), 1, "Pair insert did not add an entry")
        self.assertTrue(pair.includes("//a/foo"), "Pair insert mapping incorrect")

        # list insert form
        lst = P4.Map()
        lst.insert(["//x/... //y/...", "//p/... //q/..."])
        self.assertEqual(lst.count(), 2, "List insert did not add two entries")

    def testKeepAlive(self):
        """Exercise PyKeepAlive.isAlive, __call__ and the polling-thread path."""
        ka = P4.PyKeepAlive()
        self.assertEqual(ka.isAlive(), 1, "Fresh keep-alive must report alive")

        # First call creates and starts the daemon polling thread
        self.assertEqual(ka(), 1, "__call__ must return the alive flag")
        # Second call hits the 'thread already running' branch
        self.assertEqual(ka(), 1, "__call__ must stay alive while polling thread runs")
        self.assertEqual(ka.isAlive(), 1, "Keep-alive should still be alive")

    def testOutputHandlerClasses(self):
        """Verify OutputHandler constants and default REPORT return values."""
        self.assertEqual(P4.OutputHandler.REPORT, 0, "REPORT constant changed")
        self.assertEqual(P4.OutputHandler.HANDLED, 1, "HANDLED constant changed")
        self.assertEqual(P4.OutputHandler.CANCEL, 2, "CANCEL constant changed")

        h = P4.OutputHandler()
        self.assertEqual(h.outputText("t"), P4.OutputHandler.REPORT, "outputText default")
        self.assertEqual(h.outputBinary(b"b"), P4.OutputHandler.REPORT, "outputBinary default")
        self.assertEqual(h.outputStat({}), P4.OutputHandler.REPORT, "outputStat default")
        self.assertEqual(h.outputInfo({}), P4.OutputHandler.REPORT, "outputInfo default")
        self.assertEqual(h.outputMessage("m"), P4.OutputHandler.REPORT, "outputMessage default")

        f = P4.FilelogOutputHandler()
        self.assertEqual(f.outputFilelog(None), P4.OutputHandler.REPORT,
                         "FilelogOutputHandler.outputFilelog default")

        # ReportHandler is the printing OutputHandler subclass; every method
        # reports HANDLED. Its methods print() to stdout by design (it's a
        # console-report handler) -- redirect that output so it doesn't leak
        # into the test runner's console, where CI log scanners can mistake
        # the hardcoded "error:"/"stat:" print labels for real failures.
        rh = P4.ReportHandler()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(rh.outputText("t"), P4.OutputHandler.HANDLED, "ReportHandler.outputText")
            self.assertEqual(rh.outputBinary(b"b"), P4.OutputHandler.HANDLED, "ReportHandler.outputBinary")
            self.assertEqual(rh.outputStat({}), P4.OutputHandler.HANDLED, "ReportHandler.outputStat")
            self.assertEqual(rh.outputInfo({}), P4.OutputHandler.HANDLED, "ReportHandler.outputInfo")
            self.assertEqual(rh.outputMessage("m"), P4.OutputHandler.HANDLED, "ReportHandler.outputMessage")

    def testProgressClasses(self):
        """Verify Progress TYPE_*/UNIT_* constants and base method state-keeping."""
        self.assertEqual(P4.Progress.TYPE_SENDFILE, 1, "TYPE_SENDFILE changed")
        self.assertEqual(P4.Progress.TYPE_RECEIVEFILE, 2, "TYPE_RECEIVEFILE changed")
        self.assertEqual(P4.Progress.TYPE_TRANSFER, 3, "TYPE_TRANSFER changed")
        self.assertEqual(P4.Progress.TYPE_COMPUTATION, 4, "TYPE_COMPUTATION changed")
        self.assertEqual(P4.Progress.UNIT_PERCENT, 1, "UNIT_PERCENT changed")
        self.assertEqual(P4.Progress.UNIT_FILES, 2, "UNIT_FILES changed")
        self.assertEqual(P4.Progress.UNIT_KBYTES, 3, "UNIT_KBYTES changed")
        self.assertEqual(P4.Progress.UNIT_MBYTES, 4, "UNIT_MBYTES changed")

        p = P4.Progress()
        p.init(P4.Progress.TYPE_SENDFILE)
        self.assertEqual(p.type, P4.Progress.TYPE_SENDFILE, "init did not store type")
        p.setDescription("uploading", P4.Progress.UNIT_FILES)
        self.assertEqual(p.description, "uploading", "setDescription did not store description")
        self.assertEqual(p.units, P4.Progress.UNIT_FILES, "setDescription did not store units")
        p.setTotal(100)
        self.assertEqual(p.total, 100, "setTotal did not store total")
        p.update(42)
        self.assertEqual(p.position, 42, "update did not store position")
        self.assertIsNone(p.done(0), "done() base implementation should return None")

        # TextProgress is the printing Progress subclass; verify it still
        # records the same state via the base class. Its methods print() to
        # stdout by design -- redirect that output for the same reason as
        # ReportHandler above.
        tp = P4.TextProgress()
        with contextlib.redirect_stdout(io.StringIO()):
            tp.init(P4.Progress.TYPE_RECEIVEFILE)
            self.assertEqual(tp.type, P4.Progress.TYPE_RECEIVEFILE, "TextProgress.init")
            tp.setDescription("syncing", P4.Progress.UNIT_FILES)
            self.assertEqual(tp.description, "syncing", "TextProgress.setDescription description")
            self.assertEqual(tp.units, P4.Progress.UNIT_FILES, "TextProgress.setDescription units")
            tp.setTotal(10)
            self.assertEqual(tp.total, 10, "TextProgress.setTotal")
            tp.update(5)
            self.assertEqual(tp.position, 5, "TextProgress.update")
            self.assertIsNone(tp.done(0), "TextProgress.done")

    def testResolverDefault(self):
        """Exercise the default Resolver.resolve / actionResolve decision logic.

        Scope: this is a pure-Python unit test of the decision logic in
        isolation (using a FakeMerge stub). The C-layer contract -- that
        run_resolve() actually instantiates and invokes the default Resolver --
        is covered by the pre-existing integration tests testResolve,
        testMergeToolReturnCode and testCallbackExceptions, which drive
        run_resolve() against a live server."""
        class FakeMerge:
            def __init__(self, hint):
                self.merge_hint = hint

        r = P4.Resolver()
        # 'e' (conflict) is special-cased to skip the resolve; this branch
        # prints to stdout by design, so redirect it for the same reason as
        # ReportHandler/TextProgress above.
        with contextlib.redirect_stdout(io.StringIO()):
            conflict_result = r.resolve(FakeMerge("e"))
        self.assertEqual(conflict_result, "s",
                         "Default resolver must skip on merge conflict")
        # any other hint is passed straight through
        self.assertEqual(r.resolve(FakeMerge("at")), "at",
                         "Default resolver must pass the hint through")
        self.assertEqual(r.actionResolve(FakeMerge("am")), "am",
                         "Default actionResolve must return the hint")

    def testIdentifyAndRepr(self):
        """Cover P4.identify() and both branches of P4.__repr__."""
        ident = P4.P4.identify()
        self.assertIsInstance(ident, str, "identify() must return a string")
        self.assertTrue(any(ch.isdigit() for ch in ident),
                        "identify() string should contain a version number")

        # disconnected repr
        p4 = P4.P4()
        p4.user = "bob"
        p4.client = "ws"
        p4.port = "myport:1666"
        rep = repr(p4)
        self.assertTrue(rep.rstrip().endswith("disconnected"),
                        "Disconnected repr must end with 'disconnected': %s" % rep)
        self.assertIn("bob", rep, "repr missing user")
        self.assertIn("ws", rep, "repr missing client")
        self.assertIn("myport:1666", rep, "repr missing port")

        # connected repr
        self.p4.connect()
        rep_c = repr(self.p4).rstrip()
        self.assertTrue(rep_c.endswith("connected"), "Connected repr must end with 'connected'")
        self.assertFalse(rep_c.endswith("disconnected"),
                         "Connected repr must not report disconnected")
        self.p4.disconnect()

    # ------------------------------------------------------------------
    # Group B - integration tests (require the RSH p4d harness).
    # ------------------------------------------------------------------

    def testDepotFileFormatting(self):
        """Cover DepotFile/Revision/Integration __str__/__repr__ and the
        each_* iterators via run_filelog output."""
        self.p4.connect()
        self._setClient()

        testDir = 'test_depotfmt'
        files = self.createFiles(testDir)

        change = self.p4.fetch_change()
        change._description = "Depot formatting add"
        self._doSubmit("Failed to submit the add", change)

        # produce an integration record so str_integration is exercised
        self.p4.run_integ(testDir + '/...', 'branch_depotfmt/...')
        change = self.p4.fetch_change()
        change._description = "Depot formatting branch"
        self._doSubmit("Failed to submit branch", change)

        filelogs = self.p4.run_filelog(testDir + '/...')
        self.assertEqual(len(filelogs), len(files), "Unexpected number of filelog entries")

        df = filelogs[0]
        self.assertIsInstance(df, P4.DepotFile, "run_filelog must yield DepotFile objects")

        text = str(df)
        self.assertIn(df.depotFile, text, "DepotFile.__str__ missing depot path")
        self.assertIn("change", text, "DepotFile.__str__ missing revision detail")

        self.assertIn("DepotFile", repr(df), "DepotFile.__repr__ missing class name")

        revs = list(df.each_revision())
        self.assertEqual(len(revs), len(df.revisions), "each_revision yielded wrong count")

        rev = df.revisions[0]
        self.assertIn("Revision", repr(rev), "Revision.__repr__ missing class name")
        self.assertGreater(len(rev.integrations), 0, "Expected at least one integration")

        integ = rev.integrations[0]
        self.assertIn("Integration", repr(integ), "Integration.__repr__ missing class name")
        integs = list(rev.each_integration())
        self.assertEqual(len(integs), len(rev.integrations),
                         "each_integration yielded wrong count")
        self.assertIn(integ.how, text, "str_integration line missing from DepotFile.__str__")

        # run_filelog with an explicit logger exercises its dedicated debug path
        import logging
        try:
            from StringIO import StringIO
        except ImportError:
            from io import StringIO
        stream = StringIO()
        lg = logging.getLogger('TestDepotFmtFilelog')
        lg.handlers = []
        lg.addHandler(logging.StreamHandler(stream))
        lg.setLevel(logging.DEBUG)
        self.p4.run_filelog(testDir + '/...', logger=lg)
        self.assertIn("//depot/test_depotfmt", stream.getvalue(),
                      "run_filelog did not emit its formatted result to the logger")

    def testPrintContent(self):
        """Cover run_print() assembly of a text file's contents."""
        self.p4.connect()
        self._setClient()

        testDir = 'test_print'
        testAbsoluteDir = os.path.join(self.client_root, testDir)
        os.mkdir(testAbsoluteDir)

        content = "Hello\nWorld\n"
        fname = os.path.join(testAbsoluteDir, "text.txt")
        with open(fname, "w") as f:
            f.write(content)
        self.p4.run_add(testDir + "/text.txt")
        self.p4.run_submit('-d', 'print content test')

        result = self.p4.run_print('//depot/test_print/text.txt')
        self.assertIsInstance(result[0], dict, "First print element must be the stat dict")
        self.assertEqual(result[1], content,
                         "run_print did not reassemble the file content exactly")

        # run_print with an explicit logger exercises its dedicated debug path
        import logging
        try:
            from StringIO import StringIO
        except ImportError:
            from io import StringIO
        stream = StringIO()
        lg = logging.getLogger('TestPrintLogger')
        lg.handlers = []
        lg.addHandler(logging.StreamHandler(stream))
        lg.setLevel(logging.DEBUG)
        logged = self.p4.run_print('//depot/test_print/text.txt', logger=lg)
        self.assertEqual(logged[1], content, "run_print with logger lost the content")
        self.assertIn("//depot/test_print/text.txt", stream.getvalue(),
                      "run_print logger output did not reference the printed depot path")

    def testRunPrintBinaryAndEmpty(self):
        """Cover run_print() empty-file ('') and binary (b''.join) branches."""
        self.p4.connect()
        self._setClient()

        testDir = 'test_print_be'
        testAbsoluteDir = os.path.join(self.client_root, testDir)
        os.mkdir(testAbsoluteDir)

        # empty text file
        empty_name = os.path.join(testAbsoluteDir, "empty.txt")
        with open(empty_name, "w") as f:
            pass
        self.p4.run_add(testDir + "/empty.txt")

        # binary file
        binary_content = bytes(range(8))
        bin_name = os.path.join(testAbsoluteDir, "data.bin")
        with open(bin_name, "wb") as f:
            f.write(binary_content)
        self.p4.run_add('-t', 'binary', testDir + "/data.bin")

        self.p4.run_submit('-d', 'print binary and empty test')

        empty_result = self.p4.run_print('//depot/test_print_be/empty.txt')
        self.assertIsInstance(empty_result[0], dict, "Empty print missing stat dict")
        self.assertEqual(empty_result[1], "",
                         "run_print on an empty file must yield an empty string")

        bin_result = self.p4.run_print('//depot/test_print_be/data.bin')
        self.assertIsInstance(bin_result[0], dict, "Binary print missing stat dict")
        self.assertIsInstance(bin_result[1], bytes, "Binary content must be bytes")
        self.assertEqual(bin_result[1], binary_content,
                         "run_print did not reassemble binary content with b''.join")

    def testFilelogOutputHandler(self):
        """Cover FilelogOutputHandler.outputStat -> processFilelog -> outputFilelog."""
        self.p4.connect()
        self._setClient()

        testDir = 'test_filelog_handler'
        files = self.createFiles(testDir)

        change = self.p4.fetch_change()
        change._description = "Filelog handler test"
        self._doSubmit("Failed to submit the add", change)

        class CapturingFilelogHandler(P4.FilelogOutputHandler):
            def __init__(self):
                P4.FilelogOutputHandler.__init__(self)
                self.depotFiles = []

            def outputFilelog(self, df):
                self.depotFiles.append(df)
                return P4.OutputHandler.HANDLED

        handler = CapturingFilelogHandler()
        self.p4.run_filelog(testDir + '/...', handler=handler)

        self.assertEqual(len(handler.depotFiles), len(files),
                         "Handler did not receive one DepotFile per file")
        self.assertTrue(all(isinstance(df, P4.DepotFile) for df in handler.depotFiles),
                        "outputFilelog must receive DepotFile objects")

    def testRunShelveWithSpecAndDelete(self):
        """Cover run_shelve() dict branch and delete_shelve() -c/-d handling."""
        self.p4.connect()
        self._setClient()
        self.assertEqual(len(self.p4.run_opened()), 0, "Shouldn't have open files")

        if self.p4.server_level >= 28:
            testDir = 'test_shelve_spec'
            files = self.createFiles(testDir)

            change = self.p4.fetch_change()
            change._description = "Shelve spec test"

            # passing the change spec (a dict subclass) exercises the -i branch
            shelved = self.p4.run_shelve(change)
            c = None
            for r in shelved:
                if isinstance(r, dict) and 'change' in r:
                    c = r['change']
                    break
            self.assertIsNotNone(c, "run_shelve(spec) did not report a change number")

            self.p4.run_revert('...')
            self.assertEqual(len(self.p4.run_opened()), 0, "Files still open after revert")

            # delete_shelve must prepend -c and -d
            self.p4.delete_shelve(c)
            shelved_changes = self.p4.run('changes', '-s', 'shelved')
            self.assertFalse(any(sc.get('change') == c for sc in shelved_changes),
                             "Shelve was not deleted")
        else:
            print("Need Perforce Server 2009.2 or greater to test shelving")

    def testSpecShortcutsAndErrors(self):
        """Cover the dynamic fetch_/save_/delete_/parse_/format_ shortcuts plus
        the iterate_ unknown-spec error and __getattr__ AttributeError path."""
        self.p4.connect()

        # fetch_ (-o) and save_ (-i)
        client = self.p4.fetch_client()
        self.assertIsInstance(client, P4.Spec, "fetch_client must return a Spec")
        client._root = self.client_root
        client._description = "Shortcut test\n"
        self.p4.save_client(client)

        # format_ then parse_ round-trip
        form = self.p4.format_client(client)
        self.assertIsInstance(form, str, "format_client must return a string")
        reparsed = self.p4.parse_client(form)
        self.assertIsInstance(reparsed, P4.Spec, "parse_client must return a Spec")
        self.assertEqual(reparsed._root, client._root,
                         "Round-tripped spec lost the Root field")

        # the reparsed spec carries a comment block, so re-formatting it
        # exercises the comment-prepending branch of format_*
        self.assertIn('comment', reparsed.__dict__, "parse_ did not attach a comment block")
        form2 = self.p4.format_client(reparsed)
        self.assertIsInstance(form2, str, "format_client must return a string")
        self.assertIn("Root:", form2, "Re-formatted spec lost its fields")

        # run_init / run_clone are deliberately disabled in favour of P4.init/clone
        self.assertRaises(Exception, self.p4.run_init)
        self.assertRaises(Exception, self.p4.run_clone)

        # delete_ shortcut on a throwaway client
        throwaway = self.p4.fetch_client('shortcut_delete_me')
        throwaway._root = self.client_root
        self.p4.save_client(throwaway)
        self.assertIn('shortcut_delete_me',
                      [c['client'] for c in self.p4.run_clients()],
                      "Throwaway client was not created")
        self.p4.delete_client('shortcut_delete_me')
        self.assertNotIn('shortcut_delete_me',
                         [c['client'] for c in self.p4.run_clients()],
                         "delete_client shortcut did not remove the client")

        # iterate_ over an unknown spec list raises
        self.assertRaises(Exception, self.p4.iterate_this_is_not_a_real_spec)

        # __getattr__ on a non-prefixed name raises AttributeError
        with self.assertRaises(AttributeError):
            self.p4.totally_unknown_attribute

    def testSpecValidation(self):
        """Cover Spec.__setitem__ validation, case-insensitive keys and
        permitted_fields()."""
        self.p4.connect()
        client = self.p4.fetch_client()

        self.assertIsNotNone(client.permitted_fields(),
                             "permitted_fields() must expose the field map")

        # non-str / non-list value is rejected
        self.assertRaises(P4.P4Exception, client.__setitem__, 'Description', 123)

        # lower-case key is normalised to the canonical field name
        client['description'] = "Case-insensitive key\n"
        self.assertIn('Description', client,
                      "Lower-case key was not normalised to canonical 'Description'")
        self.assertEqual(client['Description'], "Case-insensitive key\n",
                         "Normalised key stored the wrong value")

        # an unknown field is rejected
        self.assertRaises(P4.P4Exception, client.__setitem__, 'NoSuchField', 'x')

    def testSpecAttributeAccess(self):
        """Cover Spec.__getattr__/__setattr__ underscore syntax, the 'comment'
        special case and AttributeError for non-underscore names."""
        self.p4.connect()
        client = self.p4.fetch_client()

        # read via _attribute shorthand
        self.assertEqual(client._root, client['Root'],
                         "_root shorthand did not return the Root field")

        # write via _attribute shorthand (normalises through __setitem__)
        client._description = "Attribute access test\n"
        self.assertEqual(client['Description'], "Attribute access test\n",
                         "_description shorthand did not set the Description field")

        # reading a non-underscore attribute raises AttributeError
        with self.assertRaises(AttributeError):
            client.notunderscored

        # assigning a non-underscore attribute raises AttributeError
        def _assign_bad():
            client.notunderscored = "x"
        self.assertRaises(AttributeError, _assign_bad)

        # the 'comment' attribute is stored verbatim on __dict__
        client.comment = "# a comment"
        self.assertEqual(client.__dict__['comment'], "# a comment",
                         "comment attribute was not stored on __dict__")

    def testContextManagers(self):
        """Cover while_tagged, at_exception_level, using_handler, saved_context
        (with exception) and the __enter__/__exit__ protocol."""
        self.p4.connect()
        self._setClient()

        old_tagged = self.p4.tagged
        with self.p4.while_tagged(False):
            self.assertFalse(self.p4.tagged, "while_tagged did not change tagged mode")
        self.assertEqual(self.p4.tagged, old_tagged, "while_tagged did not restore tagged")

        old_level = self.p4.exception_level
        with self.p4.at_exception_level(P4.P4.RAISE_NONE):
            self.assertEqual(self.p4.exception_level, P4.P4.RAISE_NONE,
                             "at_exception_level did not change the level")
        self.assertEqual(self.p4.exception_level, old_level,
                         "at_exception_level did not restore the level")

        handler = P4.OutputHandler()
        with self.p4.using_handler(handler):
            self.assertEqual(self.p4.handler, handler, "using_handler did not set the handler")
        self.assertIsNone(self.p4.handler, "using_handler did not restore the handler")

        # saved_context must restore even when the block raises
        cwd = self.p4.cwd
        try:
            with self.p4.saved_context(cwd='/tmp'):
                self.assertEqual(self.p4.cwd, '/tmp', "saved_context did not apply override")
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        self.assertEqual(self.p4.cwd, cwd, "saved_context did not restore cwd after exception")

        # context-manager protocol disconnects on exit
        with P4.P4() as p4b:
            p4b.port = self.port
            p4b.user = self.p4.user
            p4b.password = self.p4.password
            p4b.connect()
            self.assertTrue(p4b.connected(), "P4 context manager did not connect")
        self.assertFalse(p4b.connected(), "__exit__ did not disconnect")

    def testEncodingModes(self):
        """Cover the run() encoding branch for utf-8 and raw modes."""
        self.p4.connect()

        # utf-8 mode: str arguments are encoded to bytes before being passed down
        self.p4.encoding = 'utf-8'
        self.assertEqual(self.p4.encoding, 'utf-8', "encoding attribute not set to utf-8")
        info = self.p4.run_info()
        self.assertIsInstance(info, list, "run_info() must still return a list under utf-8")

        # raw mode: the encoding step is skipped and values come back as bytes
        self.p4.encoding = 'raw'
        self.assertEqual(self.p4.encoding, 'raw', "encoding attribute not set to raw")
        info_raw = self.p4.run_info()[0]
        self.assertEqual(type(info_raw['serverVersion']), bytes,
                         "raw encoding must return bytes values")

        # back under utf-8, a non-str (bytes) argument must be passed through
        # the encoding step untouched
        self.p4.encoding = 'utf-8'
        changes = self.p4.run('changes', b'-m1')
        self.assertIsInstance(changes, list,
                              "bytes argument under utf-8 encoding was not handled")

    def testLogMessages(self):
        """Cover the run() logger integration: info logging on success and the
        exception path that logs then re-raises."""
        import logging
        try:
            from StringIO import StringIO
        except ImportError:
            from io import StringIO

        self.p4.connect()

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.formatter = logging.Formatter('%(levelname)s:%(message)s')
        logger = logging.getLogger('TestLogMessages')
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        self.p4.logger = logger

        # a successful command logs the command line at INFO
        self.p4.run_info()
        self.assertIn("INFO:p4 info", stream.getvalue(),
                      "Successful command did not log at INFO")

        # a failing command must log via the except path and still raise
        stream.truncate(0)
        stream.seek(0)
        self.p4.exception_level = P4.P4.RAISE_ALL
        self.assertRaises(P4Exception, self.p4.run_files, '//depot/does_not_exist')
        self.assertIn("WARNING:", stream.getvalue(),
                      "Exception path did not log the warning before re-raising")

        self.p4.logger = None

    def testLoggerSeverityLevels(self):
        """Cover log_messages() mapping of severities 1/2/3 to info/warning/error
        and the silent skip of any other severity."""
        import logging
        try:
            from StringIO import StringIO
        except ImportError:
            from io import StringIO

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.formatter = logging.Formatter('%(levelname)s:%(message)s')
        logger = logging.getLogger('TestLoggerSeverityLevels')
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        class FakeMessage:
            def __init__(self, severity, text):
                self.severity = severity
                self._text = text

            def __str__(self):
                return self._text

        # duck-typed stand-in carrying the two attributes log_messages reads
        class Holder:
            pass

        holder = Holder()
        holder.logger = logger
        holder.messages = [
            FakeMessage(1, "info msg"),
            FakeMessage(2, "warn msg"),
            FakeMessage(3, "error msg"),
            FakeMessage(0, "ignored empty"),
            FakeMessage(4, "ignored fatal"),
        ]

        self.assertTrue(hasattr(P4.P4, 'log_messages'),
                        "P4.P4.log_messages is missing — log_messages() was removed or renamed")
        P4.P4.log_messages(holder)
        out = stream.getvalue()
        self.assertIn("INFO:info msg", out, "Severity 1 did not map to info")
        self.assertIn("WARNING:warn msg", out, "Severity 2 did not map to warning")
        self.assertIn("ERROR:error msg", out, "Severity 3 did not map to error")
        self.assertNotIn("ignored empty", out, "Severity 0 should be skipped")
        self.assertNotIn("ignored fatal", out, "Severity 4 should be skipped")


if __name__ == '__main__':
    unittest.main()

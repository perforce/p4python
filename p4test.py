# -*- encoding: UTF8 -*-

from __future__ import print_function

import glob, sys, time, stat, platform, os
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

def onRmTreeError( function, path, exc_info ):
    os.chmod( path, stat.S_IWRITE)
    os.remove( path )

class TestP4Python(unittest.TestCase):

    def setUp(self):
        self.setDirectories()
        self.p4d = "p4d"
        self.port = "rsh:%s -r \"%s\" -L log -vserver=3 -i" % ( self.p4d, self.server_root )
        self.p4 = P4.P4()
        self.p4.port = self.port

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
        password = "Password"
        self.p4.ticket_file = ticketFile
        self.assertEqual( self.p4.ticket_file, ticketFile, "Ticket file not set correctly")

        self.p4.connect()
        client = self.p4.fetch_client()
        client._root = self.client_root
        self.p4.save_client(client)

        try:
            self.p4.run_password( "", password )
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
            self.assertEqual( e.value, 'Password invalid.')

        try:
            self.p4.run_password( password, "" )
        except P4.P4Exception:
            self.fail( "Failed to reset the password" )

        self.assertTrue( os.path.exists(ticketFile), "Ticket file not found")

        tickets = self.p4.run_tickets()
        self.assertEqual(len(tickets), 1, "Expected only one ticket")
        self.assertEqual(len(tickets[0]), 3, "Expected exactly three entries in tickets")

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
                    self.t.assertEqual(mergeData.merge_action, "(text+wx)",
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
        self.assertEqual( sys.getrefcount(h), 2 )

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
        self.assertEqual( sys.getrefcount(h), 2 )
        self.p4.handler = h

        self.assertEqual( len(self.p4.run_files('...')), 0, "p4 does not return empty list")
        self.assertEqual( len(h.statOutput), len(files), "Less files than expected")
        self.assertEqual( len(h.messageOutput), 0, "Messages unexpected")
        self.p4.handler = None
        self.assertEqual( sys.getrefcount(h), 2 )

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



if __name__ == '__main__':
    unittest.main()

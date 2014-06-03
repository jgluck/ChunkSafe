#!/usr/bin/python
'''
chunksafe.py is our program you can call it with the following arguments
first node
<port to run on><backup dir><scratch dir><hours><min>
subject node
<port to run on><ip of bootstrap node><port of bootstrap node><backup dir><scratch dir><hours><min>

resume
<port to run on (must be the same)>

sorry
'''
# The way this works at the moment:
# Ask some nodes to reserve space
# Pick the first one that confirms
# Cancel the reservation on all the other ones
# Tell the other node to get the file

import sys, socket, cPickle, datetime, signal, os
import time
from comm import ChunkSafeComm
from googlevoice import *
from chunks import Chunk, BackupDir
from server import ChunkServer
from chunkfile import ChunkFile
from twisted.internet import reactor, defer, threads
from entangled.kademlia import datastore

class ChunkSafeNode:
    def __init__(self, udpPort, backupDir=None, storeDir=None, backupTime=None, bootstrapAddr=None, bootstrapPort=None):
        # Set parameters
        self.commPort = udpPort
        self.address = socket.gethostbyname(socket.gethostname())
        if backupDir != None and storeDir != None:
            # New node - params specified on command line
            self.serverPort = udpPort + 500
            self.backupDir = backupDir
            self.storageDir = storeDir
            self.backupTime = backupTime
            print "Time: " + str(self.backupTime)
            self.saveParams()
        else:
            # Resuming node - load parameters
            try:
                self.loadParams()
            except IOError:
                print "Can't resume node, there is no saved state in this directory!"
                exit(1)

        # Create and store helper objects
        self.reactor = reactor
        dataStore = datastore.SQLiteDataStore(str(udpPort)+".db")
        self.comm = ChunkSafeComm(self.commPort, dataStore)
        self.backup = BackupDir(self.backupDir,self.storageDir)
        self.server = ChunkServer(self.serverPort, self.reactor, os.getcwd())

        # Connect to the Entangled network
        if bootstrapAddr != None and bootstrapPort != None:
            self.comm.joinNetwork([(bootstrapAddr,bootstrapPort)])
        else:
            self.comm.joinNetwork(None)
        
        # Schedule the backup
        self.reactor.callLater(self.secsToBackup(), self.backUp, None)

        def sigHandler(signum,frame):
            self.reactor.callLater(0,self.backUp,None)
        signal.signal(signal.SIGUSR1,sigHandler)

    # Save a dict of params to a pickle file
    def saveParams(self):
        params = {}
        params["storageDir"] = self.storageDir
        params["backupDir"] = self.backupDir
        params["serverPort"] = self.serverPort
        params["backupTime"] = self.backupTime
        paramFile = open(str(self.commPort)+".params","wb")
        cPickle.dump(params,paramFile)
        paramFile.close()

    # Load the parameters from a saved file
    def loadParams(self):
        paramFile = open(str(self.commPort)+".params","rb")
        params = cPickle.load(paramFile)
        paramFile.close()
        self.storageDir = params["storageDir"]
        self.backupDir = params["backupDir"]
        self.serverPort = params["serverPort"]
        self.backupTime = params["backupTime"]

    # Number of seconds before the backup
    def secsToBackup(self):
        backupTime = datetime.time(*self.backupTime)
        now = datetime.datetime.now()
        then = datetime.datetime.combine(now.date(), backupTime)
        diff = (then-now).seconds
        if diff == 0:
            diff = 3600*24
        print "Backing up in " + str(diff) + " seconds"
        return diff

    def backUp(self, result):
        #benchmark line
        timer = [0]

        #benchmark line
        def startTimer(result):
            timer[0] = time.time()
            return result

        #benchmark line
        def stopTimer(result):
            timer[0] = time.time() - timer[0]
            print "it took %f seconds to negotiate a partner\n" %(timer[0])
            return result

        chunkfile = [None]

        #archives the chunkfile
        def archiveItem(result,item,storageDir):
            chunkfile[0] = item.archive(storageDir)
            #print "archiveItem: " + str(chunkfile)
            return chunkfile[0]
        #tells server to prepare file
        def allowTheSend(result):
            #print "allowTheSend: " + str(chunkfile)
            self.server.allowSend(result,chunkfile[0])
            return result
        #schedule after tells teh server to schedule the following procedure after it sends the file
        def scheduleAfter(result, method):
            self.server.scheduleAfterSend(chunkfile[0].getName(), method)
            return result
        def send(result):
            df = self.comm.sendChunk(result,self.address,self.serverPort,chunkfile[0])
            return df
        def printDone(result):
            #benchmark line
            print "Done sending"

        #sends text msg of notification of the backup's completion
        def sendText(result):
            a = Voice()
            a.login("salvo.program","qwertyqwerty")
            a.send_sms(7327071629,"donebackup")

        # Schedule next backup
        self.reactor.callLater(self.secsToBackup(), self.backUp, None)

        self.backup.walkDir()
        backupDf = defer.Deferred()
        for item in self.backup.chunks():
            backupDf.addCallback(archiveItem,item,self.storageDir)
            backupDf.addCallback(startTimer)
            backupDf.addCallback(self.comm.findDestination)
            backupDf.addCallback(stopTimer)
            backupDf.addCallback(allowTheSend)
            backupDf.addCallback(scheduleAfter, item.dissolve)
            backupDf.addCallback(send)
        backupDf.addErrback(self.comm.printNum,"chunksafe36")
        backupDf.addCallback(sendText)
        backupDf.addCallback(printDone)
        #self.comm.storeHostContents(d.subdirs())
        backupDf.callback(None)

def usage():
    print sys.argv[0] + " <port> <bootstrap ip> <bootstrap port> <backup dir> <scratch dir> <backup time (HH MM)>"

if __name__ == "__main__":

    if len(sys.argv) == 6: # initial node
        print "Creating initial node"
        n = ChunkSafeNode(int(sys.argv[1]), sys.argv[2],sys.argv[3],(int(sys.argv[4]),int(sys.argv[5])))
    elif len(sys.argv) == 8: # subsequent node
        print "Creating node"
        n = ChunkSafeNode(int(sys.argv[1]),sys.argv[4],sys.argv[5], (int(sys.argv[6]),int(sys.argv[7])), sys.argv[2],int(sys.argv[3]),)
        #print "Registering callback"
        #n.comm._joinDeferred.addCallback(n.backUp)
    elif len(sys.argv) == 2: # restarting node
        print "Resuming node"
        n = ChunkSafeNode(int(sys.argv[1]))
    else:
        usage()
        exit(1)
    #reactor.callLater(60,reactor.stop)
    reactor.run()

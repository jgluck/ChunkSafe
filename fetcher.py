#!/usr/bin/python

# A client for our file server that will request and store a specified file

import sys
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientCreator
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred

class ChunkFetchProtocol(LineReceiver):
    def __init__(self):
        self.fileDf = Deferred()
        self.fp = None

    def getFile(self,fname):
        self.sendLine(fname)
        self.fp = open(fname,'wb')
        self.setRawMode()

    def rawDataReceived(self, data):
        self.fp.write(data)

    def connectionLost(self, reason):
        if self.fp != None:
            self.fp.close()
            self.fileDf.callback("Closed")
            # print "File received"

class ChunkFetcher(ClientCreator):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        ClientCreator.__init__(self, reactor, ChunkFetchProtocol)

    def connect(self):
        return self.connectTCP(self.address,self.port)

if __name__ == '__main__':
    def getTheFile(protocol, fname):
        protocol.getFile(fname)
        protocol.fileDf.addCallback(stopReactor)

    def stopReactor(result):
        reactor.stop()

    address = '127.0.0.1'
    port = 6000 #500 above the contact port from comm
    cf = ChunkFetcher(address, port)
    cf.connect().addCallback(getTheFile, sys.argv[1])
    reactor.run()

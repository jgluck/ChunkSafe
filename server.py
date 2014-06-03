#!/usr/bin/python

from chunkfile import ChunkFile
from twisted.internet.protocol import Protocol, Factory
from twisted.protocols.basic import FileSender, LineReceiver
from twisted.internet import reactor
from twisted.internet.defer import Deferred
import os

# Protocol that sends a requested file, but only from the approved directory or 
# if specifically approved by the node
class ChunkSender(LineReceiver):
    def lineReceived(self, line):
        name = line.strip()
        if name in self.factory.allowedList:
            f = self.factory.allowedList[name][0]
            df = self.factory.allowedList[name][1]
            # print "Sending " + name
            buf = f.read()
            self.transport.write(buf)
            f.close()
            df.callback("Closed")
            del self.factory.allowedList[name]
        else:
            try:
                # Sanitize input:
                name = os.path.join(self.factory.dirname,os.path.basename(name))
                # This is bad: for example, try sending "/etc/passwd" to the server
                #path = os.path.join(self.factory.dirname,name)
                f = ChunkFile(name)
                print "Sending " + name
                buf = f.read()
                self.transport.write(buf)
                f.close()
            except IOError:
                print "File " + name + " not found"
        self.transport.loseConnection()

class ChunkServer(Factory):
    def __init__(self, port, reactor, dirname = "."):
        self.port = port
        self.dirname = dirname
        self.protocol = ChunkSender
        self.allowedList = {}
        reactor.listenTCP(self.port, self)

    def allowSend(self, contact, chunkfile):
        df = Deferred()
        self.allowedList[chunkfile.getName()] = (chunkfile, df, contact)
        print str(self.port) + " allowing send of " + chunkfile.getName()
        return contact

    def scheduleAfterSend(self, name, method, *args):
        self.allowedList[name][1].addCallback(method, *args)

if __name__ == '__main__':
    s = ChunkServer(6000,reactor,"/home/ben/src/devstorm-cs87/src")
    reactor.run()

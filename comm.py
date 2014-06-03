#!/usr/bin/python
'''
Comm.py is the set of methods and objects which handle the nitty gritty data transfer and communication for the sending files part of our program
'''


# sender.py: connects to network, sends a message to another node, quits


import entangled, twisted, sys, time, os, struct, hashlib
from twisted.internet import reactor, defer
from entangled.kademlia.node import rpcmethod
from entangled.kademlia import datastore
from fetcher import ChunkFetcher

class ChunkSafeComm(entangled.node.EntangledNode):
    def __init__(self, udpPort=4000, dataStore=None, routingTable=None, networkProtocol=None):
        self.avSpace = self.spaceFinder('/')
        entangled.node.EntangledNode.__init__(self, udpPort, dataStore, routingTable, networkProtocol)

    # returns amount of free space on drive so we can allocate
    def spaceFinder(self,dir):
        statistics = os.statvfs(dir)
        return int(statistics.f_bavail * statistics.f_frsize)

    # Callback that prints the result to the screen
    def printout(self, result):
        print result
        return result

    def printNum(self,result,number):
            print "result was: " + str(result)
            print number
            return result

    def countSuccess(self,result):
        num = len([i for i in result if i[0] == True])
        print str(num) + " succeeded"
        return result

    # Callback that, given a list of contacts, runs the printMesg rpc on them.
    # Sets up callbacks so that each result will be printed out, and then the
    # program will quit once we've heard back from all nodes
    def sayHello(self, nodes):
        print "Found nodes"
        results = []
        numreplied = 0
        for node in nodes:
            # call RPC
            numreplied += 1
            res = node.printMesg("Hello from " + str(self.port))
            # print out result of RPC when it completes
            res.addCallback(self.printout)
            res.addErrback(self.printNum,"^ERROR^")
            results.append(res)
        # set up a DeferredList (barrier) to stop reactor when all RPCs return
        dl = defer.DeferredList(results, consumeErrors=True)
        dl.addErrback(self.printNum,"comm59")
        dl.addCallback(self.printNum, numreplied)
        dl.addCallback(self.countSuccess)
        dl.addCallback(stopReactor)

    # Hello world callback - finds a bunch of nodes and sets up sayHello to talk to them - for testing
    def doHelloWorld(self, *args):
        print "Finding nodes"
        df = self.iterativeFindNode("aaaaaaaaaaaaaaaaaaaa")
        df.addCallback(self.sayHello)

    # Returns a contact that is willing to store the specified chunk
    def findDestination(self, chunk):
        selected = None

        # contact each of the nodes in the result to see if they are willing to 
        # store the chunk

        def tryNodes(result):
            resp = []
            contactlist = []
            for contact in result:
                contactlist.append(contact)
                # print contact.port
                if contact.id != self.id:
                    resp.append(contact.reserveSpace(chunk.size))
            dl = defer.DeferredList(resp)
            dl.addErrback(self.printNum,"comm83")
            dl.addCallback(gotResponses,contactlist,chunk)
            dl.addCallback(pickOutContact)
            return dl

        # called when we hear back from the nodes we asked to reserve space
        # result is a list of (True, (ok?, id, freespace)) and (False, <Failure>)
        # for the moment, select the one that's ok and has most free space
        def gotResponses(result,contactlist,chunk):
            selected = None
            responses = []
            #print "Responses: " + str([res[1] for res in result])
            for res in result:
                if res[0] == True and res[1][0] == True:
                    if selected == None or res[1][2] > selected[2]:
                        selected = res[1]
            responses.append(self.findContact(selected[1]))
            for contact in contactlist:
                if contact.id != selected[1] and contact.id != self.id:
                    responses.append(contact.cancelReservation(chunk.size))
            return defer.DeferredList(responses)

        def pickOutContact(result):
            return result[0][1]
                    
        # invert all bytes of my id
        searchid = struct.pack("20b",*[~b for b in struct.unpack("20b", self.id)])
        df = self.iterativeFindNode(searchid)
        df.addErrback(self.printNum,"comm115")
        df.addCallback(tryNodes)
        return df

    # callback for once we've picked a destination, ask the destination to
    # fetch the specified chunk
    def sendChunk(self, contact, myip, myport, chunk):
        print "sending chunk to " + str(contact.port)
        df = contact.fetchChunk(myip, myport, chunk.getName())
        df.addErrback(self.printNum,"comm124")
        return df

    # RPC method that returns this node's port
    @rpcmethod
    def sayport(self):
        return self.port
    
    #used for negotiation heuristic
    @rpcmethod
    def sayAvailableSpace(self):
        return self.avSpace

    # RPC method that prints a message to the remote node's screen, and then
    # returns a success message
    @rpcmethod
    def printMesg(self, mesg):
        time.sleep(1)
        print str(self.port) + " received message: " + mesg
        return str(self.port) + ": Message received"

    #subtracts the ammt of space required from the avail. space
    @rpcmethod
    def reserveSpace(self, chunkSize):
        if chunkSize <= self.avSpace:
            self.avSpace -= chunkSize
            print str(self.port) + " reserving " + str(chunkSize) + "/" + str(self.avSpace) + " bytes"
            return (True, self.id, self.avSpace)
        else:
            print str(self.port) + " can't reserve " + str(chunkSize) + "/" + str(self.avSpace) + " bytes"
            return (False, self.id, self.avSpace)


    #after rejection unallocates the space
    #ugly because we'd like to be able to free space if requests time
    #out as well
    @rpcmethod
    def cancelReservation(self, chunkSize):
        self.avSpace += chunkSize
        print str(self.port) + " freeing " + str(chunkSize) + "/" + str(self.avSpace) + " bytes"
        return True
        #pass

    # tells a node to download a particular chunk from the fileserver
    # running on the specified address and port
    @rpcmethod
    def fetchChunk(self, sourceAddress, sourcePort, chunkName):
        print "getting " + chunkName + " from " + str(sourcePort)
        #benchmark line
        timestart = time.time()
        def getTheFile(protocol, fname):
            #print "began transfer"
            protocol.getFile(fname)
            protocol.fileDf.addCallback(logTheFile)

        def logTheFile(result):
            hKey = hashlib.sha1(chunkName).digest()
            self.iterativeStore(hKey,self.id)
            #print "Storing {%s -> %s}" % (chunkName,self.id)
            return result
            
        fetcher = ChunkFetcher(sourceAddress,sourcePort)
        connDf = fetcher.connect()
        connDf.addErrback(self.printNum,"comm168")
        connDf.addCallback(getTheFile,chunkName)
        #benchmark lines 2
        timeend = time.time()
        print "It took %f seconds to fetch %s\n" %(timeend-timestart,chunkName)
        return True

# stop the reactor
def stopReactor(*args):
    reactor.stop()

# Command line invocation - for testing
if __name__ == "__main__":
    # first argument is this node's port number
    n = ChunkSafeComm(int(sys.argv[1]))
    # second argument is bootstrap IP, third is bootstrap port
    n.joinNetwork([(sys.argv[2],int(sys.argv[3]))])
    # Install our program to run once node joined to network
    n._joinDeferred.addCallback(n.doHelloWorld)
    twisted.internet.reactor.run()

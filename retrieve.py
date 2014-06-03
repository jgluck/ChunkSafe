#!/usr/bin/python
'''
you run retrieve from the commandline with the following parameters
<Virtual file name> <Destination Directory> <port (if using start chunksafe always 4000)>
'''
import hashlib, os, tarfile, sys
from fetcher import ChunkFetcher
from comm import ChunkSafeComm
from twisted.internet import reactor

class ChunkReader:
    def __init__(self,dirname,bootstrapPort):
        self.dirname = dirname
        self.commPort = getFreePort(5000)
        self.comm = ChunkSafeComm(self.commPort)
        self.comm.joinNetwork([("127.0.0.1",bootstrapPort)])
        self.name = hashlib.sha1(dirname).hexdigest() + ".tar.bz2"
        print self.name

    def copyFile(self,fname,dest):
        hKey = hashlib.sha1(self.name).digest()
        def findContact(result):
            if type(result) == dict:
                id = result[hKey]
                print "asking for contact with id " + id
                contactDf = self.comm.findContact(id)
                return contactDf
            else:
                raise KeyError
        
        def connectToContact(result):
            servAddr = result.address
            servPort = result.port + 500
            print servAddr + ":" + str(servPort)
            fetcher = ChunkFetcher(servAddr, servPort)
            return fetcher.connect()

        # retrieveFile(Protocol)
        def retrieveChunk(result):
            result.getFile(self.name)
            return result.fileDf

        #pulls the file out of the tar
        def retrieveFile(result):
            print result
            self.tar = tarfile.open(self.name, 'r:bz2')
            if os.path.isdir(dest):
                destdir = dest
            else:
                destdir = os.path.dirname(dest)
            self.tar.extract(fname,destdir)

        #Deletes the tar after retrieval
        def cleanup(result):
            print "Cleaning Up"
            self.tar.close()
            os.remove(self.name)
            reactor.stop()

        #handles error
        def errorHandler(result):
            result.trap(KeyError)
            print "That directory was not found!"

        print hKey
        idDf = self.comm.iterativeFindValue(hKey)
        idDf.addCallback(findContact)
        idDf.addCallback(connectToContact)
        idDf.addCallback(retrieveChunk)
        idDf.addCallback(retrieveFile)
        idDf.addCallback(cleanup)
        idDf.addErrback(errorHandler)
        idDf.addErrback(self.comm.printNum, "retrieve17")
        

def getFreePort(startPort):
    return 7000

def usage():
    print sys.argv[0] + " <virtual filename> <destination> <daemon port>"

if __name__ == "__main__":
    def copyTheFile(result):
        c.copyFile(fname,sys.argv[2])

    if len(sys.argv) != 4:
        usage()
        exit(1)
    else:
        (dir,fname) = os.path.split(sys.argv[1])
        c = ChunkReader(dir, int(sys.argv[3]))
        c.comm._joinDeferred.addCallback(copyTheFile)
        reactor.run()

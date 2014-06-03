import twisted.internet.reactor, os
from os import stat


class ChunkFile(object):
    
    '''
    constructor
    opens the file in read mode
    '''
    def __init__(self,iName):
        self.name = iName
        self.meat = file(str(iName),'r')
        statInfo= stat(iName)
        self.size = statInfo.st_size
        #self.user = statInfo.st_uid

    '''
    Retreivers
    '''
    def getName(self):
        #return self.name
        return os.path.basename(self.name)

    def getMeat(self):
        return self.meat

    def getSize(self):
        return self.size

    def getModTime(self):
        return stat(self.name).st_mtime

    def getAccessTime(self):
        return stat(self.name).st_atime

    def read(self):
        return self.meat.read()

    def close(self):
        self.meat.close()


if __name__== "__main__":
    inName = raw_input("What file name?>")
    a = ChunkFile(inName)
    print a.getSize()
    print a.getModTime()
    print a.getAccessTime()
    print a.getMeat().read(500)
    print a.getAccessTime()

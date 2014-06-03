#!/usr/bin/python

# chunks.py: contains routines for dividing a directory into chunks

import tarfile, os, hashlib, platform
from chunkfile import ChunkFile

'''
Chunk: represents a tar file of the files in a directory:
essentially, the result of
find ! -type d | xargs tar cf chunk

Form of chunk names is
/<basedir>/<path>/<file>
becomes a file in
sha1(/<hostname>/<path>).tar.bz2
'''
class Chunk:
    # initialize the chunk with the name of the dir getting backed up
    def __init__(self, dirname, realbase, virtbase):
        self.realdir = os.path.join(realbase,dirname)
        self.virtdir = os.path.join(virtbase,dirname).rstrip(os.path.sep)
        self.name = hashlib.sha1(self.virtdir).hexdigest() + ".tar.bz2"

    # Make an archive of the files in this chunk
    def archive(self,storageDir):
        self.fileName = os.path.join(storageDir,self.name)
        tar = tarfile.open(self.fileName, 'w:bz2')
        files = os.listdir(self.realdir)
        #print files
        for fname in files:
            path = os.path.join(self.realdir,fname)
            if(os.path.isdir(path)):
                tar.add(path,fname,recursive = False)
                #continue
            else:
                #print "archive: " + fname
                tar.add(path,fname)
        tar.close()
        self.chunkfile = ChunkFile(self.fileName)
        return self.chunkfile

    # Delete this chunk's tar file
    def dissolve(self,result):
        self.chunkfile.close()
        # print "dissolving " + self.name
        os.remove(self.fileName)

# BackupDir: create one of these for the root directory we want to back up
class BackupDir:
    def __init__(self, dirname, storedir):
        self.realbase = dirname
        self.storageDir = storedir
        hostname = platform.node()
        sep = os.path.sep
        self.virtbase = sep + hostname
        self.sdList = None
        self.chunkList = None

    # returns a string containing the list of directories inside this one to be
    # stored in DHT
    def subdirs(self):
        # paths = ""
        # for item in self.sdList:
        #     paths = paths + "\n" +    item 
        return "\n".join([self.dirToVirtDir(dir) for dir in self.walkDir()])

    def dirToVirtDir(self, dir):
        return os.path.join(self.virtbase,dir).rstrip(os.path.sep)
    
    # returns a list or iterator for the chunks that will be made of the directory
    def chunks(self):
        if self.chunkList == None:
            self.chunkList = []
            for dir in (self.walkDir()):
                self.chunkList.append(Chunk(dir,self.realbase,self.virtbase))
        return self.chunkList

    # sets sdList to the list of subdirectories
    def walkDir(self):
        if self.sdList == None:
            self.sdList = []
            for root,dirs,files in os.walk(self.realbase):
                # remove self.realbase from the directory path:
                if root.startswith(self.realbase): # probably always true
                    if self.realbase[-1] == os.path.sep: # make sure to remove leading "/"
                        root = root[len(self.realbase):]
                    else:
                        root = root[len(self.realbase)+1:] 
                self.sdList.append(root)
        return self.sdList


# how I'd like to use this stuff
# d = BackupDir("/local")
# node.store(hostname, d.subdirs())
# for c in d.chunks():
#     h = chooseHost(c)
#     h.sendFile(c.file())
#     node.store(c.name(), h)
#Currently dumps a bunch of tars wherever you are. Watch out!
if __name__ == "__main__":
    d = BackupDir("/home/jgluck1/cs33/hello",".")
    d.walkDir()
    #print d.subdirs()
    for item in d.chunks():
        #print "main: " + item.name
        item.archive(".")
    print d.subdirs()
    #print os.listdir("/home/jonathan/Documents/") 

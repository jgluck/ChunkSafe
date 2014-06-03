#!/usr/bin/python

# create a test network of ChunkSafeNodes

from chunksafe import ChunkSafeNode
import twisted.internet.reactor
import sys

def usage():
    print sys.argv[0] + " <starting port> <backup dir> <temp storage dir>"

if __name__ == "__main__":
    if len(sys.argv) != 4:
        usage()
        exit(1)

    nodes = []
    addr = "127.0.0.1"
    startport = int(sys.argv[1])
    n = ChunkSafeNode(startport,sys.argv[2],sys.argv[3])
    nodes.append(n)

    for i in range(14):
        port = startport + 1 + i
        n = ChunkSafeNode(port,sys.argv[2],sys.argv[3],addr,port-1)
        nodes.append(n)

    twisted.internet.reactor.run()

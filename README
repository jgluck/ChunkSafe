ChunkSafe: Content-Addressable Peer-to-Peer Backup for Trusted Networks
Ben Lipton and Jonathan Gluck
CPSC 87: Parallel and Distributed Systems
Swarthmore College, Spring 2010

Included files:
chunksafe.py: main program, call as follows:
    1. Create first node
    chunksafe.py <port to run on> <backup dir> <scratch dir> <backup time (HH MM)>
    2. Create subsequent node
    chunksafe.py <port to run on> <ip of bootstrap node> <port of bootstrap node> <backup dir> <scratch dir> <backup time (HH MM)>
    3. Resume killed node
    chunksafe.py <port to run on (must be the same as original node)>

startchunksafe.sh: ugly shell script for running program on Swarthmore network. Can be modified to work on other systems, but designed only to facilitate testing.

retrieve.py: file retrieval script, call as follows:
    retrieve.py <Virtual file name> <Destination Directory> <port of local daemon (if using startchunksafe.sh always 4000)>

bootstrap.py: program used for testing, creates 15 nodes on a single machine
chunkfile.py: class abstracting a file on the filesystem so that we can get its stats easily
chunks.py: classes related to making chunks out of a backup directory
comm.py: DHT node used by ChunkSafeNode to communicate between machines
fetcher.py: Class that uses Twisted to download a file from file server
server.py: Class that uses Twisted to send a file when requested via TCP

Directories:
entangled: DHT implementation based on Twisted engine
examples: Examples taken from Entangled for reference
googlevoice: Allows the program to send Jon a text message when the backup finishes (just for fun)

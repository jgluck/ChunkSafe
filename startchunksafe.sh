#!/bin/bash

mkdir -p /local/blipto1/{backup,storage,scratch}
src=/home/jgluck1/cs87/devstorm-cs87/src
backup=/local/blipto1/backup
storage=/local/blipto1/storage
scratch=/local/blipto1/scratch

if [ -z $1 ]; then
  t1=1
  t2=00
else
  t1=$1
  t2=$2
fi

if [ -f chunksafedetails ]; then
  ip=`cut -d '|' -f 1 chunksafedetails`
  port=`cut -d '|' -f 2 chunksafedetails`
  pushd $storage
  ($src/chunksafe.py 4000 $ip $port $backup $scratch $t1 $t2)
  popd
else
  ip=`ifconfig  | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}'`
  port=4000
  echo "$ip|$port" > chunksafedetails
  pushd $storage
  ($src/chunksafe.py $port $backup $scratch $t1 $t2)
  popd
  rm -v chunksafedetails
fi

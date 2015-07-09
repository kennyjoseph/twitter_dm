"""
A script to determine whether or not a particular user has been deleted or suspended
"""
__author__ = 'kjoseph'
import sys, os, requests
from time import sleep

deleted_or_suspended = []
with open(sys.argv[1]) as infil:
    for line in infil:
        line_spl = line.strip().split(',')
        deleted_or_suspended.append(line_spl[0])

print len(deleted_or_suspended)

i = 0
if os.path.exists(sys.argv[2]):
    with open(sys.argv[2]) as infil:
        already_gotten = set([line.strip().split(",")[0] for line in infil])
        print len(already_gotten)
    deleted_or_suspended = [u for u in (set(deleted_or_suspended) - already_gotten)]

print 'N deleted/suspended to check: ', len(deleted_or_suspended)

with open(sys.argv[2], "a") as out_fil:
    for u in deleted_or_suspended:
        #if i % 100 == 0:
        print i
        try:
            status = requests.get('http://twitter.com/intent/user?user_id=' + u).status_code
            if status == 404:
                out_fil.write(u + ",d\n")
            elif status == 200:
                out_fil.write(u +",s\n")
            i += 1
        except:
            print 'FAILED: ', u
            sleep(600)
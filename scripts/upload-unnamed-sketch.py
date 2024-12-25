#! /usr/bin/env python
import sys
import argparse
import requests
import sourmash
import json
import os
import time


def main():
    p = argparse.ArgumentParser()
    p.add_argument('sketchfile')
    p.add_argument('--host', default='https://chill-filter.sourmash.bio')
    p.add_argument('--write-result-to-pidfile', action='store_true')
    args = p.parse_args()

    # load sketch
    ss = list(sourmash.load_file_as_signatures(args.sketchfile, ksize=51))
    assert len(ss) == 1
    ss = ss[0]

    mh = ss.minhash.downsample(scaled=100_000)
    new_ss = sourmash.SourmashSignature(mh) # w/o name

    # now re-encode as in-form JSON (=> not in an array)
    sig_json = sourmash.save_signatures_to_json([new_ss])
    sig2 = json.loads(sig_json)
    sig2 = sig2[0]
    sig2_json = json.dumps(sig2)

    url = args.host + '/sketch'
    print(os.getpid(), 'posting:', url)
    start = time.time()
    r = requests.post(url, data=dict(signature=sig2_json))
    finish = time.time()

    if args.write_result_to_pidfile:
        status_code = r.status_code
        pidfile = f"upload.pid={os.getpid()}.status={status_code}.html"
        with open(pidfile, "wt") as fp:
            fp.write(r.text)
            fp.write(f"\n<!-- start: {start}; finish: {finish}; duration: {finish - start} -->\n")

        sys.exit(0)

    assert 'Sample search summary for: (unnamed sample)' in r.text
    assert r.result_code == 200


if __name__ == '__main__':
    sys.exit(main())

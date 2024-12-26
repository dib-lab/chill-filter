#! /usr/bin/env python
import sourmash
import argparse
import sys
import os


from chill_filter_web import utils


def main():
    p = argparse.ArgumentParser()
    p.add_argument('sketchfile')
    args = p.parse_args()

    ss = utils.load_sig(args.sketchfile)
    assert ss is not None

    filename = os.path.basename(args.sketchfile)
    md5 = ss.md5sum()[:8]

    url = f"/{md5}/{filename}"
    print(url)


if __name__ == '__main__':
    sys.exit(main())

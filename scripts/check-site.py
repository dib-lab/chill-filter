#! /usr/bin/env python
import sys
import argparse
import requests


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='https://chill-filter.sourmash.bio')
    args = p.parse_args()

    url = args.host + '/'
    print('getting:', url)
    r = requests.get(url)
    assert r.status_code == 200
    assert '<title>chill-filter sample screening - home page</title>' in r.text

    url = args.host + '/example?filename=SRR606249.k51.s100_000.sig.zip'
    print('getting:', url)
    r = requests.get(url)
    assert r.status_code == 200, r.status_code
    assert '95.0% (5.1 Gbp)' in r.text

    url = args.host + '/ee6adb3e/SRR606249.k51.s100_000.sig.zip/delete'
    print('getting:', url)
    r = requests.get(url)
    assert r.status_code == 200, r.status_code

    url = args.host + '/example?filename=SRR606249.k51.s100_000.sig.zip'
    print('getting:', url)
    r = requests.get(url)
    assert r.status_code == 200
    assert '95.0% (5.1 Gbp)' in r.text

    print('success!!')


if __name__ == '__main__':
    sys.exit(main())

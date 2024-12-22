import time

import sourmash
from sourmash_plugin_branchwater import sourmash_plugin_branchwater as branch

from .database_info import MOLTYPE, KSIZE, SCALED


def load_sig(fullpath):
    fullpath = str(fullpath)
    try:
        ss = sourmash.load_file_as_index(fullpath)
        ss = ss.select(moltype=MOLTYPE, ksize=KSIZE, scaled=SCALED)
        if len(ss) == 1:
            ss = list(ss.signatures())[0]
            if len(ss.minhash):
                return ss
    except:
        pass

    return None


def run_gather(outpath, csv_filename, db_info):
    start = time.time()
    status = branch.do_fastmultigather(
        outpath,
        db_info.filename,
        0,
        KSIZE,
        SCALED,
        MOLTYPE,
        csv_filename,
        False,
        False,
    )
    end = time.time()

    print(f"branchwater gather status: {status}; time: {end - start:.2f}s")
    return status


def sig_is_assembly(ss):
    mh = ss.minhash
    # track abundance set? => assembly
    if not mh.track_abundance:
        print('ZZZ1 - is assembly')
        return True

    # count the number > 1 in abundance
    n_above_1 = sum(1 for (hv, ha) in mh.hashes.items() if ha > 1)
    f_above_1 = n_above_1/len(mh)
    print(f'n_above_1: {n_above_1}, of {len(mh)}, f={f_above_1:.3}')

    # more than 10% > 1? => probably not assembly
    if f_above_1 > 0.1:
        return False

    # nope! assembly!
    return True


def estimate_weight_of_unknown(ss, db, *, CUTOFF=5):
    mh = ss.minhash
    merged_hashes = db.merged_hashes

    unknown = [ (hv, ha) for (hv, ha) in mh.hashes.items() if ha not in merged_hashes ]
    sum_unknown = sum( ha for (hv, ha) in unknown )
    sum_high = sum( ha for (hv, ha) in unknown if ha >= CUTOFF )
    sum_low = sum( ha for (hv, ha) in unknown if ha < CUTOFF )

    return sum_high / sum_unknown, sum_low / sum_unknown


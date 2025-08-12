import time

import sourmash
from sourmash import commands
from sourmash_plugin_branchwater import sourmash_plugin_branchwater as branch

from .database_info import MOLTYPE, KSIZE, SCALED


class FakeArgs:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def load_sig(fullpath):
    fullpath = str(fullpath)
    try:
        ss = sourmash.load_file_as_index(fullpath)
        ss = ss.select(moltype=MOLTYPE, ksize=KSIZE, scaled=SCALED)
        if len(ss) == 1:
            ss = list(ss.signatures())[0]
            return ss
    except:
        pass

    return None


def run_gather(sigpath, csv_filename, db_info):
    start = time.time()
    status = 0
    # prepare args object
    args = FakeArgs(quiet=True,
                    debug=False,
                    ksize=KSIZE,
                    scaled=SCALED,
                    picklist=None,
                    moltype=MOLTYPE,
                    md5=None,
                    query=sigpath,
                    linear=False,
                    prefetch=True,
                    save_prefetch=None,
                    save_prefetch_csv=False,
                    output=csv_filename,
                    save_matches=False,
                    threshold_bp=0,
                    output_unassigned=False,
                    dna=True,
                    protein=False,
                    dayhoff=False,
                    hp=False,
                    skipm1n3=False,
                    skipm2n3=False,
                    include_db_pattern=None,
                    exclude_db_pattern=None,
                    cache_size=0,
                    databases=db_info.filenames,
                    fail_on_empty_database=True,
                    ignore_abundance=False,
                    estimate_ani_ci=True,
                    num_results=0,
                    )
    
    commands.gather(args)
    if 0:
        status = branch.do_fastmultigather(
            sigpath,
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


def calc_abund_stats_above_1(mh):
    # count the number > 1 in abundance
    n_above_1 = sum(1 for (hv, ha) in mh.hashes.items() if ha > 1)
    f_above_1 = n_above_1/len(mh)

    return n_above_1


def sig_is_assembly(ss):
    mh = ss.minhash

    # track abundance not set? => assembly
    if not mh.track_abundance:
        return True

    n_above_1 = calc_abund_stats_above_1(mh)
    f_above_1 = n_above_1 / len(mh)

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


import os
import tempfile
import time
import gzip
import shutil

from flask import Flask, flash, request, redirect, url_for
from flask import render_template, send_from_directory
from werkzeug.utils import secure_filename

import pandas as pd

import sourmash
from sourmash import save_signatures_to_json
from sourmash_plugin_branchwater import sourmash_plugin_branchwater as branch

UPLOAD_FOLDER = "/tmp/chill"
EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "../examples/")

from .database_info import databases as sourmash_databases
from .database_info import MOLTYPE, KSIZE, SCALED

if 0:
    start = time.time()
    print(f'loading dbs:')
    for db in sourmash_databases:
        db.load()
        print(f'...done! {time.time() - start:.1f}s')

app = Flask(__name__)
jinja_env = app.jinja_env

def percent(value):
    return f"{value*100:.1f}%"
jinja_env.filters['percent'] = percent

def format_bp(bp):
    "Pretty-print bp information."
    bp = float(bp)
    if bp < 500:
        return f"{bp:.0f} bp"
    elif bp <= 500e3:
        return f"{round(bp / 1e3, 1):.1f} kbp"
    elif bp < 500e6:
        return f"{round(bp / 1e6, 1):.1f} Mbp"
    elif bp < 500e9:
        return f"{round(bp / 1e9, 1):.1f} Gbp"
    return f"??? {bp}"
jinja_env.filters['format_bp'] = format_bp

def unique_weighted_bp(item):
    return format_bp(item['n_unique_weighted_found'] * item['scaled'])
jinja_env.filters['unique_weighted_bp'] = unique_weighted_bp

def unique_flat_bp(item):
    return format_bp(item['unique_intersect_bp'])
jinja_env.filters['unique_flat_bp'] = unique_flat_bp


def load_sig(fullpath):
    try:
        ss = sourmash.load_file_as_index(fullpath)
        ss = ss.select(moltype=MOLTYPE, ksize=KSIZE, scaled=SCALED)
        if len(ss) == 1:
            ss = list(ss.signatures())[0]
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


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # check if the post request has the file part
        if "sketch" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["sketch"]

        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            outpath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(outpath)

            ss = load_sig(outpath)
            if ss:
                md5 = ss.md5sum()[:8]
                return redirect(f"/{md5}/{filename}/search")

    # default
    return render_template("index.html")


@app.route("/sketch", methods=["GET", "POST"])
def sketch():
    if request.method == "POST":
        # check if the post request has the file part
        if "signature" not in request.form:
            flash("No file part")
            return redirect(request.url)
        sig_json = request.form["signature"]

        success = False
        filename = f"t{int(time.time())}.sig.gz"
        outpath = os.path.join(UPLOAD_FOLDER, filename)
        with gzip.open(outpath, "wt") as fp:
            fp.write(f"[{sig_json}]")

        ss = load_sig(outpath)
        if ss:
            md5 = ss.md5sum()[:8]
            return redirect(f"/{md5}/{filename}/search")

    return redirect(url_for("index"))


@app.route("/example", methods=["GET"])
def example():
    "Retrieve an example"
    filename = request.args["filename"]
    filename = secure_filename(filename)
    frompath = os.path.join(EXAMPLES_DIR, filename)
    if not os.path.exists(frompath):
        return f"example file {filename} not found in examples/"

    ss = load_sig(frompath)
    if ss is None:
        return f"bad example."

    md5 = ss.md5sum()[:8]

    # now build the filename & make sure it's in the upload dir.
    topath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(topath):
        print("copying")
        shutil.copy(frompath, topath)

    return redirect(f"/{md5}/{filename}/search")


@app.route("/")
@app.route("/<path:path>")
def get_md5(path):
    print("PATH IS:", path, os.path.split(path))
    md5, filename, action = path.split("/")

    outpath = os.path.join(UPLOAD_FOLDER, filename)
    success = False
    ss = None
    if os.path.exists(outpath):
        ss = load_sig(outpath)
        if ss and ss.md5sum()[:8] == md5:
            success = True

    if success:
        assert ss is not None
        sample_name = ss.name or "(unnamed sample)"
        if action == 'download_csv':
            csv_filename = filename + ".x.all.gather.csv" # @CTB
            return send_from_directory(UPLOAD_FOLDER, csv_filename)
        elif action == "search":
            search_db = None
            for db in sourmash_databases:
                if db.default:
                    search_db = db
                    break

            if search_db is None:
                raise Exception("no default search DB?!")

            csv_filename = f"{outpath}.x.{search_db.shortname}.gather.csv"
            if not os.path.exists(csv_filename):
                status = run_gather(outpath, csv_filename, search_db)
                if status != 0:
                    return "search failed, for reasons that are probably not your fault"
                else:
                    print(f'output is in: "{csv_filename}"')
            else:
                print(f"using cached output in: '{csv_filename}'")

            gather_df = pd.read_csv(csv_filename)
            gather_df = gather_df[gather_df["f_unique_weighted"] >= 0.001]

            gather_df['match_description'] = gather_df['match_name'].apply(search_db.get_display_name)

            # process abundance-weighted matches
            if not sig_is_assembly(ss):
                #f_unknown_high, f_unknown_low = estimate_weight_of_unknown(ss,
                #         search_db)
                f_unknown_high, f_unknown_low = 0, 0

                if len(gather_df):
                    last_row = gather_df.tail(1).squeeze()
                    sum_weighted_found = last_row["sum_weighted_found"]
                    total_weighted_hashes = last_row["total_weighted_hashes"]

                    f_found = sum_weighted_found / total_weighted_hashes

                    return render_template(
                        "sample_search_abund.html",
                        sample_name=sample_name,
                        sig=ss,
                        gather_df=gather_df,
                        f_found=f_found,
                        f_unknown_high=f_unknown_high,
                        f_unknown_low=f_unknown_low,
                    )
                else:
                    return "no matches found!"
            # process flat matching (assembly)
            else:
                print('running flat')
                if len(gather_df):
                    last_row = gather_df.tail(1).squeeze()
                    f_found = gather_df['f_unique_to_query'].sum()

                    return render_template(
                        "sample_search_flat.html",
                        sample_name=sample_name,
                        sig=ss,
                        gather_df=gather_df,
                        f_found=f_found,
                    )
                else:
                    return "no matches found!"

        elif action == "download":
            return send_from_directory(UPLOAD_FOLDER, filename)

        # default
        sum_weighted_hashes = sum(ss.minhash.hashes.values())
        return render_template(
            "sample_index.html",
            sig=ss,
            sig_filename=filename,
            sample_name=sample_name,
            sum_weighted_hashes=sum_weighted_hashes,
        )
    else:
        return redirect(url_for("index"))

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/guide")
def guide():
    return render_template("guide.html")

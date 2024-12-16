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

MOLTYPE = "DNA"
KSIZE = 51
SCALED = 100_000
UPLOAD_FOLDER = "/tmp/chill"
EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "../examples/")

app = Flask(__name__)


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
                md5 = ss.md5sum()
                return redirect(f"/{md5}/{filename}/")

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
            md5 = ss.md5sum()
            return redirect(f"/{md5}/{filename}/")

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

    md5 = ss.md5sum()

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
        if ss and ss.md5sum() == md5:
            success = True

    if success:
        # @CTB check that it's weighted?
        assert ss is not None
        sample_name = ss.name or "(unnamed sample)"
        if action == "search":
            csv_filename = outpath + ".gather.csv"
            if not os.path.exists(csv_filename):
                start = time.time()
                status = branch.do_fastmultigather(
                    outpath,
                    "prepare-db/plants+animals+gtdb.rocksdb",
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
                if status != 0:
                    return "search failed, for reasons that are probably not your fault"
                else:
                    print(f'output is in: "{csv_filename}"')
            else:
                print(f"using cached output in: '{csv_filename}'")

            # load/process
            gather_df = pd.read_csv(csv_filename)
            gather_df = gather_df[gather_df["f_unique_weighted"] >= 0.001]
            if len(gather_df):
                last_row = gather_df.tail(1).squeeze()
                sum_weighted_found = last_row["sum_weighted_found"]
                total_weighted_hashes = last_row["total_weighted_hashes"]

                f_found = sum_weighted_found / total_weighted_hashes

                return render_template(
                    "sample_search.html",
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

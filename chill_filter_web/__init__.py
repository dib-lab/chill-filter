import os
import tempfile
import time
import gzip
import shutil
import glob
import collections
import uuid

from flask import Flask, flash, request, redirect, url_for
from flask import render_template, send_from_directory
from werkzeug.utils import secure_filename
import markdown

import pandas as pd

from . import jinja2_filters
from .database_info import get_search_db
from .database_info import MOLTYPE, KSIZE, SCALED
from .utils import *

default_settings = dict(
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../chill-data'),
    EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples/"),
    MAX_CONTENT_LENGTH = 10*1000*1000,
)


app = None
def init():
    global app

    app = Flask(__name__)
    app.config.update(default_settings)
    if 'CHILL_FILTER_SETTINGS' in os.environ:
        app.config.from_envvar('CHILL_FILTER_SETTINGS')

    jinja2_filters.add_filters(app.jinja_env.filters)

    try:
        os.mkdir(app.config['UPLOAD_FOLDER'])
    except FileExistsError:
        pass

    if 0:
        start = time.time()
        print(f'loading dbs:')
        for db in sourmash_databases:
            db.load()
            print(f'...done! {time.time() - start:.1f}s')


init()


def create_app():
    # Quick test configuration. Please use proper Flask configuration options
    # in production settings, and use a separate file or environment variables
    # to manage the secret key!
    app.secret_key = "super secret key"
    app.config["SESSION_TYPE"] = "filesystem"

    # sess.init_app(app)

    app.debug = True
    return app

###
### actual Web site stuff
###

# @CTB can we put this in a different module?


# handles default index
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/faq")
def faq():
    return render_template("faq.md")


@app.route("/guide")
def guide():
    return render_template("guide.md")


@app.route("/favicon.ico")
def favicon():
    return ""


# handles upload of precalculated sketch.
@app.route("/upload", methods=["POST"])
def upload():
    # check if the post request has the file part
    if "sketch" not in request.files:
        #flash("No file part")
        return redirect(request.url)

    file = request.files["sketch"]

    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == "":
        #flash("No selected file") # @CTB
        return redirect(request.url)

    if file:
        filename = secure_filename(file.filename)
        outpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(outpath)

        ss = load_sig(outpath)
        if ss:
            if ss.minhash:      # not empty?
                md5 = ss.md5sum()[:8]
                return redirect(url_for("sig_search", md5=md5, filename=filename))
            else:
                msg = "sketch is empty; please use a query larger than 500kb!"
                return render_template("error.html", error_message=msg), \
                    404

    # default - flash? redirect? @CTB
    return render_template("index.html")


# handles client-side sketch w/JSON sig
@app.route("/sketch", methods=['POST'])
def sketch():
    # check if the post request has the file part
    if "signature" not in request.form:
        #flash("No file part") # @CTB
        return redirect(request.url)

    # retrieve uploaded JSON and save to unique filename
    sig_json = request.form["signature"]
    filename = f"t{uuid.uuid4().hex}.sig.gz"
    outpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with gzip.open(outpath, "wt") as fp:
        fp.write(f"[{sig_json}]")

    # ok, can we load it?
    ss = load_sig(outpath)
    if ss:
        if ss.minhash:          # not empty?
            # success? build URL & redirect
            md5 = ss.md5sum()[:8]
            if app.config['TESTING']:
                return "TESTING MODE: upload successful"

            return redirect(url_for("sig_search", md5=md5, filename=filename))
        else:
            msg = "sketch is empty; please use a query larger than 500kb!"
            return render_template("error.html", error_message=msg), \
                404
    else:
        os.unlink(outpath)      # remove unused sketches

    # default: redirect to /
    return redirect(url_for("index"))


@app.route("/example", methods=["GET"])
def example():
    "Retrieve an example"
    filename = request.args["filename"]
    filename = secure_filename(filename)
    frompath = os.path.join(app.config['EXAMPLES_DIR'], filename)
    if not os.path.exists(frompath):
        msg = f"example file <tt>{filename}</tt> not found in examples"
        return render_template("error.html", error_message=msg), \
            404

    ss = load_sig(frompath)
    if ss is None:
        # doesn't match moltype etc, or other problems.
        msg = "Internal error: bad example file!?"
        return render_template("error.html", error_message=msg), \
            404

    md5 = ss.md5sum()[:8]

    # now build the filename & make sure it's in the upload dir.
    topath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(topath):
        print(f"copying example file: {frompath} {topath}")
        shutil.copy(frompath, topath)

    return redirect(url_for("sig_search", md5=md5, filename=filename))

## all the stuff underneath...

LoadedSig = collections.namedtuple('LoadedSig',
                                   ['ss', 'sample_name', 'prefix'])


# generic function to load md5/filename => LoadedSig tuple
def load_sig_by_urlpath(md5, filename):
    sigpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(sigpath):
        ss = load_sig(sigpath)
        if ss and ss.md5sum()[:8] == md5:
            sample_name = ss.name or "(unnamed sample)"

            return LoadedSig(ss, sample_name, sigpath)

    return None


# index page for LoadedSig
@app.route("/<string:md5>/<string:filename>/")
def sig_index(md5, filename):
    websig = load_sig_by_urlpath(md5, filename)
    if websig is None:
        return redirect(url_for("index"))

    mh = websig.ss.minhash
    num_distinct_hashes = len(mh)
    sum_weighted_hashes = sum(mh.hashes.values())
    n_above_1 = calc_abund_stats_above_1(mh)
    f_above_1 = n_above_1 / len(mh)
    return render_template(
        "sample_index.html",
        sig=websig.ss,
        sig_filename=filename,
        sample_name=websig.sample_name,
        num_distinct_hashes=num_distinct_hashes,
        sum_weighted_hashes=sum_weighted_hashes,
        n_above_1=n_above_1,
        f_above_1=f_above_1,
    )

# download CSV for LoadedSig
# @CTB: check if gather does not exist?
@app.route("/<string:md5>/<string:filename>/download_csv")
def sig_download_csv(md5, filename):
    websig = load_sig_by_urlpath(md5, filename)
    if websig is None:
        return redirect(url_for("index"))

    search_db = get_search_db()
    csv_filename = filename + f".x.{search_db.shortname}.gather.csv"
    return send_from_directory(app.config['UPLOAD_FOLDER'], csv_filename)


# download sketch for LoadedSig
@app.route("/<string:md5>/<string:filename>/download")
def sig_download(md5, filename):
    websig = load_sig_by_urlpath(md5, filename)
    if websig is None:
        return redirect(url_for("index"))

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# delete sketch for LoadedSig
@app.route("/<string:md5>/<string:filename>/delete")
def sig_delete(md5, filename):
    websig = load_sig_by_urlpath(md5, filename)
    if websig is None:
        return redirect(url_for("index"))

    ss = websig.ss
    sample_name = websig.sample_name
    sigpath = websig.prefix

    file_list = glob.glob(f"{sigpath}.*.csv")
    for filename in file_list + [sigpath]:
        try:
            print('removing:', (filename,))
            os.unlink(filename)
        except:
            pass
    return redirect(url_for("index"))


# top level search!
@app.route("/<string:md5>/<string:filename>/search")
def sig_search(md5, filename):
    websig = load_sig_by_urlpath(md5, filename)
    if websig is None:
        return redirect(url_for("index"))

    search_db = get_search_db()

    csv_filename = f"{websig.prefix}.x.{search_db.shortname}.gather.csv"
    if not os.path.exists(csv_filename):
        status = run_gather(websig.prefix, csv_filename, search_db)
        if status != 0:
            return "search failed, for reasons that are probably not your fault"
        else:
            print(f'output is in: "{csv_filename}"')
    else:
        print(f"using cached output in: '{csv_filename}'")

    # read!
    try:
        gather_df = pd.read_csv(csv_filename)
        gather_df = gather_df[gather_df["f_unique_weighted"] >= 0.001]
        gather_df = gather_df.sort_values(by='gather_result_rank')
    except:
        gather_df = []

    # no (significant) results?? exit.
    if not len(gather_df):
        return render_template(
            "sample_search_no_matches.html",
            search_db=search_db,
            sample_name=websig.sample_name)

    # ok, now prep for display.

    # provide match descriptions based on database-specific name rewriting
    gather_df['match_description'] = gather_df['match_name'].apply(search_db.get_display_name)

    # process abundance-weighted matches
    if not sig_is_assembly(websig.ss):
        #f_unknown_high, f_unknown_low = estimate_weight_of_unknown(ss,
        #         search_db)
        f_unknown_high, f_unknown_low = 0, 0

        last_row = gather_df.sort_values(by='sum_weighted_found').tail(1).squeeze()
        sum_weighted_found = last_row["sum_weighted_found"]
        total_weighted_hashes = last_row["total_weighted_hashes"]

        f_found = sum_weighted_found / total_weighted_hashes

        return render_template(
            "sample_search_abund.html",
            sample_name=websig.sample_name,
            sig=websig.ss,
            gather_df=gather_df,
            f_found=f_found,
            f_unknown_high=f_unknown_high,
            f_unknown_low=f_unknown_low,
            search_db=search_db,
        )
    # process flat matching (assembly)
    else:
        print('running flat')
        f_found = gather_df['f_unique_to_query'].sum()

        return render_template(
            "sample_search_flat.html",
            sample_name=websig.sample_name,
            sig=websig.ss,
            gather_df=gather_df,
            f_found=f_found,
            search_db=search_db,
        )


# subsearch - against other database(s)
@app.route("/<string:md5>/<string:filename>/subsearch/<string:dbname>/")
def sig_subsearch(md5, filename, dbname):
    websig = load_sig_by_urlpath(md5, filename)
    if websig is None:
        return redirect(url_for("index"))

    search_db = get_search_db(name=dbname)

    csv_filename = f"{websig.prefix}.x.{search_db.shortname}.gather.csv"
    if not os.path.exists(csv_filename):
        status = run_gather(websig.prefix, csv_filename, search_db)
        if status != 0:
            return "search failed, for reasons that are probably not your fault"
        else:
            print(f'output is in: "{csv_filename}"')
    else:
        print(f"using cached output in: '{csv_filename}'")

    # read!
    try:
        gather_df = pd.read_csv(csv_filename)
        gather_df = gather_df[gather_df["f_unique_weighted"] >= 0.001]
        gather_df = gather_df.sort_values(by='f_unique_weighted', ascending=False)
    except:
        gather_df = []

    # no (significant) results?? exit.
    if not len(gather_df):      # @CTB test
        return render_template(
            "subsearch_no_matches.html",
            search_db=search_db,
            sample_name=websig.sample_name)

    # ok, now prep for display.

    # provide match descriptions based on database-specific name rewriting
    gather_df['match_description'] = gather_df['match_name'].apply(search_db.get_display_name)

    # process abundance-weighted matches
    if not sig_is_assembly(websig.ss):
        last_row = gather_df.sort_values(by='sum_weighted_found').tail(1).squeeze()
        sum_weighted_found = last_row["sum_weighted_found"]
        total_weighted_hashes = last_row["total_weighted_hashes"]

        f_found = sum_weighted_found / total_weighted_hashes

        return render_template(
            "subsearch_abund.html",
            sample_name=websig.sample_name,
            sig=websig.ss,
            gather_df=gather_df,
            f_found=f_found,
            search_db=search_db,
        )
    # process flat matching (assembly)
    else:
        print('running flat')
        f_found = gather_df['f_unique_to_query'].sum()

        return render_template(
            "subsearch_flat.html",
            sample_name=websig.sample_name,
            sig=websig.ss,
            gather_df=gather_df,
            f_found=f_found,
            search_db=search_db,
        )


# subsearch - download CSV
@app.route("/<string:md5>/<string:filename>/subsearch/<string:dbname>/download_csv")
def sig_subsearch_download_csv(md5, filename, dbname):
    websig = load_sig_by_urlpath(md5, filename)
    if websig is None:
        return redirect(url_for("index"))

    csv_filename = f"{filename}.x.{dbname}.gather.csv"
    return send_from_directory(app.config['UPLOAD_FOLDER'], csv_filename)

import os
import tempfile
import time
import gzip
import shutil
import glob

from flask import Flask, flash, request, redirect, url_for
from flask import render_template, send_from_directory
from werkzeug.utils import secure_filename
import markdown

import pandas as pd

from . import jinja2_filters
from .database_info import databases as sourmash_databases
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


# handles default index, plus upload of precalculated sketch.
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
            outpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(outpath)

            ss = load_sig(outpath)
            if ss:
                md5 = ss.md5sum()[:8]
                return redirect(f"/{md5}/{filename}/search")

    # default
    return render_template("index.html")


# handles client-side sketch w/JSON sig
@app.route("/sketch", methods=["GET", "POST"])
def sketch():
    if request.method == "POST":
        # check if the post request has the file part
        if "signature" not in request.form:
            flash("No file part") # @CTB
            return redirect(request.url)

        # take uploaded file and save
        sig_json = request.form["signature"]
        success = False
        filename = f"t{int(time.time())}.sig.gz"
        outpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with gzip.open(outpath, "wt") as fp:
            fp.write(f"[{sig_json}]")

        ss = load_sig(outpath)
        if ss:
            # success? build URL & redirect
            md5 = ss.md5sum()[:8]
            if app.config['TESTING']:
                return "TESTING MODE: upload successful"
            return redirect(f"/{md5}/{filename}/search")

    print('fallthru')

    # default: redirect to /
    return redirect(url_for("index"))


@app.route("/example", methods=["GET"])
def example():
    "Retrieve an example"
    filename = request.args["filename"]
    filename = secure_filename(filename)
    frompath = os.path.join(app.config['EXAMPLES_DIR'], filename)
    if not os.path.exists(frompath):
        return render_template("error.html",
                               error_message=f"example file <tt>{filename}</tt> not found in examples"), 404

    ss = load_sig(frompath)
    if ss is None:
        # doesn't match moltype etc, or other problems.
        return render_template("error.html",
                               error_message="Internal error: bad example file!?"), 404

    md5 = ss.md5sum()[:8]

    # now build the filename & make sure it's in the upload dir.
    topath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(topath):
        print(f"copying: {frompath} {topath}")
        shutil.copy(frompath, topath)

    return redirect(f"/{md5}/{filename}/search")


@app.route("/")
@app.route("/<path:path>")
def get_by_md5(path):
    print("PATH IS:", path, os.path.split(path))
    path = path.split("/")
    if len(path) != 3:
        return redirect(url_for("index"))

    md5, filename, action = path

    # now try loading the sketch
    sigpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    success = False
    ss = None
    if os.path.exists(sigpath):
        ss = load_sig(sigpath)
        if ss and ss.md5sum()[:8] == md5:
            success = True

    print('SUCCESS VALUE:', success)
    if not success:
        return redirect(url_for("index"))

    assert ss is not None
    sample_name = ss.name or "(unnamed sample)"

    # actions!
    if action == 'download_csv':
        csv_filename = filename + ".x.all.gather.csv" # @CTB
        return send_from_directory(app.config['UPLOAD_FOLDER'], csv_filename)
    elif action == "download":
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    elif action == "delete":
        file_list = glob.glob(f"{sigpath}.*.csv")
        for filename in file_list + [sigpath]:
            try:
                print('removing:', (filename,))
                os.unlink(filename)
            except:
                pass
        return redirect(url_for("index"))
    elif action == "search":
        search_db = None
        for db in sourmash_databases:
            if db.default:
                search_db = db
                break

        if search_db is None:
            raise Exception("no default search DB?!")

        csv_filename = f"{sigpath}.x.{search_db.shortname}.gather.csv"
        if not os.path.exists(csv_filename):
            status = run_gather(sigpath, csv_filename, search_db)
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
        except:
            gather_df = []

        # no (significant) results?? exit.
        if not len(gather_df):
            return render_template(
                "sample_search_no_matches.html",
                sample_name=sample_name)

        # ok, now prep for display.

        gather_df['match_description'] = gather_df['match_name'].apply(search_db.get_display_name)

        # process abundance-weighted matches
        if not sig_is_assembly(ss):
            #f_unknown_high, f_unknown_low = estimate_weight_of_unknown(ss,
            #         search_db)
            f_unknown_high, f_unknown_low = 0, 0

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
        # process flat matching (assembly)
        else:
            print('running flat')
            last_row = gather_df.tail(1).squeeze()
            f_found = gather_df['f_unique_to_query'].sum()

            return render_template(
                "sample_search_flat.html",
                sample_name=sample_name,
                sig=ss,
                gather_df=gather_df,
                f_found=f_found,
            )

    # default: sample index
    sum_weighted_hashes = sum(ss.minhash.hashes.values())
    return render_template(
        "sample_index.html",
        sig=ss,
        sig_filename=filename,
        sample_name=sample_name,
        sum_weighted_hashes=sum_weighted_hashes,
    )

@app.route("/faq")
def faq():
    return render_template("faq.md")

@app.route("/guide")
def guide():
    return render_template("guide.md")

@app.route("/favicon.ico")
def favicon():
    return ""

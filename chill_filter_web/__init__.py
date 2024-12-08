import os
from flask import Flask, flash, request, redirect, url_for
from flask import render_template
from werkzeug.utils import secure_filename
import sourmash
from sourmash_plugin_branchwater import sourmash_plugin_branchwater as branch
import pandas as pd
import tempfile
import time

UPLOAD_FOLDER = '/tmp/chill'

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    print(request.method)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'sketch' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['sketch']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        print(file.filename)
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            success = False
            filename = secure_filename(file.filename)
            outpath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(outpath)

            try:
                ss = sourmash.load_file_as_index(outpath)
                ss = ss.select(moltype='DNA', ksize=51, scaled=100_000)
                if len(ss) == 1:
                    success = True
                    ss = list(ss.signatures())[0]
                    md5 = ss.md5sum()
                    print('SUCCESS')
            except:
                pass
                
            if success:
                return redirect(f'/{md5}/{filename}/')
    return render_template("index.html")


@app.route('/')
@app.route('/<path:path>')
def get_md5(path):
    print('PATH IS:', path, os.path.split(path))
    md5, filename, action = path.split('/')

    outpath = os.path.join(UPLOAD_FOLDER, filename)
    success = False
    ss = None
    if os.path.exists(outpath):
        ss = sourmash.load_file_as_index(outpath)
        ss = ss.select(moltype='DNA', ksize=51, scaled=100_000)
        if len(ss) == 1:
            ss = list(ss.signatures())[0]
            if ss.md5sum() == md5:
                success = True

    if success:
        # @CTB check that it's weighted?
        assert ss is not None
        if action == 'search':
            csv_filename = outpath + '.gather.csv'
            if not os.path.exists(csv_filename):
                start = time.time()
                status = branch.do_fastgather(outpath,
                                              'prepare-db/animals-and-gtdb.rocksdb',
                                              0,
                                              51,
                                              100_000,
                                              'DNA',
                                              csv_filename,
                                              None)
                end = time.time()

                print(f'branchwater gather status: {status}; time: {end - start:.2f}s')
                if status !=0 :
                    return "search failed, for reasons that are probably not your fault"
                else:
                    print(f'output is in: "{csv_filename}"')
            else:
                print(f"using cached output in: '{csv_filename}'")

            gather_df = pd.read_csv(csv_filename)
            gather_df = gather_df[gather_df['f_unique_weighted'] >= 0.1]
            if len(gather_df):
                last_row = gather_df.tail(1).squeeze()
                sum_weighted_found = last_row['sum_weighted_found'] 
                total_weighted_hashes = last_row['total_weighted_hashes']

                f_found = sum_weighted_found / total_weighted_hashes

                return render_template("sample_search.html",
                                       sig=ss,
                                       gather_df=gather_df,
                                       f_found=f_found)
            else:
                return "no matches found!"

        elif action == 'download':
            return "download me"

        # default
        sum_weighted_hashes = sum(ss.minhash.hashes.values())
        return render_template("sample_index.html", sig=ss,
                               sum_weighted_hashes=sum_weighted_hashes)
    else:
        return redirect(url_for('index'))

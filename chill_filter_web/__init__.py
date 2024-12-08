import os
from flask import Flask, flash, request, redirect, url_for
from flask import render_template
from werkzeug.utils import secure_filename
import sourmash
from sourmash_plugin_branchwater import sourmash_plugin_branchwater as branch
import pandas as pd

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
    if os.path.exists(outpath):
        ss = sourmash.load_file_as_index(outpath)
        ss = ss.select(moltype='DNA', ksize=51, scaled=100_000)
        if len(ss) == 1:
            ss = list(ss.signatures())[0]
            success = True

    if success:
        if action == 'search':
            status = branch.do_fastgather(outpath,
                                          'prepare-db/animals-and-gtdb.mf.csv',
                                          0,
                                          51,
                                          100_000,
                                          'DNA',
                                          'foo.csv',
                                          None)
            print('XXX', status)

            gather_df = pd.read_csv('foo.csv')
            if len(gather_df):
                last_row = gather_df.tail(1).squeeze()
                sum_weighted_found = last_row['sum_weighted_found'] 
                total_weighted_hashes = last_row['total_weighted_hashes']
                return(f"total ref k-mers found (abund): {sum_weighted_found / total_weighted_hashes * 100:.1f}%")
            else:
                return "no matches found!"

        return f"name: {ss.name}, len: {len(ss.minhash)}, {action}"
    else:
        return redirect(url_for('index'))

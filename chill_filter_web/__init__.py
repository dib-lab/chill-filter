import os
from flask import Flask, flash, request, redirect, url_for
from flask import render_template
from werkzeug.utils import secure_filename
import sourmash

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
                ss = ss.select(moltype='DNA', ksize=31, scaled=100_000)
                if len(ss) == 1:
                    success = True
                    ss = list(ss.signatures())[0]
                    md5 = ss.md5sum()
                    print('SUCCESS')
            except:
                pass
                
            if success:
                return redirect(url_for('index', md5=md5))
    return render_template("index.html")

#! /bin/bash
source ~/miniforge3/etc/profile.d/conda.sh
conda activate chill
mkdir -p logs
gunicorn -w 4 -b localhost:5000 chill_filter_web:app

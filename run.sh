#! /bin/bash
source ~/miniforge3/etc/profile.d/conda.sh
conda activate chill
python -m chill_filter_web -p 5000 --host 0.0.0.0

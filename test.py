import subprocess

result = subprocess.run(["cmd", "/c", "dir", "/b"], stdout=subprocess.PIPE, text=True)
print(result.stdout)

import numpy as np
import pandas as pd
import holoviews as hv
import os, glob
from IPython.display import Latex
from IPython.display import Image

hv.extension("bokeh")
s0=0
w = "results/w.sdds"


png = "results/image.png"
with open("machine.lte", "r") as f:
    print(f.read())

with open("track.ele", "r") as f:
    print(f.read())

if not os.path.exists("results/"): os.mkdir("results/")
# clear the "results" folder:
for f in glob.glob('results/*'): os.remove(f)

result = subprocess.run(["cmd", "/c", "elegant track.ele", "/b"], stdout=subprocess.PIPE, text=True)
print(result.stdout)
#sdds2stream "results/w1.sdds" -par=s
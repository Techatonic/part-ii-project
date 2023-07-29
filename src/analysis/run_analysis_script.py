import os
from argparse import ArgumentParser
import time
import numpy as np
import pandas as pd

parser = ArgumentParser("Analysis on Runtime of Event Scheduler")
parser.add_argument(
    "-n", required=True, type=int, help="Number of times to run the program"
)
parser.add_argument("--stmt", required=True, type=str, help="statement to execute")
args = None
try:
    args = parser.parse_args()
except:
    print("Invalid input")
    exit()

times = np.array([], dtype=float)

for run in range(args.n):
    start_time = time.time()
    os.system(args.stmt)
    times = np.append(times, time.time() - start_time)

df = pd.DataFrame(times)
print()
print(df.describe(percentiles=[0.05, 0.95]).transpose())

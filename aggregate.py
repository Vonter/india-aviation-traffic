import glob
import numpy as np
import os
import pandas as pd
import re

from utils import *
from domestic import *
from international import *

def dump_international():
    os.makedirs("aggregated/international", exist_ok=True)

    for table in ['1', '2', '3', '4']:
        international_table(table)

def dump_domestic():
    os.makedirs("aggregated/domestic", exist_ok=True)

    domestic_table_city()
    #domestic_table_carrier()

def dump():
    dump_international()
    dump_domestic()

dump()

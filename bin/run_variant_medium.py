#!/usr/bin/env python

import os
import sys
from pathlib import Path

# Add the src folder to Python module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import fire
from src.run import Hyperparams



def main():
    fire.Fire(Hyperparams)


if __name__ == "__main__":
    main()
#!/usr/bin/env python

import sys
from pathlib import Path

# Adds the parent folder (project root) to Python's module search path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import fire
from src.run import Hyperparams



def main():
    fire.Fire(Hyperparams)


if __name__ == "__main__":
    main()
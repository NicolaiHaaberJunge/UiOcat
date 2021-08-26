# UiOcat

* [General](#general-info)
* [Purpose](#purpose)
* [Installation](#installation)
* [How-To](#how-to)

## General

UiOcat is a python package to be used within the Jupyter environment for 
analysing and processing catalytic Time-On-Stream gas chromatography data.
Currently UiOcat is used at the section for catalysis at
the University of Oslo.

## Purpose

UiOcat was created to improve data analysis workflow and has been designed
to be easily extended with more advanced analysis or addition of new catalytic
test rigs.

## Installation

With a python environment configures (conda or pipenv), clone the repo and simply:

```
cd UiOcat
pip install .
```

## How-To

To perform an analysis the following workflow is to be used.

1. Import analysis, reactions, and instrument classes like:
```
from uiocat.analysis import GC_Analysis
from uiocat.reactions import Reaction
from uiocat.instrument import CoFeedRig, HighPressureRig
```
2. Define a reaction object.
```
mth = Reaction(reac='mth')
```
3. Choose a test rig instrument and load the reaction and raw GC data from your instrument (.csv file).
```
cofeed = CoFeedRig(data_file)
```
4. Choose the type of analysis and provide the reaction and instrument.
```
analysis = GC_Analysis(reaction=MTH, instrument=cofeed)
```

5. Finally you can visualize the analysis (requires iPywidgets) and export the results.
```
analysis.results()
analysis.export_to_excel()
```


from setuptools import setup, find_packages

VERSION = '1.0.0' 
DESCRIPTION = 'UiOcat'
LONG_DESCRIPTION = 'A python package for working with catalytic data in Jupyter Lab/Notebook'

# Setting up
setup(
       # the name must match the folder name 'verysimplemodule'
        name="uiocat", 
        version=VERSION,
        author="Nicolai Haaber Junge",
        author_email="<nicolai.junge@outlook.com>",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=['pandas', 'matplotlib', 'xlrd', 'ipywidgets'], # add any additional packages that 
        # needs to be installed along with your package. Eg: 'caer'
        
        keywords=['python', 'catalysis', 'UniversityOfOslo'],
        classifiers= [
            "Intended Audience :: Education",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows"
        ]
)
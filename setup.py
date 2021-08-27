from setuptools import setup, find_packages

VERSION = '1.0.0' 
DESCRIPTION = 'UiOcat'
LONG_DESCRIPTION = 'A python package for working with catalytic data in Jupyter Lab/Notebook'

# Setting up
setup(
        name="uiocat", 
        version=VERSION,
        author="Nicolai Haaber Junge",
        author_email="<nicolai.junge@outlook.com>",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=['pandas', 'matplotlib', 'xlrd', 'ipywidgets', 'ipympl'],
        
        keywords=['python', 'catalysis', 'UniversityOfOslo'],
        include_package_data=True,
        package_data={'': ['antoine_coef_lib/*.json', 'instrument_lib/*.json', 'reaction_lib/*.json']}

)
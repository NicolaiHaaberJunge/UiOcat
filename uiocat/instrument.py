""""
This is the instrument definition file for PyCat. Here we define the classes that reads instrument raw
data into a standardized data format. For most instruments this is a simple pandas Dataframe. The main
point is that the standardized data format should be the same for all instrument. That way 
the analysis class can be re-used. 
"""

import os
import json
import pandas as pd
import numpy as np
import datetime as dt
import xlrd
import pkg_resources

######################
# GC Instrument Class
# Here the GC instrument classes are defined. The structure builds on a parent class and subsequent sub classes.
######################

class GC_Instrument:
    ''''
    GC instrument parent class. This mainly adds som utility functions such as
    being able to add instrument configurations. Not strictly necessary currently
    but may be usefull in the future.
    '''

    def __init__(self, name='default', measurment_offset=0):
        """
        Inputs
        ------------
        name : instrument name (found in "instrument:lib/")
        measurment_offset : offset time from start of reactant gas feeding to start of GC sampling (minutes)
        """
        #self.instrument_libary_loc =  os.path.join(pathlib.Path(__file__).parent, 'instrument_lib')
        self.name = name  # name of the instrument
        self.instrument_config = self.fetch_instrument_config()  #  Fetches the instrument config
        self.measurment_offset = measurment_offset  # Sets the measurment offset

    def __str__(self):  
        return 'Instrument Loaded: {}'.format(self.name)  

    def fetch_instrument_config(self):
        """
        Fetches the instrument configurations such as response_factors etc.
        """
        stream = pkg_resources.resource_stream(__name__, 'instrument_lib\\{}.json'.format(self.name))

        try:
            return json.load(stream)
        except:
            raise AssertionError("Your reaction is not defined")


    def instrument_exists(self, name, directory):
        """
        check is the instrument from "name" exists in instrument_lib/
        """
        reaction_files = os.listdir(directory)
        if name + '.json' in reaction_files:
            return True
        else:
            raise Exception('Instrument does not exist')

class CoFeedRig(GC_Instrument):
    """
    The Co-Feed rig instrument. This only deals with GC data but the Cofeed rig also has MS data. See
    under MS_instruments.
    
    """
    def __init__(self, datafile, name='CoFeed', measurment_offset=0):
        """
        INPUTS
        -----------
        datafile : the raw data file path. (File as generated from OpenLab , .csv file)
        name : the name of the cofeed rig in instrument_lib/
        measurment_offset : offset time from start of reactant gas feeding to start of GC sampling (minutes)
        """
        # Loading reaction and instrument object
        GC_Instrument.__init__(self, name, measurment_offset)
        
        #Loading data
        self.datafile = datafile
        self.raw_data = self.read_gcdata()  # Processes the raw data and creates a standardized dataset.
        self.compounds = self.raw_data.columns.to_list()  # Returns a list of all integrated compounds
        self.tos = self.raw_data.index.to_list()  # Returns the "time-on-stream" data as a list.

    #####  Loading Data  #####
    def read_gcdata(self):
        """
        Method that reads the raw data from the CoFeed-rig and creates a standardized dataformat.
        """

        def convert_to_timestamp(times):
            """
            Function that convert the raw data time string to datetime timestamp.
            """
            new_times = []
            for i, val in enumerate(times):
                timestamp = val[:-3]
                date = dt.datetime.strptime(timestamp, "%Y%m%d %H%M%S")  # The format of the time string given by OpenLab.
                new_times.append(date.timestamp())

            new_times = np.array(new_times)
            new_times = (new_times - new_times[0])/3600  # Convert the times to hours.

            return np.round(new_times, 2)  # Rounding the times to 2 decimals.

        def _correct_for_responsfac(df, respons_factors):
            """
            functions that corrects the FID responds with the response factors.
            """
            for i in respons_factors:
                df[i] = df[i]/respons_factors[i]  # Divides each relevant compound with its response factor.
            return df

        
        compound_names = pd.read_csv(self.datafile, nrows=1, header=None).drop([0], axis=1).dropna(axis=1)  # The list of compounds
        df = pd.read_csv(self.datafile, skiprows=2, header=None, engine='python').fillna(0).drop([1, 2], axis=1)  # The raw data.
        df = df[df[0] !=0]  # Removing empty rows that does not contain any data
        df = df[:-2]  # Removing the last two rows which are information we don't need
        
        old_column_names = compound_names.values[0, :].tolist()
        old_column_names = [x.lower() for x in old_column_names]  # We force lower case on all compounds names.
        new_column_names = ['TOS'] + old_column_names  # Replacing column names
        df.columns = new_column_names

        df['TOS'] = convert_to_timestamp(df['TOS']) # Converting the time strings of the raw data to TOS in hours.

        if self.measurment_offset != 0:  #  If we assign a measurment offset it is added here to the TOS list.
            df['TOS'] += self.measurment_offset/60
                       
        df = _correct_for_responsfac(df, self.instrument_config['Response_Factors'])  # Here we correct for respons factors.
        
        df = df.round(decimals=2)  # We round the data to two decimals
        df.set_index('TOS', inplace=True)  # We set the dataframe index to be the TOS column. This makes data processing more convenient.
        return df  # returns processed and standardized GC data.

    
class HighPressureRig(GC_Instrument):
    """
    The high pressure rig instrument. Analogous to the CoFeed rig instrument defined above.
    The high pressure rig has two FID detectors and therefore has two data sets that needs
    to be processed and combined. This instrument method does exactly this and returns a dataframe
    which are identical to the CoFeed rig.
    
    """
    def __init__(self, data, name='HPR', measurment_offset=0):
        """
        INPUTS
        ----------
        data : A tuple or list which takes the file locations for the two FID datafiles.

        """

        # Loading reaction and instrument object
        GC_Instrument.__init__(self, name, measurment_offset)

        #  Loading data
        self.datafile = data[0]
        self.datafile_MFID = data[0]  # The Mid FID data
        self.datafile_BFID = data[1]  # The Back FID data
        self.raw_data = self.read_gcdata().round(decimals=2)  # Processing the raw data
        self.compounds = self.raw_data.columns.to_list()  # The list of compounds
        self.tos = self.raw_data.index.to_list() # Returns the "time-on-stream" data as a list.

    #####  Loading Data  #####
    def read_gcdata(self):
        """
        This is the data parser function which reads in the GC data.
        """
        def to_df(df):
            """
            This functions reads each loaded pandas and cleanes up the raw data.
            ---------------------
            INPUTS
            df : pandas dataframe with loaded raw data from excel file
            OUTPUTS
            df : cleaned dataframe
            """
            row_id_start = df.index[df.iloc[:, 0] == 'Array 1'][0]  # Finding the start of the data
            row_id_end = df.index[df.iloc[:, 0] == 'Mean'][0]  #  Finding the end of the data

            df  = df.iloc[row_id_start+1:row_id_end, 1:].reset_index(drop=True)  # Select data and remove index
            df.columns=df.iloc[0, :]  # Set the column names
            df.drop(index=0, inplace=True)  # removes the first column
            df.reset_index(drop=True, inplace=True)

            cols = df.columns.to_list()  # Get current columns
            c_new = [c for c in cols if c[0:4]!='Time']  # Build column name list with the correct name (remove all Time)

            df = df[c_new]  # Select correcte columns with Area
            df = df[df['Run Time'] > 20]  #  Remove bypass injections
            df.drop(columns=['Acquisition Method Name', 'Run Time'], inplace=True) # Remove unneeded columns

            cols = df.columns.to_list() 
            cc = [cols[i][5:].lower() if i < len(cols)-1 else cols[i] for i in range(len(cols)) ]  # Rename column headers with simpler names
            cc[0] = 'TOS'


            df.columns = cc  # New column header
    
            return df

        def join_FIDs(MFID, BFID):
            """
            Helper function that combines the data from the front and back FID.
            ---------------------
            INPUTS
            MFID : Dataframe with loaded Mid FID data
            BFID : Dataframe with loeaded Back FID data
            OUTPUTS
            df_combo : Merged dataframe containing the complete dataset
            """
        
            df_comb = pd.concat([MFID, BFID.iloc[:, 1:]], axis=1)
            df_comb['Total Area']= df_comb['Total Peak Area'].sum(axis=1)
            df_comb.drop(columns=['Total Peak Area'], inplace=True)
            df_comb = df_comb.reindex(index=df_comb.index[::-1]).reset_index(drop=True)


            df_comb['TOS'] = pd.to_datetime(df_comb.TOS, format="%d/%m/%Y %H:%M:%S")
            df_comb['TOS'] = np.round((df_comb['TOS'] - df_comb['TOS'][0])/np.timedelta64(1, 'h'), 2)
            df_comb.set_index('TOS', inplace=True)
            
            df_comb['aromatics'] = (df_comb.iloc[:, -1] - df_comb.iloc[:, :-1].sum(axis=1)).round(1)
            df_comb.drop(columns='Total Area', inplace=True)
            df_comb.fillna(0, inplace=True)
            df_comb[df_comb<0] = 0

            return df_comb

        def _correct_for_responsfac(df, respons_factors):
            """
            This function corrects the raw data for the GC respons factors
            """

            for i in respons_factors:
                df[i] = df[i]/respons_factors[i]
            return df

        wb1 = xlrd.open_workbook(self.datafile_MFID, logfile=open(os.devnull, 'w'))  #  This is needed to surpress annoying log messages
        wb2 = xlrd.open_workbook(self.datafile_BFID, logfile=open(os.devnull, 'w'))  #  This is needed to surpress annoying log messages

        df_MidFid = pd.read_excel(wb1)  # Reading the Mid FID datafile
        df_BackFid = pd.read_excel(wb2)  # Reading the Back FID datafile

        df_MFID = to_df(df_MidFid)  # Cleans the read dataframe
        df_BFID = to_df(df_BackFid)

        df_data = join_FIDs(df_MFID, df_BFID)  # Join the Mid and Back FID dataframes.

        df_data = _correct_for_responsfac(df_data, self.instrument_config['Response_Factors'])  # Correcting for respons factors.

        return df_data

###########################
# MS Instruments
###########################


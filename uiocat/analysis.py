"""
The analysis module  calculates relevant catalytic data
such as selectivity, conversion, and yield from processed instrument
data. It can also plot the data as interactive charts using iPywidgets and
return a dashboard with the plots. Lastly, the analysis can be saved to
a complete excel report including processed data, plots etc.

The structure of an analysis class is such that it takes two paramets. "Reaction"
and "Instrument". The "reaction" json object defined compounds are reactants and which
are products. The reactions are found in reaction_lib/ in json format. This allows one
to define alot of metadata to the reaction which can be used later. The "instrument" 
parameter takes an instrument objects generated with the instrument module of PyCat.

The analysis module contains:

1) GC data analysis 
    calculates
    - Conversion
    - Selectivity
    - Yield

"""

import pandas as pd
import numpy as np
import datetime as dt
import os

import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.ticker import MaxNLocator

import ipywidgets as widgets
from ipywidgets import Output, HBox, VBox
from IPython.display import display

####################
## GC data analysis
###################

class GC_Analysis:
    def __init__(self, reaction, instrument):
        """
        An analysis class for calculating catalytic data from instrument data processed with the instrument module in PyCat.
        """
        # Loading reaction and instrument object
        self.reaction = reaction  # A python object created with the reaction module of pycat. This holds the reaction metadata.
        self.instrument = instrument # A python object created with the instrument module of pycat. This holds the standardized raw data.
        
        # Loaded Data File
        self.data_file_dir = '\\'.join(instrument.datafile.split('\\')[:-1])  # This is the loaded data file path
        self.loaded_file = instrument.datafile.split('\\')[-1]  # Gives the name of the loaded data file


        # Calculation
        self.conversion = pd.DataFrame()  # Initiates an empty dataframe or return the conversion data after being computed
        self.give_yield = pd.DataFrame()
        self.give_selectivity = pd.DataFrame()

    ####################
    ## Computations
    ###################
    
    def area_sum(self):
        """"
        Calculates the carbon area sum to check that there is carbon balance throughout the GC injections.
        """
        df_area_sum =  pd.DataFrame(self.instrument.raw_data.sum(axis=1), columns=['area']).round(decimals=2)
        return df_area_sum
    
    def calc_conversion(self):
        """
        Calculates reaction conversion.
        """


        self.conversion = pd.DataFrame(100*(1 -self.instrument.raw_data[self.reaction.feed['compounds']].sum(axis=1)/self.instrument.raw_data.sum(axis=1)),
                                         columns=['conv']).round(decimals=2)  
        return self.conversion
    
    def calc_selectivity(self):
        """
        calculates reaction selectivity
        """
        if self.conversion is None: # If the conversion has not been calculated yet it is calculated.
            self.conversion = self.calc_conversion().round(decimals=2)

        df_selec = pd.DataFrame([])  # Created empty dataframe
        for i in self.reaction.reaction_compounds:
            percent_carbon = pd.DataFrame(self.instrument.raw_data[self.reaction.reaction_compounds[i]['compounds']].sum(axis=1)/self.instrument.raw_data.sum(axis=1), columns=[i])
            selectivity = pd.DataFrame(100*percent_carbon[i]/(self.conversion['conv']*1e-2), columns=[i])
            df_selec = pd.concat([df_selec, selectivity], axis=1)
        self.give_selectivity = df_selec.round(decimals=2)
        return  self.give_selectivity
    
    def calc_yield(self):
        """
        calculated the reaction yield.
        """
        df_yield = pd.DataFrame([])
        for i in self.reaction.reaction_compounds:
            percent_carbon = pd.DataFrame(100*self.instrument.raw_data[self.reaction.reaction_compounds[i]['compounds']].sum(axis=1)/self.instrument.raw_data.sum(axis=1), columns=[i])
            df_yield = pd.concat([df_yield, percent_carbon], axis=1)
        self.give_yield = df_yield.round(decimals=2)
        return self.give_yield


    ## Plotting Results     

    def results(self):
        """
        Function that plots the analysis results and returns an interactive dashboard with plots.
        """

        area_sum_output = widgets.Output()
        conv_output = widgets.Output()
        selc_output = widgets.Output()
        yield_output = widgets.Output()

        with area_sum_output:
            if self.instrument.raw_data.shape[0] == 1:
                bar_width = 0.05
            else: 
                bar_width = 0.4
            area_plot = self.area_sum().reset_index(drop=True).plot(kind='bar',legend=False, ylabel='Counts', xlabel='Injection No.',
                                                                        title='Area Sum', rot=0, width=bar_width)
            if self.instrument.raw_data.shape[0] > 20:
                area_plot.xaxis.set_major_locator(MaxNLocator(20))

        with conv_output:
                if self.instrument.raw_data.shape[0] == 1:
                    conversion_plot = self.calc_conversion().iloc[::1,:].plot(kind='bar', title='Conversion', 
                                                        legend=False, ylabel='Conversion (%)',
                                                        xlabel='TOS (h)', rot=0, width=0.05, ylim=(0, 100))
                else:
                    conversion_plot = self.calc_conversion().iloc[0::1,:].plot(ls="-", marker="o", title='Conversion', 
                                                        grid=True, legend=False, ylabel='Conversion (%)', ylim=(0, 105),
                                                        xlabel='TOS (h)')

        with selc_output:
            if self.instrument.raw_data.shape[0] == 1:
                plot_selec = self.calc_selectivity().plot(kind='bar', stacked=True, rot=0, width=0.05, title='Selectivity',
                                                        xlabel='TOS (h)',
                                                        ylabel='Selectivity. (%)')
            else:
                plot_selec = self.calc_selectivity().iloc[0::2,:].plot(ls="-", marker="<", ms=6,  grid=True, title='Selectivity',
                                                        xlabel='TOS (h)',
                                                        ylabel='Selectivity. (%)')
            plot_selec.set_ylim(0, 100)
        with yield_output:
            if self.instrument.raw_data.shape[0] == 1:  
                yield_plot = self.calc_yield().plot(kind='bar', stacked=True, rot=0, width=0.05,
                                                        ylabel='Yield (%)', xlabel='TOS (h)')
            else:
                yield_plot = self.calc_yield().iloc[0::2,:].plot(ls="-", marker="<", ms=6, title='Yield', grid=True,
                                                    ylabel='Yield (%)', xlabel='TOS (h)')
            
            yield_plot.set_ylim(0, 100)
            
        Row_1 = widgets.HBox([area_sum_output, conv_output])
        Row_2 = widgets.HBox([yield_output, selc_output])
        Main = widgets.VBox([Row_1, Row_2])
        
        return display(Main)


    ## Dump to excel

    def export_to_excel(self, out_name=None):
        """
        Methods which outputs the analysis as an excel report.
        """

        def create_chart(writer, workbook, df_name, df):

            worksheet = writer.sheets[df_name]

            nr_rows, nr_cols = df.shape
            chart = workbook.add_chart({'type': 'line'})

            cols_names = df.columns.to_list()

            for i in range(0, nr_cols):
                if i == 0:
                    pass
                chart.add_series({
                                    'name':       cols_names[i],
                                    'categories': [df_name, 1, 0, nr_rows, 0],
                                    'values':  [df_name, 1, i+1, nr_rows, i+1],
                                    'marker': {
                                                'type': 'square',
                                                'size': 5,
                                                'border': {'color': 'black'},
                                                }
                                })
            chart.set_x_axis({
                    'name': 'TOS (h)',
                    'min' : '0.00'
            })

            chart.set_y_axis({
                    'name': '{} (%)'.format(df_name)
            })

            chart.set_size({'x_scale': 1.5, 'y_scale': 2})

            worksheet.insert_chart('K2', chart)

            return

        def create_sheet(writer, df_name, df):
            df.to_excel(writer, sheet_name=df_name)
            return

        if out_name is None:
            report_default_name = 'analysis-{0}.xlsx'.format(dt.datetime.now().strftime("%Y-%m-%d_%H%M%S"))
            out_name = os.path.join(self.data_file_dir, report_default_name)
        
        data = {
            'Raw Data' : self.instrument.raw_data,
            'Conversion' : self.conversion,
            'Yield' : self.give_yield,
            'Selectivity' : self.give_selectivity
        }
        
        valid_data = [i for i in data if not data[i].empty]

        
        writer = pd.ExcelWriter(out_name, engine='xlsxwriter')
        workbook = writer.book

        for i, name in enumerate(valid_data):
            create_sheet(writer, name, data[name])
            if i > 0:
                create_chart(writer, workbook, name, data[name])

        writer.save()

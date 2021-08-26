""""
The reaction module is used to define reaction parameters and reaction compounds.This
is needed for the PyCat analysis module. Ideally this should also be used for MS instruments.
"""

import os
import json
import pandas as pd
import ipywidgets as widgets
from ipywidgets import Output, HBox, VBox, fixed, interactive, FloatSlider, Layout, Label
from IPython.display import display


class Reaction:

    def __init__(self, reac='empty'):
        """
        INPUTS:

        """
        self.type = reac
        self.reaction_libary_loc = r'pycat\reaction_lib'
        self.reaction = self.fetch_reaction_compounds()
        self.feed = self.reaction['feed'] # The feed compounds of the reaction (reactants)
        self.reaction_compounds = self.reaction['products'] # The reaction compounds (products).

    def __str__(self):
        return 'Reaction: {}, Feed: {}'.format(self.type, ', '.join(self.feed))

    def fetch_reaction_compounds(self):

        if self.reaction_exists(self.type, self.reaction_libary_loc):  # Checks if the reaction name exists
            json_file = os.path.join(self.reaction_libary_loc, self.type +'.json')
            with open(json_file) as js_data: 
                reacton_dict = json.load(js_data) 
                return reacton_dict  # returns the json reaction file as a python dictionary.
        else:
            raise Exception("Your reaction is not defined") 

    def reaction_to_lib(self, name=None, reaction_dict=None): 
        """
        This method can add a new reaction to the reaction_lib/. It takes a reaction name and a
        python dictionary.
        """
        
        self.type = name  # Name of the reaction
        reaction_to_store = os.path.join(self.reaction_libary_loc, self.type +'.json')  # The python dictionary with reaction parameters.

        if self.reaction_exists(name, self.reaction_libary_loc):
            raise Exception('Reaction already exists.')
        else:
            with open(reaction_to_store, 'w') as fp:
                json.dump(reaction_dict, fp)

            self.reaction_compounds = reaction_dict

            return self.type

    def reaction_exists(self, name, directory):
        """
        Checks if the reactions already exists before adding it to reaction_lib/
        """
        reaction_files = os.listdir(directory)
        if name + '.json' in reaction_files:
            return True


###################
# Class to calculate reaction parameters for planning an MTH reaction.
####################

class ReactionSetup:
    """
    Class which returns an interactive dashboard for quickly calculating WHSV and Flow rates.
    """
    __path_to_antoine_lib = r'pycat\antoine_coef_lib\antoine_coef.json'

    Psat_vapour = 0
    F_HeToTank = 0
    F_comp = 0

    def __init__(self):

        self.calculator()
        return

    def __str__(self):
        print('Tool for setting up reactions with liquid feed')

    def calculator(self):
        df = pd.read_json(self.__path_to_antoine_lib).round(3)
        self.data = df
        compounds = df.index.to_list()

        AntoineEq = lambda A, B, C, T: 10**(A-B/(T+C))*1013.25/760

        ### INPUT WIDGETS:

        style_input = {'description_width': '140px'}
        layout_output = Layout(width='230px', height='37px')
        loc = widgets.Select(
                        options=compounds,
                        description='Compounds',
                        disabled=False,
                        layout=Layout(width='350px', height='150px'),
                        style={'description_width': '120px'}
                    )

        Tset= widgets.FloatText(value=37.0, description='Temperature (Celsius)', disabled=False, style=style_input, layout=layout_output)
        TotFlow = widgets.FloatText(value=26.0, description='Flow (ml/min)', disabled=False, style=style_input,  layout=layout_output)
        DiluentMass = widgets.FloatText(value=0.0, description='Diluent (mg)', disabled=False, style=style_input,  layout=layout_output)
        CatalystMass = widgets.FloatText(value=210.0, description='Catalyst Mass (mg)', disabled=False, style=style_input, layout=layout_output)
        
        InputLabel = widgets.Label('Test')


        inputWidgets = VBox([Tset, TotFlow, DiluentMass, CatalystMass])
        InputMain = VBox([InputLabel, HBox([loc, inputWidgets])], layout=Layout(justify_content='center'))

        ### OUTPUT WIDGETS

        style_output = {'description_width': '120px'}
        layout_ouput = Layout(width='250px', height='30px')

        PsatWidget = widgets.FloatText(value=0.0, description='Psat (mbar)', disabled=False, style=style_output, layout=layout_ouput)
        F_HeToTank = widgets.FloatText(value=0.0, description='HeToTank (ml/min)', disabled=False, style=style_output, layout=layout_ouput)
        F_comp = widgets.FloatText(value=0.0, description='Net Reac. flow (ml/min)', disabled=False, style=style_output, layout=layout_ouput)

        F_mass = widgets.FloatText(value=0.0, description='Net. mass. flow (g/h)', disabled=False, style=style_output, layout=layout_ouput)

        space_velocity = widgets.FloatText(value=0.0, description='WHSV (1/h)', disabled=False, style=style_output, layout=layout_ouput)
        contact_time = widgets.FloatText(value=0.0, description='Contact Time (min)', disabled=False, style=style_output, layout=layout_ouput)

        Veloc = VBox([space_velocity, contact_time])
        Output_Flows = VBox([PsatWidget, F_HeToTank, F_comp, F_mass])
        OutputMain = HBox([Output_Flows, Veloc])

        ## EVENT HANDLER
        output = widgets.Output()

        def on_value_change(change):
            A, B, C = df.loc[loc.value][1:-3]
            PsatWidget.value = round(AntoineEq(A, B, C, Tset.value), 5)
            F_HeToTank.value = round((1000-PsatWidget.value)/1000*TotFlow.value, 5)
            F_comp.value = round((TotFlow.value - F_HeToTank.value), 5)
            F_mass.value = round(0.987*F_comp.value*60*df.loc[loc.value][-1]/(0.082*1000*298), 5)

            space_velocity.value = round(1000*F_mass.value/(CatalystMass.value), 5)
            contact_time.value = round(space_velocity.value**-1*60, 5)

        def on_Flow_change(change):
            F_HeToTank.value = round((1000-PsatWidget.value)/1000*TotFlow.value, 5)
            F_comp.value = round(TotFlow.value - F_HeToTank.value, 5)
            F_mass.value = round(0.987*F_comp.value*60*df.loc[loc.value][-1]/(0.082*1000*298), 5)
            space_velocity.value = round(1000*F_mass.value/(CatalystMass.value), 5)
            contact_time.value = round(space_velocity.value**-1*60, 5)

        def on_CatalystMass_change(change):
            space_velocity.value = round(1000*F_mass.value/(CatalystMass.value), 5)
            contact_time.value = round(space_velocity.value**-1*60, 5)
            pass

        ## CALLBACKS
        loc.observe(on_value_change, names='value')
        Tset.observe(on_value_change, names='value')
        TotFlow.observe(on_Flow_change, names='value')
        CatalystMass.observe(on_CatalystMass_change, names='value')

        ## DISPLAY
        display(InputMain)
        display(OutputMain)
        display(output)
        return 
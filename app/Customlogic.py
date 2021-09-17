"""
    FeatureCloud Template

    Copyright 2021 Mohammad Bakhtiari. All Rights Reserved.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""
from .logic import AppLogic, bcolors
import bios
import os


class CustomLogic(AppLogic):
    """ Subclassing AppLogic for overriding specific methods
        to implement the deep learning application.

    Attributes
    ----------
    parameters: dict
    workflows_states: dict

    Methods
    -------
    init_state()
    read_input()
    final_step()
    write_results():
    """

    def __init__(self):
        super(CustomLogic, self).__init__()

        # Shared parameters and data
        self.results = {}

        # Define States
        self.states = {"Initializing": self.init_state,
                       "Wait for Results": self.wait_for_data,
                       "Read Input": None,
                       "Calculate Mean": None,
                       "Writing Results": None,
                       "Finishing": self.final_step
                       }

        self.current_state = 'Initializing'

    def init_state(self):
        if self.id is not None:  # Test if setup has happened already
            self.current_state = "Read Input"

    def wait_for_data(self):
        self.progress = 'wait for results from server'
        decoded_data = self.wait_for_server()
        if decoded_data is not None:
            print(f"{bcolors.SEND_RECEIVE} Received results from coordinator. {bcolors.ENDC}")
            self.results = decoded_data[0]
            self.current_state = "Writing Results"

    def read_input(self):
        if self.coordinator:
            self.current_state = "Calculate Mean"
        else:
            self.current_state = "Wait for Results"

    def average(self):
        self.broadcast(self.results)
        self.current_state = "Writing Results"

    def write_results(self):
        if self.coordinator:
            self.data_incoming.append('DONE')
            self.current_state = "Finishing"
        else:
            self.data_outgoing = 'DONE'
            self.modify_status(available=True, finished=True)

    def final_step(self):
        self.progress = 'finishing...'
        if len(self.data_incoming) == len(self.clients):
            self.modify_status(finished=True)

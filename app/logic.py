"""
    FeatureCloud Template
    mohammad.bakhtiari@uni-hamburg.de
"""
import copy
import threading
import time
import os
import shutil
import bios

import jsonpickle
import jsonpickle.ext.numpy as jsonpickle_numpy
import jsonpickle.ext.pandas as jsonpickle_pd
import json

jsonpickle_numpy.register_handlers()
jsonpickle_pd.register_handlers()


class AppLogic:
    """ Implementing the workflow for FeatureCloud platform

    Attributes
    ----------
    default_status: dict
    status: dict
    id: int
    coordinator: bool
    clients: list
    data_incoming: list
    data_outgoing: list
    thread:
    iteration: int
    progress: str
    INPUT_DIR: str
    OUTPUT_DIR: str
    mode: str
    dir: str
    splits: set
    test_splits: dict
    states: dict
    current_state: str

    Methods
    -------
    handle_setup(client_id, coordinator, clients)
    handle_incoming(data)
    handle_outgoing()
    app_flow()
    send_to_server(data_to_send)
    wait_for_server()
    broadcast(data)
    lazy_initialization(mode, dir)
    """

    def __init__(self):

        # === Status of this app instance ===
        self.default_status = {"available": False,
                               "finished": False,
                               "message": None,
                               "progress": None,
                               "state": "running",
                               "destination": None,
                               "smpc": {"operation": "add",
                                        "serialization": "json",
                                        "shards": 0,
                                        "range": 0}}
        self.status = copy.deepcopy(self.default_status)

        # By default SMPC will not be used for communications unless been ask for.
        self.disable_smpc()
        self.smpc_used = False
        self.smpc_required = False

        # === Parameters set during setup ===
        self.id = None
        self.coordinator = None
        self.clients = None

        # === Data ===
        self.data_incoming = []
        self.data_outgoing = None

        # === Internals ===
        self.thread = None
        self.iteration = 0
        self.progress = 'not started yet'

        # === App config Attributes ===
        self.INPUT_DIR = "/mnt/input"
        self.OUTPUT_DIR = "/mnt/output"

        self.config_file = {}
        self.mode = None
        self.dir = None
        self.splits = set()
        self.input_files = {}
        self.output_files = {}

        # === App States ===
        self.states = {}
        self.current_state = None

    def handle_setup(self, client_id, coordinator, clients):
        """ Is called once upon startup and contains information about the execution context of this instance

        Parameters
        ----------
        client_id: int
        coordinator: bool
        clients: list

        """
        self.id = client_id
        self.coordinator = coordinator
        self.clients = clients
        print(f'Received setup: {self.id} {self.coordinator} {self.clients}', flush=True)

        self.thread = threading.Thread(target=self.app_flow)
        self.thread.start()

    def handle_incoming(self, data):
        """ Is called when new data arrives

        """
        print("Process incoming data....")
        self.data_incoming.append(data.read())

    def handle_outgoing(self):
        """ Is called when data is requested

        """
        print("Process outgoing data...")
        self.modify_status(available=False)
        if not self.coordinator:
            self.disable_smpc()
        return self.data_outgoing

    def app_flow(self):
        """ Runs the state machine for FeatureCloud clients
            Reports Current states and transition between them
            And executes state functions

        """
        print(f"{bcolors.STATE}States:{bcolors.ENDC}")
        for i, state in enumerate(self.states):
            print(f"{bcolors.STATE}{i}: {state}{bcolors.ENDC}")

        # Initial state
        self.progress = 'initializing...'
        previous_states = [self.current_state]
        last_iteration = self.iteration
        while True:
            # print the executed states
            if last_iteration < self.iteration:
                previous_states = [self.current_state]
            if self.current_state != previous_states[-1]:
                previous_states.append(self.current_state)
                msg = f"{self.iteration}'th Iteration:\n"
                if len(previous_states) < 5:
                    for state in previous_states:
                        msg += state + "$#@"
                else:
                    msg = "... "
                    for state in previous_states[-5:]:
                        msg += state + "$#@"
                print(f"{bcolors.STATE}{msg[:-3].strip().replace('$#@', ' ---> ')}{bcolors.ENDC}")
                print(f"{bcolors.STATE}Current State: {self.current_state}{bcolors.ENDC}")

            # execute the step
            self.states[self.current_state]()

            if self.status["finished"]:
                break

            time.sleep(1)

    def send_to_coordinator(self, data_to_send):
        """  Is called only for clients
            to send their parameters or local statistics for the coordinator

        Parameters
        ----------
        data_to_send: list

        """

        data_to_send = json.dumps(data_to_send) if self.smpc_used else jsonpickle.encode(data_to_send)
        if not self.smpc_used and self.coordinator:
            self.data_incoming.append(data_to_send)
        else:
            self.data_outgoing = data_to_send
            self.modify_status(available=True)
            print(f'{bcolors.SEND_RECEIVE} [CLIENT] Sending data to coordinator. {bcolors.ENDC}', flush=True)

    def get_clients_data(self):
        """ Will be called only for the coordinator
            to get all the clients parameters or statistics.
            For each split, corresponding clients' data will be yield back.

        Returns
        -------
        clients_data: list
        split: str
        """
        print(f"{bcolors.SEND_RECEIVE} Received data of all clients. {bcolors.ENDC}")
        if self.is_received_data_aggregated():
            data = jsonpickle.decode(self.data_incoming[0])
            self.data_incoming = []
            for i, split in enumerate(self.splits):
                print(f'{bcolors.SPLIT} Get {split} {bcolors.ENDC}')
                yield data[i], split
            self.disable_smpc()
        else:
            data = [jsonpickle.decode(client_data) for client_data in self.data_incoming]
            self.data_incoming = []
            for i, split in enumerate(self.splits):
                print(f'{bcolors.SPLIT} Get {split} {bcolors.ENDC}')
                clients_data = []
                for client in data:
                    clients_data.append(client[i])
                yield clients_data, split

    def wait_for_coordinator(self):
        """ Will be called only for clients
            to wait for server to get
            some globally shared data.

        Returns
        -------
        None or list
            in case no data received None will be returned
            to signal the state!
        """
        if len(self.data_incoming) > 0:
            if len(self.data_incoming) == 1:
                data_decoded = jsonpickle.decode(self.data_incoming[0])
            else:
                data_decoded = jsonpickle.decode(self.data_incoming)
            self.data_incoming = []
            return data_decoded
        return None

    def broadcast(self, data):
        """ will be called only for the coordinator after
            providing data that should be broadcast to clients

        Parameters
        ----------
        data: list

        """
        data_to_broadcast = jsonpickle.encode(data)
        self.data_outgoing = data_to_broadcast
        self.modify_status(available=True)
        print(f'{bcolors.SEND_RECEIVE} [COORDINATOR] Broadcasting data to clients. {bcolors.ENDC}', flush=True)

    def finalize_config(self):
        """

        Returns
        -------

        """
        if self.mode == "directory":
            splits = [f.path for f in os.scandir(f'{self.INPUT_DIR}/{self.dir}') if f.is_dir()]
        else:
            splits = [self.INPUT_DIR, ]
        self.splits = set(sorted(splits))
        print(f"{bcolors.SPLIT} Splits order:")
        for i, split in enumerate(self.splits):
            print(f"Split {i}: {split}")
        self.input_files = {k: set([f"{split}/{v}" for split in self.splits])
                            for k, v in self.config_file['local_datasets'].items()}
        self.output_files = {k: set([f"{split.replace('/input', '/output')}/{v}" for split in self.splits])
                             for k, v in self.config_file['results'].items()}

        for split in self.splits:
            os.makedirs(split.replace("/input", "/output"), exist_ok=True)
        shutil.copyfile(self.INPUT_DIR + '/config.yml', self.OUTPUT_DIR + '/config.yml')

    def read_config(self, app_name):
        """ Read Config file

        Parameters
        ----------
        app_name: string
            path to the config.yaml file!

        """
        self.config_file = bios.read(f"{self.INPUT_DIR}/config.yml")[app_name]
        if 'logic' in self.config_file:
            self.mode = self.config_file['logic']['mode']
            self.dir = self.config_file['logic']['dir']
        else:
            print(f"{bcolors.WARNING}There are no 'logic' options in 'config.yml' file!\n"
                  f"default values will be used:\n"
                  f"mod: 'file'\n"
                  f"dir: '.'{bcolors.ENDC}")
            self.mode = 'file'
            self.dir = '.'
        if 'smpc_required' in self.config_file:
            self.smpc_required = self.config_file['smpc_required']
        else:
            print(f"{bcolors.WARNING}There is no 'smpc_required' option in 'config.yml' file!\n"
                  f"By default SMPC will not be used{bcolors.ENDC}")
        self.finalize_config()

    def is_clients_data_arrived(self):
        if self.smpc_used:
            if len(self.splits) == 1:
                return len(self.data_incoming) > 0
            return len(self.data_incoming) == len(self.splits)
        else:
            return len(self.data_incoming) == len(self.clients)

    def enable_smpc(self):
        self.status['smpc'] = copy.deepcopy(self.default_status['smpc'])
        self.smpc_used = True

    def disable_smpc(self):
        self.status['smpc'] = None
        self.smpc_used = False

    def modify_status(self, available=None, finished=False, message=None, progress=None, state=None,
                      destination=None, smpc=None):
        if available is not None:
            self.status["available"] = available
        if finished is not None:
            self.status["finished"] = finished
        if message is not None:
            self.status["message"] = message
        if progress is not None:
            self.status["progress"] = progress
        if state is not None:
            self.status["state"] = state
        if destination is not None:
            self.status["destination"] = destination
        if smpc is not None:
            self.status["smpc"] = smpc

    def make_smpc_setting(self, operation=None, serialization=None, shards=None, smpc_range=None):
        smpc = self.default_status["smpc"]
        if operation is not None:
            smpc["operation"] = operation
        if serialization is not None:
            smpc["serialization"] = serialization
        if shards is not None:
            smpc["shards"] = shards
        if smpc_range is not None:
            smpc["range"] = smpc_range
        return smpc

    def is_received_data_aggregated(self):
        return self.smpc_used


class TextColor:
    def __init__(self, color):
        if color:
            self.SEND_RECEIVE = '\033[95m'
            self.STATE = '\033[94m'
            self.SPLIT = '\033[96m'
            self.VALUE = '\033[92m'
            self.WARNING = '\033[93m'
            self.FAIL = '\033[91m'
            self.ENDC = '\033[0m'
            self.BOLD = '\033[1m'
            self.UNDERLINE = '\033[4m'
        else:
            self.SEND_RECEIVE = ''
            self.STATE = ''
            self.SPLIT = ''
            self.VALUE = ''
            self.WARNING = ''
            self.FAIL = ''
            self.ENDC = ''
            self.BOLD = ''
            self.UNDERLINE = ''


bcolors = TextColor(color=False)

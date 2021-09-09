# FeatureCloud Template
### Implementing FeatureCloud Applications

FeatureCloud provide an advantageous platform which is accessible at [FeatureCloud.ai](https://featurecloud.ai/) 

With FeatureCloud Template you can implement your application in an OO fashion. 
This template is consist of three main classes to interacting with FC Controller
and implement the app level tasks. Generally, two types of clients are used in FeatureCloud Template:
- Client: Every participant in the FeatureCloud platform is considered as a client, that should perform local tasks and
 communicate it some intermediary results with coordinator. No raw data are supposed to be exchanged among clients, and the coordinator.
- Coordinator: which is just one of the clients, that can receive clients results, aggregate, and broadcast it.



## AppLogic
Using the `AppLogic` class, users can define different states and make a flow to move from one to another.
Each state, should be added to the `self.states` attributes, while there is no predefined order for executing states, 
the flow direction will be handled using `CustomLogic` class. `self.state` keep track of current state, which helps developer
to know where is the flow currently and which state they desire to move in.

### Attributes
We categorize attributes in the `AppLogic` class as follows:
- Controlling the flow:
  - `states`: Python dictionary that keeps names of states, as keys, and methods, as values.
  - `current_state` Name of current state that should be changed to move to the next state.
  - `status_available`: Boolean attribute to signal the availability of data to the FeatureCloud Controller to share it. 
  - `status_finished`: Boolean variable to signal the end of app's execution to the FeatureCloud Controller.
  - `thread`:
  - `iteration`: Number of executed iterations
  - `progress`: Short descriptor of internal progress of app instance for the FeatureCloud Controller.
- General 
  - `id`: ID of each participant, regardless of being client or coordinator.
  - `coordinator`: Boolean flag indicating whether the running container is a coordinator or not.
  - `clients`: Contains IDs of all participating clients.
- Data management:
  - For communicating data:
    - `data_incoming`: list of data that received.
    - `data_outgoing`: list of data that should be shared.
  - For I/O from the docker container:
    - `INPUT_DIR`: path to the directory inside the docker container for reading the input files.
    - `OUTPUT_DIR`: path to the directory inside the docker container for writing the results.
    - `mode`: primarily used for indicating whether input files are stored in one folder or multiple folders.
    - `dir`: the folder containing the input files. 
    - `splits`: a set of possible splits(folder names, containing the input data, that are used for training) 
  
### Methods
Developers can use to initialize some attributes in an arbitrary time. `app_flow` is the main method in `AppLogic` class that contains a state machine for the client and the coordinator. 
It calls corresponding methods to each state. There four methods in `AppLogic` class that facilitate communicating data between coordinator and clients.

- `send_to_server`: should be called only for clients to send their data to the coordinator.
- `get_clients_data`: Should be called only for the coordinator to wait for the clients until receiving their data.
  For each split, corresponding clients' data will be yield back.
- `wait_for_server`: Should be called only for clients to wait for coordinator until receiving broadcasted data.
- `broadcast`: should be called only for the coordinator to broadcast same date to all clients.


## CustomLogic
is an extension class of `AppLogic`, which defines all the states, determines the first state, and more importantly, 
implements the flow between states. Beside the controlling of the flow, generally, we categorize states's tasks as
operational and/or communicational. For communicational states, which are responsible to share or receive data,
the method will be fully implemented and assigned to the state in `CustomLogic` class. For others, only the flow 
related part will be implemented here, and the operation happens in `CustomApp` class. All the data related
attributes that should be shared among clients should be introduced in `CustomLogic`.  
 
### Attributes
- `parameters`: A dictionary that can contain any data that should be shared.
- `workflows_states`: A dictionary that can signal any messages to the coordinator or vice versa.

### Methods
Methods are highly diverse regrading the target application, however, almost every application
should include initializing and finalizing state and method. 
- `init_state`
- `read_input`
- `final_step`

## CustomApp
`CustomApp` is an extension of `CustomLogic` that introduces all the required attributes and methods
to carrying on the app's task. For handling the flow between states, each state's method should call
its corresponding super class method in `CustomLogic`, that was previously implemented.

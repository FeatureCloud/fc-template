# FeatureCloud Template
### Implement FeatureCloud Applications

FeatureCloud provide an advantageous platform which is accessible at featurecloud.ai 

With FeatureCloud Template you can implement your application in an OO fashion. 
This template is consist of three main classes to interacting with FC Controller
and implement the app level tasks. Generally, two types of clients are used in FeatureCloud Template:
- Client: Every participant in the FeatureCloud platform is considered as a client, that should perform local tasks and
 communicate it some intermediary results with coordinator. No raw data are supposed to be exchanged among clients, and the coordinator.
- Coordinator: which is just one of the clients, that can recieve clients results, aggregate, and broadcast it.



## AppLogic
Using the `AppLogic` class, users can define different states and make a flow to move from one to another.
Each state, should be added to the `self.states` attributes, while there is no predefined order for executing states, 
the flow direction will be handled using `CustomLogic` class. `self.state` keep track of current state, which helps developer
to know where is the flow currently and which state they desire to move in.

###Attributes
We categorize attributes in the `AppLogic` class as follows:
- Controlling the flow:
  - `self.states`: Python dictionary that keeps names of states, as keys, and methods, as values.
  - `self.current_state` Name of current state that should be changed to move to the next state.
  - `status_available`: Boolean attribute to signal the availability of data to the FeatureCloud Controller to share it. 
  - `status_finished`: Boolean variable to signal the end of app's execution to the FeatureCloud Controller.
  - `thread`:
  - `iteration`: Number of executed iterations
  - `progress`: Short descriptor of internal progress of app instance for the FeatureCloud Controller.
- General 
  - `id`: ID of each participant, regardless of being client or coordinator.
  - `coordinator`: Boolean flag indicating whether the running image is a coordinator or not.
  - `clients`: Contains IDs of all participating clients.
- Data management:
  - For communicating data:
    - `data_incoming`: list of data that received.
    - `data_outgoing`: list of data that should be shared.
  - For I/O from the docker image:
    - `INPUT_DIR`: path to the directory inside the docker image for reading the input files.
    - `OUTPUT_DIR`: path to the directory inside the docker image for writing the results.
    - `mode`: primarily used for indicating whether input files are stored in one folder or multiple folders.
    - `dir`: the folder containing the input files. 
    - `splits`: a set of possible splits(folder names, containing the input data, that are used for training) 
  
###Methods
Developers can use to initialize some attributes in an arbitrary time. `app_flow` is the main method in `AppLogic` class that contains a state machine for the client and the coordinator. 
It calls corresponding methods to each state. There four methods in `AppLogic` class that facilitate communicating data between coordinator and clients.

- `send_to_server`: should be called only for clients to send their data to the coordinator.
- `get_clients_data`: Should be called only for the coordinator to wait for the clients until receiving their data.
  For each split, corresponding clients' data will be yield back.
- `wait_for_server`: Should be called only for clients to wait for coordinator until receiving broadcasted data.
- `broadcast`: should be called only for the coordinator to broadcast same date to all clients.



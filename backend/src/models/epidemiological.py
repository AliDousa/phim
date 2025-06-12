"""
Epidemiological models for disease spread simulation and analysis.
"""

import numpy as np
from scipy.integrate import odeint
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json


@dataclass
class SEIRParameters:
    """Parameters for SEIR epidemiological model."""
    beta: float  # Transmission rate
    sigma: float  # Incubation rate (1/incubation_period)
    gamma: float  # Recovery rate (1/infectious_period)
    mu: float = 0.0  # Birth/death rate
    population: int = 100000  # Total population


@dataclass
class ModelResults:
    """Results from epidemiological model simulation."""
    time: np.ndarray
    susceptible: np.ndarray
    exposed: np.ndarray
    infectious: np.ndarray
    recovered: np.ndarray
    parameters: Dict


class SEIRModel:
    """
    SEIR (Susceptible-Exposed-Infectious-Recovered) epidemiological model.
    
    This model simulates disease spread through a population with four compartments:
    - S: Susceptible individuals
    - E: Exposed (infected but not yet infectious)
    - I: Infectious individuals
    - R: Recovered (immune) individuals
    """
    
    def __init__(self, parameters: SEIRParameters):
        self.parameters = parameters
    
    def _seir_equations(self, y: List[float], t: float) -> List[float]:
        """
        SEIR differential equations.
        
        Args:
            y: Current state [S, E, I, R]
            t: Current time
            
        Returns:
            Derivatives [dS/dt, dE/dt, dI/dt, dR/dt]
        """
        S, E, I, R = y
        N = self.parameters.population
        
        # Calculate derivatives
        dSdt = self.parameters.mu * N - self.parameters.beta * S * I / N - self.parameters.mu * S
        dEdt = self.parameters.beta * S * I / N - self.parameters.sigma * E - self.parameters.mu * E
        dIdt = self.parameters.sigma * E - self.parameters.gamma * I - self.parameters.mu * I
        dRdt = self.parameters.gamma * I - self.parameters.mu * R
        
        return [dSdt, dEdt, dIdt, dRdt]
    
    def simulate(self, 
                 initial_conditions: Dict[str, int],
                 time_points: np.ndarray) -> ModelResults:
        """
        Run SEIR model simulation.
        
        Args:
            initial_conditions: Initial values for S, E, I, R
            time_points: Array of time points for simulation
            
        Returns:
            ModelResults object with simulation results
        """
        # Set initial conditions
        y0 = [
            initial_conditions.get('S', self.parameters.population - 1),
            initial_conditions.get('E', 0),
            initial_conditions.get('I', 1),
            initial_conditions.get('R', 0)
        ]
        
        # Solve differential equations
        solution = odeint(self._seir_equations, y0, time_points)
        
        return ModelResults(
            time=time_points,
            susceptible=solution[:, 0],
            exposed=solution[:, 1],
            infectious=solution[:, 2],
            recovered=solution[:, 3],
            parameters=self.parameters.__dict__
        )
    
    def calculate_r0(self) -> float:
        """
        Calculate basic reproduction number R0.
        
        Returns:
            R0 value
        """
        return self.parameters.beta / (self.parameters.gamma + self.parameters.mu)
    
    def calculate_peak_infection(self, 
                                initial_conditions: Dict[str, int],
                                max_time: float = 365) -> Tuple[float, float]:
        """
        Calculate peak infection time and value.
        
        Args:
            initial_conditions: Initial conditions for simulation
            max_time: Maximum time to simulate
            
        Returns:
            Tuple of (peak_time, peak_infections)
        """
        time_points = np.linspace(0, max_time, int(max_time * 10))
        results = self.simulate(initial_conditions, time_points)
        
        peak_idx = np.argmax(results.infectious)
        peak_time = results.time[peak_idx]
        peak_infections = results.infectious[peak_idx]
        
        return peak_time, peak_infections


class AgentBasedModel:
    """
    Agent-based model for disease spread simulation.
    
    This model simulates individual agents and their interactions
    to model disease transmission at a more granular level.
    """
    
    def __init__(self, 
                 population_size: int,
                 transmission_probability: float,
                 recovery_time: int,
                 incubation_time: int):
        self.population_size = population_size
        self.transmission_probability = transmission_probability
        self.recovery_time = recovery_time
        self.incubation_time = incubation_time
        self.agents = self._initialize_agents()
    
    def _initialize_agents(self) -> List[Dict]:
        """Initialize agent population."""
        agents = []
        for i in range(self.population_size):
            agent = {
                'id': i,
                'state': 'S',  # S, E, I, R
                'infection_time': 0,
                'contacts': []
            }
            agents.append(agent)
        
        # Set patient zero
        if agents:
            agents[0]['state'] = 'I'
        
        return agents
    
    def _generate_contacts(self, num_contacts: int = 5) -> None:
        """Generate random contacts between agents."""
        for agent in self.agents:
            # Random contacts per day
            contacts = np.random.choice(
                range(self.population_size), 
                size=min(num_contacts, self.population_size - 1),
                replace=False
            )
            agent['contacts'] = [c for c in contacts if c != agent['id']]
    
    def simulate_step(self) -> Dict[str, int]:
        """
        Simulate one time step of the model.
        
        Returns:
            Current state counts
        """
        self._generate_contacts()
        
        new_infections = []
        state_transitions = []
        
        for agent in self.agents:
            if agent['state'] == 'I':
                # Infectious agent can transmit to contacts
                for contact_id in agent['contacts']:
                    contact = self.agents[contact_id]
                    if (contact['state'] == 'S' and 
                        np.random.random() < self.transmission_probability):
                        new_infections.append(contact_id)
                
                # Check for recovery
                agent['infection_time'] += 1
                if agent['infection_time'] >= self.recovery_time:
                    state_transitions.append((agent['id'], 'R'))
            
            elif agent['state'] == 'E':
                # Exposed agent may become infectious
                agent['infection_time'] += 1
                if agent['infection_time'] >= self.incubation_time:
                    state_transitions.append((agent['id'], 'I'))
        
        # Apply new infections
        for agent_id in new_infections:
            self.agents[agent_id]['state'] = 'E'
            self.agents[agent_id]['infection_time'] = 0
        
        # Apply state transitions
        for agent_id, new_state in state_transitions:
            self.agents[agent_id]['state'] = new_state
            if new_state == 'I':
                self.agents[agent_id]['infection_time'] = 0
        
        # Count current states
        state_counts = {'S': 0, 'E': 0, 'I': 0, 'R': 0}
        for agent in self.agents:
            state_counts[agent['state']] += 1
        
        return state_counts
    
    def simulate(self, time_steps: int) -> Dict[str, List[int]]:
        """
        Run full simulation for specified time steps.
        
        Args:
            time_steps: Number of time steps to simulate
            
        Returns:
            Dictionary with time series for each state
        """
        results = {'S': [], 'E': [], 'I': [], 'R': [], 'time': []}
        
        for t in range(time_steps):
            state_counts = self.simulate_step()
            results['time'].append(t)
            for state in ['S', 'E', 'I', 'R']:
                results[state].append(state_counts[state])
        
        return results


class NetworkModel:
    """
    Network-based epidemiological model using contact networks.
    
    This model uses graph theory to represent social networks
    and simulate disease spread through network connections.
    """
    
    def __init__(self, 
                 network_type: str = 'small_world',
                 network_params: Optional[Dict] = None):
        self.network_type = network_type
        self.network_params = network_params or {}
        self.network = None
        self.node_states = {}
    
    def create_network(self, num_nodes: int) -> None:
        """
        Create network structure.
        
        Args:
            num_nodes: Number of nodes in the network
        """
        # Simplified network creation (would use networkx in full implementation)
        self.network = {}
        
        if self.network_type == 'small_world':
            # Create small-world network structure
            k = self.network_params.get('k', 4)  # Each node connected to k nearest neighbors
            p = self.network_params.get('p', 0.1)  # Rewiring probability
            
            for i in range(num_nodes):
                neighbors = []
                for j in range(1, k//2 + 1):
                    neighbors.extend([(i + j) % num_nodes, (i - j) % num_nodes])
                
                # Random rewiring
                for j, neighbor in enumerate(neighbors):
                    if np.random.random() < p:
                        neighbors[j] = np.random.randint(0, num_nodes)
                
                self.network[i] = list(set(neighbors))
        
        # Initialize all nodes as susceptible except patient zero
        self.node_states = {i: 'S' for i in range(num_nodes)}
        if num_nodes > 0:
            self.node_states[0] = 'I'
    
    def simulate_transmission(self, 
                            transmission_rate: float,
                            recovery_rate: float,
                            time_steps: int) -> Dict[str, List[int]]:
        """
        Simulate disease transmission on network.
        
        Args:
            transmission_rate: Probability of transmission per contact
            recovery_rate: Probability of recovery per time step
            time_steps: Number of simulation steps
            
        Returns:
            Time series of state counts
        """
        results = {'S': [], 'I': [], 'R': [], 'time': []}
        
        for t in range(time_steps):
            new_infections = []
            new_recoveries = []
            
            # Transmission step
            for node, state in self.node_states.items():
                if state == 'I':
                    # Infectious node can transmit to neighbors
                    for neighbor in self.network.get(node, []):
                        if (self.node_states[neighbor] == 'S' and 
                            np.random.random() < transmission_rate):
                            new_infections.append(neighbor)
                    
                    # Check for recovery
                    if np.random.random() < recovery_rate:
                        new_recoveries.append(node)
            
            # Apply state changes
            for node in new_infections:
                self.node_states[node] = 'I'
            for node in new_recoveries:
                self.node_states[node] = 'R'
            
            # Count states
            state_counts = {'S': 0, 'I': 0, 'R': 0}
            for state in self.node_states.values():
                state_counts[state] += 1
            
            results['time'].append(t)
            for state in ['S', 'I', 'R']:
                results[state].append(state_counts[state])
        
        return results


def create_seir_model(parameters: Dict) -> SEIRModel:
    """
    Factory function to create SEIR model from parameters dictionary.
    
    Args:
        parameters: Dictionary containing model parameters
        
    Returns:
        Configured SEIR model
    """
    seir_params = SEIRParameters(
        beta=parameters.get('beta', 0.5),
        sigma=parameters.get('sigma', 1/5.1),  # 5.1 day incubation
        gamma=parameters.get('gamma', 1/10),   # 10 day infectious period
        mu=parameters.get('mu', 0.0),
        population=parameters.get('population', 100000)
    )
    
    return SEIRModel(seir_params)


def create_agent_based_model(parameters: Dict) -> AgentBasedModel:
    """
    Factory function to create agent-based model from parameters dictionary.
    
    Args:
        parameters: Dictionary containing model parameters
        
    Returns:
        Configured agent-based model
    """
    return AgentBasedModel(
        population_size=parameters.get('population_size', 1000),
        transmission_probability=parameters.get('transmission_probability', 0.05),
        recovery_time=parameters.get('recovery_time', 10),
        incubation_time=parameters.get('incubation_time', 5)
    )


def create_network_model(parameters: Dict) -> NetworkModel:
    """
    Factory function to create network model from parameters dictionary.
    
    Args:
        parameters: Dictionary containing model parameters
        
    Returns:
        Configured network model
    """
    return NetworkModel(
        network_type=parameters.get('network_type', 'small_world'),
        network_params=parameters.get('network_params', {})
    )


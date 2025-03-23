import httpx
from .storage import Storage
from .decision import DecisionInput, DecisionOutput
import logging

# Set up logging
logger = logging.getLogger(__name__)

class Cooperative:
    def __init__(self, config, initial_token_balance):
        """
        Initialize the energy cooperative with storages and token balances
        
        Args:
            config: Configuration dictionary with 'storages' list
            initial_token_balance: Starting token balance
        """
        self.storages = [Storage(**storage_config) for storage_config in config.get('storages', [])]
        # Initialize token balances for community and each storage
        self.token_balances = {'community': initial_token_balance}
        for storage in self.storages:
            self.token_balances[storage.name] = initial_token_balance
        self.community_token_balance = initial_token_balance
        
        # Initialize history tracking
        self.history_consumption = []
        self.history_production = []
        self.history_token_balance = []
        self.history_p2p_price = []
        self.history_grid_price = []
        self.history_storage = {storage.name: [] for storage in self.storages}
        self.history_energy_deficit = []
        self.history_energy_surplus = []
        self.history_energy_sold_to_grid = []
        self.history_energy_sold_to_p2p = []  # New tracking for P2P sales
        self.history_tokens_gained_from_grid = []
        self.history_purchase_price = []
        self.logs = []

    def simulate_step(self, step, p2p_base_price, hourly_data, grid_costs, 
                     min_price=0.2, token_mint_rate=0.1, token_burn_rate=0.1):
        """
        Simulate a single time step in the energy management system
        
        Args:
            step: Current simulation step
            p2p_base_price: Base price for peer-to-peer trading
            hourly_data: List of dictionaries with hourly consumption and production data
            grid_costs: List of dictionaries with grid purchase and sale prices
            min_price: Minimum energy price (optional)
            token_mint_rate: Rate at which tokens are minted (optional)
            token_burn_rate: Rate at which tokens are burned (optional)
        """
        # Get data for the current step
        hourly_data_step = hourly_data[step]
        hour = hourly_data_step['hour']
        consumption = hourly_data_step['consumption']
        production = hourly_data_step['production']
        date = hourly_data_step['date']
        
        # Get grid prices for the current step
        grid_price = grid_costs[step % len(grid_costs)]['purchase']
        sale_price = grid_costs[step % len(grid_costs)]['sale']

        # Calculate energy surplus/deficit
        energy_surplus = max(0, production - consumption)
        energy_deficit = max(0, consumption - production)

        # Prepare the request payload
        request_payload = DecisionInput(
            hour=hour,
            production=production,
            consumption=consumption,
            storage_levels={
                storage.name: {'current_level': storage.current_level, 'capacity': storage.capacity}
                for storage in self.storages
            },
            grid_purchase_price=grid_price,
            grid_sale_price=sale_price,
            p2p_base_price=p2p_base_price,
            token_balance=self.community_token_balance
        )

        # Send the request to the manager agent with error handling
        try:
            with httpx.Client(timeout=10.0) as client:  # Add a timeout
                response = client.post(
                    "http://127.0.0.1:8000/decision",
                    json=request_payload.dict()
                )
                response.raise_for_status()
                decision_output = DecisionOutput(**response.json())
        except Exception as e:
            logger.error(f"Error communicating with the manager agent: {str(e)}")
            # Default to a simple strategy in case of error
            decision_output = DecisionOutput(
                energy_added_to_storage=min(energy_surplus, sum(s.capacity - s.current_level for s in self.storages)),
                energy_sold_to_grid=max(0, energy_surplus - min(energy_surplus, sum(s.capacity - s.current_level for s in self.storages))),
                energy_bought_from_storages=min(energy_deficit, sum(s.current_level for s in self.storages)),
                energy_bought_from_grid=max(0, energy_deficit - min(energy_deficit, sum(s.current_level for s in self.storages)))
            )

        # Extract the decision results
        energy_added_to_storage = decision_output.energy_added_to_storage
        energy_sold_to_grid = decision_output.energy_sold_to_grid
        energy_bought_from_storages = decision_output.energy_bought_from_storages
        energy_bought_from_grid = decision_output.energy_bought_from_grid

        # Update storage levels based on the decision
        remaining_to_store = energy_added_to_storage
        remaining_to_discharge = energy_bought_from_storages
        
        for storage in self.storages:
            if remaining_to_store > 0:
                charged_energy = storage.charge(remaining_to_store)
                remaining_to_store -= charged_energy
            if remaining_to_discharge > 0:
                discharged_energy = storage.discharge(remaining_to_discharge)
                remaining_to_discharge -= discharged_energy

            # 1. Mint tokens based on renewable energy consumption
            renewable_consumption = min(consumption, production)
            minted_tokens = renewable_consumption * token_mint_rate
            self.community_token_balance += minted_tokens

            # 2. Add tokens for energy added to storage (P2P)
            self.community_token_balance += energy_added_to_storage * p2p_base_price

            # 3. Add tokens from grid sales
            self.community_token_balance += energy_sold_to_grid * sale_price

            # 4. Subtract tokens for energy taken from storage
            self.community_token_balance -= energy_bought_from_storages * p2p_base_price

            # 5. Handle grid purchases with token burning
            required_tokens = energy_bought_from_grid * grid_price
            if self.community_token_balance >= required_tokens:
                # Subtract cost of grid purchases
                self.community_token_balance -= required_tokens
                # Burn tokens for grid energy
                burned_tokens = energy_bought_from_grid * token_burn_rate
                self.community_token_balance -= burned_tokens
            else:
                # If not enough tokens, buy only what's affordable
                affordable_energy = self.community_token_balance / grid_price if grid_price > 0 else 0
                energy_bought_from_grid = affordable_energy
                self.community_token_balance = 0

        # Log the negotiation details
        log_entry = f"=== Current step: {date} ===\n"
        log_entry += f"Total consumption: {consumption:.2f} kWh\n"
        log_entry += f"Total production: {production:.2f} kWh\n"
        log_entry += f"Energy surplus: {energy_surplus:.2f} kWh\n"
        log_entry += f"Energy deficit: {energy_deficit:.2f} kWh\n"
        log_entry += f"Energy added to storage: {energy_added_to_storage:.2f} kWh\n"
        log_entry += f"Energy got from storages: {energy_bought_from_storages:.2f} kWh\n"
        log_entry += f"Energy bought from grid: {energy_bought_from_grid:.2f} kWh\n"
        log_entry += f"Energy sold to grid: {energy_sold_to_grid:.2f} kWh\n"
        log_entry += f"Purchase grid price for this step: {grid_price:.2f} CT/kWh\n"
        log_entry += f"Sale grid price for this step: {sale_price:.2f} CT/kWh\n"
        log_entry += f"P2P base price for this step: {p2p_base_price:.2f} CT/kWh\n"
        
        for storage in self.storages:
            log_entry += f"Storage {storage.name} level after intervention: {storage.current_level:.2f} kWh\n"
        
        log_entry += f"Token balance: {self.community_token_balance:.2f} CT\n"
        self.logs.append(log_entry)

        # Update history
        self.history_consumption.append(consumption)
        self.history_production.append(production)
        self.history_token_balance.append(self.community_token_balance)
        self.history_p2p_price.append(p2p_base_price)
        self.history_grid_price.append(sale_price)
        self.history_purchase_price.append(grid_price)
        
        for storage in self.storages:
            self.history_storage[storage.name].append(storage.current_level)
        
        self.history_energy_deficit.append(energy_deficit)
        self.history_energy_surplus.append(energy_surplus)
        self.history_energy_sold_to_grid.append(energy_sold_to_grid)
        self.history_tokens_gained_from_grid.append(energy_sold_to_grid * sale_price)

    def simulate(self, steps, p2p_base_price, min_price, token_mint_rate, token_burn_rate, hourly_data, grid_costs):
        """
        Run a complete simulation for the specified number of steps
        
        Args:
            steps: Number of simulation steps to run
            p2p_base_price: Base price for peer-to-peer trading
            min_price: Minimum energy price
            token_mint_rate: Rate at which tokens are minted
            token_burn_rate: Rate at which tokens are burned
            hourly_data: List of dictionaries with hourly consumption and production data
            grid_costs: List of dictionaries with grid purchase and sale prices
        """
        for step in range(steps):
            self.simulate_step(
                step=step, 
                p2p_base_price=p2p_base_price, 
                hourly_data=hourly_data, 
                grid_costs=grid_costs,
                min_price=min_price, 
                token_mint_rate=token_mint_rate, 
                token_burn_rate=token_burn_rate
            )

    def save_logs(self, filename):
        """
        Save simulation logs to a file
        
        Args:
            filename: Path to the log file
        """
        with open(filename, 'w') as f:
            for log in self.logs:
                f.write(log + "\n")
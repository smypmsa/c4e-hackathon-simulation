from .storage import Storage


class Cooperative:
    def __init__(self, config, initial_token_balance):
        self.storages = [Storage(**storage_config) for storage_config in config.get('storages', [])]
        self.token_balances = {'community': initial_token_balance}
        for storage in self.storages:
            self.token_balances[storage.name] = initial_token_balance
        self.community_token_balance = initial_token_balance
        self.history_consumption = []
        self.history_production = []
        self.history_token_balance = []
        self.history_p2p_price = []
        self.history_grid_price = []
        self.history_storage = {storage.name: [] for storage in self.storages}
        self.history_energy_deficit = []
        self.history_energy_surplus = []
        self.logs = []

    def simulate_step(self, step, p2p_base_price, grid_price, min_price, token_mint_rate, token_burn_rate, hourly_data):
        hourly_data_step = hourly_data[step]
        consumption = hourly_data_step['consumption']
        production = hourly_data_step['production']

        # Calculate net energy balance
        net_energy = production - consumption

        # Update storage level
        energy_surplus = 0
        minted_tokens = 0
        if net_energy > 0:
            for storage in self.storages:
                net_energy -= storage.charge(net_energy)
                if net_energy <= 0:
                    break
            if net_energy > 0:
                energy_surplus = net_energy
                for storage in self.storages:
                    if storage.current_level >= net_energy:
                        storage.discharge(net_energy)
                        minted_tokens = net_energy * token_mint_rate
                        self.community_token_balance += minted_tokens
                        break

        elif net_energy < 0:
            for storage in self.storages:
                net_energy += storage.discharge(-net_energy)
                if net_energy >= 0:
                    break

        # If there is still a deficit, buy from the grid
        energy_deficit = 0
        burned_tokens = 0
        if net_energy < 0:
            energy_deficit = -net_energy
            required_tokens = energy_deficit * grid_price
            if self.community_token_balance >= required_tokens:
                self.community_token_balance -= required_tokens
                burned_tokens = energy_deficit * token_burn_rate
                self.community_token_balance -= burned_tokens
            else:
                # If not enough tokens, buy as much as possible
                affordable_energy = self.community_token_balance / grid_price
                energy_deficit -= affordable_energy
                self.community_token_balance = 0
                burned_tokens = affordable_energy * token_burn_rate

        # Log the negotiation details
        log_entry = f"=== Negocjacje w bieżącym kroku ===\n"
        log_entry += f"Łączne zużycie: {consumption:.2f} kWh\n"
        log_entry += f"Łączna produkcja: {production:.2f} kWh\n"
        log_entry += f"Handlowana energia (OZE): {max(0, production - consumption):.2f} kWh, średnia cena: {p2p_base_price:.2f} PLN/kWh\n"
        log_entry += f"Tokeny mintowane w tym kroku: {minted_tokens:.2f}\n"
        log_entry += f"Niedobór energii: {energy_deficit:.2f} kWh, zakupione z gridu po {grid_price:.2f} PLN/kWh (koszt: {energy_deficit * grid_price:.2f} PLN)\n"
        log_entry += f"Tokeny spalane z powodu gridu: {burned_tokens:.2f}\n"
        for storage in self.storages:
            log_entry += f"Stan magazynu {storage.name} po interwencji: {storage.current_level:.2f} kWh\n"
        log_entry += f"Saldo tokenów: {self.community_token_balance:.2f} CT\n"
        self.logs.append(log_entry)

        # Update history
        self.history_consumption.append(consumption)
        self.history_production.append(production)
        self.history_token_balance.append(self.community_token_balance)
        self.history_p2p_price.append(p2p_base_price)
        self.history_grid_price.append(grid_price)
        for storage in self.storages:
            self.history_storage[storage.name].append(storage.current_level)
        self.history_energy_deficit.append(energy_deficit)
        self.history_energy_surplus.append(energy_surplus)

    def simulate(self, steps, p2p_base_price, grid_price, min_price, token_mint_rate, token_burn_rate, hourly_data):
        for step in range(steps):
            self.simulate_step(step, p2p_base_price, grid_price, min_price, token_mint_rate, token_burn_rate, hourly_data)

    def save_logs(self, filename):
        with open(filename, 'w') as f:
            for log in self.logs:
                f.write(log + "\n")
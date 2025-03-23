from typing import Dict

class DecisionInput:
    def __init__(
        self,
        hour: int,
        production: float,
        consumption: float,
        storage_levels: Dict[str, float],
        grid_purchase_price: float,
        grid_sale_price: float,
        p2p_base_price: float,
        token_balance: float
    ):
        self.hour = hour
        self.production = production
        self.consumption = consumption
        self.storage_levels = storage_levels
        self.grid_purchase_price = grid_purchase_price
        self.grid_sale_price = grid_sale_price
        self.p2p_base_price = p2p_base_price
        self.token_balance = token_balance
    
    def dict(self):
        return {
            "hour": self.hour,
            "production": self.production,
            "consumption": self.consumption,
            "storage_levels": self.storage_levels,
            "grid_purchase_price": self.grid_purchase_price,
            "grid_sale_price": self.grid_sale_price,
            "p2p_base_price": self.p2p_base_price,
            "token_balance": self.token_balance
        }

class DecisionOutput:
    def __init__(
        self,
        energy_added_to_storage: float = 0.0,
        energy_sold_to_grid: float = 0.0,
        energy_bought_from_storages: float = 0.0,
        energy_bought_from_grid: float = 0.0
    ):
        self.energy_added_to_storage = energy_added_to_storage
        self.energy_sold_to_grid = energy_sold_to_grid
        self.energy_bought_from_storages = energy_bought_from_storages
        self.energy_bought_from_grid = energy_bought_from_grid
    
    def dict(self):
        return {
            "energy_added_to_storage": self.energy_added_to_storage,
            "energy_sold_to_grid": self.energy_sold_to_grid,
            "energy_bought_from_storages": self.energy_bought_from_storages,
            "energy_bought_from_grid": self.energy_bought_from_grid
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            energy_added_to_storage=data.get("energy_added_to_storage", 0.0),
            energy_sold_to_grid=data.get("energy_sold_to_grid", 0.0),
            energy_bought_from_storages=data.get("energy_bought_from_storages", 0.0),
            energy_bought_from_grid=data.get("energy_bought_from_grid", 0.0)
        )
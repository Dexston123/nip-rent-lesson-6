from src.models import Apartment, Bill, Parameters, Tenant, TenantSettlement, Transfer, ApartmentSettlement
from typing import List, Tuple

class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters 

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []
       
        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True

    def get_apartment_costs(self, apartment_key: str, year: int = None, month: int = None) -> float | None:
        if month is not None and (month < 1 or month > 12):
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            return None
        total_cost = 0.0
        for bill in self.bills:
            if bill.apartment == apartment_key and (year is None or bill.settlement_year == year) and (month is None or bill.settlement_month == month):
                total_cost += bill.amount_pln
        return total_cost

    def get_settlement(self, apartment_key: str, year: int, month: int) -> ApartmentSettlement | None:
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            return None
        total_cost = self.get_apartment_costs(apartment_key, year, month)
        if total_cost is None:
            return None
        
        return ApartmentSettlement(
            key=f"{apartment_key}-{year}-{month}",
            apartment=apartment_key,
            year=year,
            month=month,
            total_due_pln=total_cost
        )
    
    def create_tenants_settlements(self, apartment_settlement: ApartmentSettlement) -> List[TenantSettlement] | None:
        if apartment_settlement.month < 1 or apartment_settlement.month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_settlement.apartment not in self.apartments:
            return None
        tenants_in_apartment = [tenant for tenant in self.tenants.values() if tenant.apartment == apartment_settlement.apartment]
        if not tenants_in_apartment:
            return []
        
        return [
            TenantSettlement(
                tenant=tenant.name,
                apartment_settlement=apartment_settlement.key,
                month=apartment_settlement.month,
                year=apartment_settlement.year,
                total_due_pln=apartment_settlement.total_due_pln / len(tenants_in_apartment)
            )
        for tenant in tenants_in_apartment ] 
    
    def get_debtors_report(self, apartment_key: str, year: int, month: int) -> List[Tuple[str, float, float, float]]:
        apartment_settlement = self.get_settlement(apartment_key, year, month)
        if apartment_settlement is None:
            return []

        tenants_settlements = self.create_tenants_settlements(apartment_settlement)
        if not tenants_settlements:
            return []

        report = []

        for tenant_settlement in tenants_settlements:
            tenant_name = tenant_settlement.tenant
            due = tenant_settlement.total_due_pln

            paid = sum(
                (
                    t.amount_pln
                    for t in self.transfers
                    if t.tenant == tenant_name
                    and t.settlement_year == year
                    and t.settlement_month == month
                    and t.apartment == apartment_key
                ),
                0.0
            )

            debt = due - paid

            if debt > 0:
                report.append((tenant_name, due, paid, debt))

        return report
    
    def get_yearly_costs(self, apartment_key: str, year: int) -> float:
        if apartment_key not in self.apartments:
            return 0.0

        return sum(
            self.get_apartment_costs(apartment_key, year, month) or 0.0
            for month in range(1, 13)
        )
    
    def get_tax(self, year: int, month: int, tax_rate: float) -> float:
        debtors_report = self.get_debtors_report("apart-polanka", year, month)
        total_revenue = sum(paid for _, _, paid, _ in debtors_report)
        tax = total_revenue * tax_rate

        return round(tax, 2)
    
    def get_annual_report(self, year: int) -> Tuple[float, float]:
        total_costs = 0.0
        total_revenue = 0.0

        for month in range(1, 13):
            total_costs += self.get_apartment_costs('apart-polanka', year, month) or 0.0

        for transfer in self.transfers:
            if transfer.settlement_year == year:
                total_revenue += transfer.amount_pln

        return total_costs, total_revenue
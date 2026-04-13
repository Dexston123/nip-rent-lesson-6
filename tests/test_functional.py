from src.manager import Manager
from src.models import Parameters
from src.models import Transfer

def test_integrity_total_due_equals_apartment_costs():
    """
    Test integralności danych:
    suma należności lokatorów == suma kosztów mieszkania
    """

    manager = Manager(Parameters())

    apartment = 'apart-polanka'
    year = 2025
    month = 1

    apartment_settlement = manager.get_settlement(apartment, year, month)
    tenants_settlements = manager.create_tenants_settlements(apartment_settlement)

    total_due_from_tenants = sum(t.total_due_pln for t in tenants_settlements)
    apartment_costs = manager.get_apartment_costs(apartment, year, month)

    assert round(total_due_from_tenants, 2) == round(apartment_costs, 2), (
        f"Integralność naruszona: "
        f"suma lokatorów ({total_due_from_tenants}) "
        f"!= koszty mieszkania ({apartment_costs})"
    )

def test_get_debtors_report():
    """
    Test: raport dłużników pokazuje kto ma niedopłatę
    """

    manager = Manager(Parameters())

    apartment = 'apart-polanka'
    year = 2025
    month = 1

    apartment_settlement = manager.get_settlement(apartment, year, month)
    tenants_settlements = manager.create_tenants_settlements(apartment_settlement)

    report = manager.get_debtors_report(apartment, year, month)

    assert isinstance(report, list)

    for item in report:
        tenant_name, due, paid, debt = item

        assert isinstance(tenant_name, str)
        assert isinstance(due, float)
        assert isinstance(paid, float)
        assert isinstance(debt, float)

        assert round(debt, 2) == round(due - paid, 2)

        assert debt > 0

def test_get_yearly_costs():
    manager = Manager(Parameters())

    apartment = 'apart-polanka'
    year = 2024

    total = manager.get_yearly_costs(apartment, year)

    manual_sum = sum(
        manager.get_apartment_costs(apartment, year, m)
        for m in range(1, 13)
    )

    assert round(total, 2) == round(manual_sum, 2)

def test_get_tax():
    """
    Test: metoda get_tax poprawnie oblicza podatek od przychodu za dany miesiąc i rok,
          bazując na raporcie dłużników.
    """
    
    manager = Manager(Parameters())

    year = 2025
    month = 1
    tax_rate = 0.085

    manager.transfers = [
        Transfer(tenant="Tenant A", amount_pln=1000.0, apartment="apart-polanka", settlement_year=2025, settlement_month=1, date="2025-01-01"),
        Transfer(tenant="Tenant B", amount_pln=1500.0, apartment="apart-polanka", settlement_year=2025, settlement_month=1, date="2025-01-01"),
        Transfer(tenant="Tenant C", amount_pln=2000.0, apartment="apart-polanka", settlement_year=2025, settlement_month=1, date="2025-01-01"),
    ]
    
    debtors_report = manager.get_debtors_report("apart-polanka", year, month)
    total_revenue = sum(paid for _, _, paid, _ in debtors_report)

    expected_tax = total_revenue * tax_rate
    calculated_tax = manager.get_tax(year, month, tax_rate)

    assert round(calculated_tax, 2) == round(expected_tax, 2)

    tax_rate = 0.10
    expected_tax = total_revenue * tax_rate
    calculated_tax = manager.get_tax(year, month, tax_rate)

    assert round(calculated_tax, 2) == round(expected_tax, 2)

def test_get_annual_report():
    """
    Test: metoda get_annual_report zwraca sumaryczne koszty i przychody dla całej firmy w danym roku
    """

    manager = Manager(Parameters())

    year = 2025

    total_costs, total_revenue = manager.get_annual_report(year)

    assert isinstance(total_costs, float)
    assert isinstance(total_revenue, float)

    assert total_costs >= 0
    assert total_revenue >= 0
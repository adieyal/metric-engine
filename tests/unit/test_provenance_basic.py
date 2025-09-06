"""Basic integration tests for provenance functionality."""
from decimal import Decimal

from metricengine.provenance import Provenance
from metricengine.value import FinancialValue


def test_basic_provenance_workflow():
    """Test basic provenance workflow from creation to access."""
    # Create a simple FinancialValue
    fv = FinancialValue(100.50)

    # Should automatically have provenance
    assert fv.has_provenance()

    # Should be able to access provenance
    prov = fv.get_provenance()
    assert prov is not None
    assert isinstance(prov, Provenance)
    assert prov.op == "literal"
    assert prov.inputs == ()
    assert isinstance(prov.id, str)
    assert len(prov.id) > 0


def test_provenance_with_helper_method():
    """Test using the _with helper method."""
    parent1 = FinancialValue(100)
    parent2 = FinancialValue(50)

    # Create a result using _with
    result = parent1._with(
        Decimal("150"), op="+", parents=(parent1, parent2), meta={"test": "addition"}
    )

    # Verify the result
    assert result.as_decimal() == Decimal("150.00")
    assert result.has_provenance()

    prov = result.get_provenance()
    assert prov.op == "+"
    assert len(prov.inputs) == 2
    assert prov.meta.get("test") == "addition"


def test_backward_compatibility():
    """Test that existing code works without modification."""
    # This simulates existing code that doesn't know about provenance
    fv1 = FinancialValue(100)
    fv2 = FinancialValue(50)

    # Basic operations should work
    assert fv1.as_decimal() == Decimal("100.00")
    assert fv2.as_decimal() == Decimal("50.00")
    assert not fv1.is_none()
    assert not fv2.is_none()

    # String representation should work
    assert fv1.as_str() == "100.00"
    assert fv2.as_str() == "50.00"

    # Comparisons should work
    assert fv1 > fv2
    assert fv2 < fv1

    # But provenance should be available if accessed
    assert fv1.has_provenance()
    assert fv2.has_provenance()


def test_none_value_provenance():
    """Test that None values get proper provenance."""
    fv = FinancialValue(None)

    assert fv.is_none()
    assert fv.has_provenance()

    prov = fv.get_provenance()
    assert prov.op == "literal"
    assert prov.inputs == ()


if __name__ == "__main__":
    test_basic_provenance_workflow()
    test_provenance_with_helper_method()
    test_backward_compatibility()
    test_none_value_provenance()
    print("All basic provenance tests passed!")

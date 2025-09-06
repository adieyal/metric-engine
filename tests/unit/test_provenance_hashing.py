"""Comprehensive tests for provenance hashing utilities."""
import hashlib
from decimal import Decimal

import pytest

from metricengine.policy import DEFAULT_POLICY, Policy
from metricengine.provenance import (
    Provenance,
    _get_policy_fingerprint,
    _serialize_meta,
    frozendict,
    hash_literal,
    hash_node,
)
from metricengine.value import FinancialValue


class TestProvenanceDataStructure:
    """Test the Provenance dataclass."""

    def test_provenance_immutable(self):
        """Test that Provenance instances are immutable."""
        prov = Provenance(id="test_id", op="literal", inputs=(), meta={"key": "value"})

        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            prov.id = "new_id"

        with pytest.raises(AttributeError):
            prov.op = "new_op"

        with pytest.raises(AttributeError):
            prov.inputs = ("new_input",)

    def test_provenance_meta_immutable(self):
        """Test that meta dictionary is converted to immutable frozendict."""
        prov = Provenance(id="test_id", op="literal", inputs=(), meta={"key": "value"})

        # Meta should be frozendict
        assert isinstance(prov.meta, frozendict)

        # Should not be able to modify meta
        with pytest.raises(TypeError):
            prov.meta["new_key"] = "new_value"

    def test_provenance_slots_optimization(self):
        """Test that Provenance uses slots for memory optimization."""
        prov = Provenance(id="test_id", op="literal", inputs=(), meta={})

        # Should have __slots__ defined (dataclass with slots=True creates this)
        assert hasattr(Provenance, "__slots__")

        # Should not be able to add arbitrary attributes (frozen dataclass behavior)
        with pytest.raises((AttributeError, TypeError)):
            prov.arbitrary_attr = "value"


class TestHashLiteral:
    """Test hash_literal function."""

    def test_hash_literal_deterministic(self):
        """Test that hash_literal produces deterministic results."""
        value = Decimal("100.50")
        policy = DEFAULT_POLICY

        # Multiple calls should produce same hash
        hash1 = hash_literal(value, policy)
        hash2 = hash_literal(value, policy)
        hash3 = hash_literal(value, policy)

        assert hash1 == hash2 == hash3
        assert len(hash1) == 64  # SHA-256 hex length

    def test_hash_literal_none_values(self):
        """Test hash_literal with None values."""
        policy = DEFAULT_POLICY

        hash1 = hash_literal(None, policy)
        hash2 = hash_literal(None, policy)

        assert hash1 == hash2
        assert len(hash1) == 64
        assert hash1 != hash_literal(Decimal("0"), policy)

    def test_hash_literal_different_values(self):
        """Test that different values produce different hashes."""
        policy = DEFAULT_POLICY

        hash1 = hash_literal(Decimal("100"), policy)
        hash2 = hash_literal(Decimal("200"), policy)
        hash3 = hash_literal(
            Decimal("100.00"), policy
        )  # Same value, different representation

        assert hash1 != hash2
        assert hash1 == hash3  # Should be same for equivalent decimals

    def test_hash_literal_policy_sensitivity(self):
        """Test that different policies produce different hashes."""
        value = Decimal("100.50")

        policy1 = DEFAULT_POLICY
        policy2 = Policy(decimal_places=4, rounding="ROUND_UP")

        hash1 = hash_literal(value, policy1)
        hash2 = hash_literal(value, policy2)

        assert hash1 != hash2

    def test_hash_literal_stability_across_runs(self):
        """Test that hashes are stable across different program runs."""
        # This tests that we're not using random seeds or memory addresses
        value = Decimal("123.45")
        policy = DEFAULT_POLICY

        # Create expected hash manually to ensure stability
        policy_fingerprint = _get_policy_fingerprint(policy)
        content = f"literal:{value}:{policy_fingerprint}"
        expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        actual_hash = hash_literal(value, policy)
        assert actual_hash == expected_hash


class TestHashNode:
    """Test hash_node function."""

    def test_hash_node_deterministic(self):
        """Test that hash_node produces deterministic results."""
        parent1 = FinancialValue(100)
        parent2 = FinancialValue(50)
        parents = (parent1, parent2)

        hash1 = hash_node("+", parents, DEFAULT_POLICY)
        hash2 = hash_node("+", parents, DEFAULT_POLICY)

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_hash_node_different_operations(self):
        """Test that different operations produce different hashes."""
        parent1 = FinancialValue(100)
        parent2 = FinancialValue(50)
        parents = (parent1, parent2)

        hash_add = hash_node("+", parents, DEFAULT_POLICY)
        hash_sub = hash_node("-", parents, DEFAULT_POLICY)
        hash_mul = hash_node("*", parents, DEFAULT_POLICY)

        assert hash_add != hash_sub != hash_mul

    def test_hash_node_parent_order_independence(self):
        """Test that parent order doesn't affect hash (for commutative operations)."""
        parent1 = FinancialValue(100)
        parent2 = FinancialValue(50)

        # Note: The current implementation sorts parent IDs, so order shouldn't matter
        hash1 = hash_node("+", (parent1, parent2), DEFAULT_POLICY)
        hash2 = hash_node("+", (parent2, parent1), DEFAULT_POLICY)

        assert hash1 == hash2

    def test_hash_node_with_metadata(self):
        """Test hash_node with metadata."""
        parent1 = FinancialValue(100)
        parent2 = FinancialValue(50)
        parents = (parent1, parent2)

        meta1 = {"input_names": {"a": "revenue", "b": "cost"}}
        meta2 = {"input_names": {"a": "price", "b": "quantity"}}

        hash1 = hash_node("+", parents, DEFAULT_POLICY, meta1)
        hash2 = hash_node("+", parents, DEFAULT_POLICY, meta2)
        hash3 = hash_node("+", parents, DEFAULT_POLICY, meta1)

        assert hash1 != hash2  # Different metadata
        assert hash1 == hash3  # Same metadata

    def test_hash_node_without_provenance_parents(self):
        """Test hash_node with parents that don't have provenance."""
        # Create FinancialValue without automatic provenance
        parent1 = FinancialValue(100, _prov=None)
        parent2 = FinancialValue(50, _prov=None)

        # Should still work by generating literal provenance for parents
        hash1 = hash_node("+", (parent1, parent2), DEFAULT_POLICY)
        hash2 = hash_node("+", (parent1, parent2), DEFAULT_POLICY)

        assert hash1 == hash2
        assert len(hash1) == 64


class TestPolicyFingerprinting:
    """Test policy fingerprinting utilities."""

    def test_policy_fingerprint_deterministic(self):
        """Test that policy fingerprints are deterministic."""
        policy = DEFAULT_POLICY

        fp1 = _get_policy_fingerprint(policy)
        fp2 = _get_policy_fingerprint(policy)

        assert fp1 == fp2

    def test_policy_fingerprint_different_policies(self):
        """Test that different policies produce different fingerprints."""
        policy1 = DEFAULT_POLICY
        policy2 = Policy(decimal_places=4, rounding="ROUND_UP")

        fp1 = _get_policy_fingerprint(policy1)
        fp2 = _get_policy_fingerprint(policy2)

        assert fp1 != fp2

    def test_policy_fingerprint_none(self):
        """Test policy fingerprint with None policy."""
        fp = _get_policy_fingerprint(None)
        assert fp == "None"

    def test_policy_fingerprint_stability(self):
        """Test that policy fingerprints are stable across changes."""
        # Create two identical policies
        policy1 = Policy(decimal_places=2, rounding="ROUND_HALF_UP")
        policy2 = Policy(decimal_places=2, rounding="ROUND_HALF_UP")

        fp1 = _get_policy_fingerprint(policy1)
        fp2 = _get_policy_fingerprint(policy2)

        assert fp1 == fp2


class TestMetadataSerialization:
    """Test metadata serialization utilities."""

    def test_serialize_meta_empty(self):
        """Test serializing empty metadata."""
        result = _serialize_meta({})
        assert result == ""

        result = _serialize_meta(None)
        assert result == ""

    def test_serialize_meta_deterministic(self):
        """Test that metadata serialization is deterministic."""
        meta = {"key1": "value1", "key2": "value2", "key3": 123}

        result1 = _serialize_meta(meta)
        result2 = _serialize_meta(meta)

        assert result1 == result2

    def test_serialize_meta_key_order_independence(self):
        """Test that key order doesn't affect serialization."""
        meta1 = {"b": "value2", "a": "value1", "c": "value3"}
        meta2 = {"a": "value1", "b": "value2", "c": "value3"}

        result1 = _serialize_meta(meta1)
        result2 = _serialize_meta(meta2)

        assert result1 == result2

    def test_serialize_meta_different_values(self):
        """Test that different metadata produces different serializations."""
        meta1 = {"key": "value1"}
        meta2 = {"key": "value2"}

        result1 = _serialize_meta(meta1)
        result2 = _serialize_meta(meta2)

        assert result1 != result2


class TestHashUniqueness:
    """Test hash uniqueness and collision resistance."""

    def test_hash_uniqueness_large_sample(self):
        """Test hash uniqueness across a large sample of inputs."""
        hashes = set()

        # Generate hashes for many different values
        for i in range(1000):
            value = Decimal(str(i * 0.01))  # 0.00, 0.01, 0.02, ..., 9.99
            hash_val = hash_literal(value, DEFAULT_POLICY)

            # Should not have seen this hash before
            assert hash_val not in hashes
            hashes.add(hash_val)

        # Should have 1000 unique hashes
        assert len(hashes) == 1000

    def test_operation_hash_uniqueness(self):
        """Test that different operations produce unique hashes."""
        parent1 = FinancialValue(100)
        parent2 = FinancialValue(50)
        parents = (parent1, parent2)

        operations = ["+", "-", "*", "/", "**", "calc:margin", "literal"]
        hashes = set()

        for op in operations:
            hash_val = hash_node(op, parents, DEFAULT_POLICY)
            assert hash_val not in hashes
            hashes.add(hash_val)

        assert len(hashes) == len(operations)


class TestHashStability:
    """Test hash stability requirements."""

    def test_identical_operations_identical_hashes(self):
        """Test that identical operations produce identical hashes."""
        # Create identical operations multiple times
        for _ in range(10):
            parent1 = FinancialValue(Decimal("100.50"))
            parent2 = FinancialValue(Decimal("25.25"))

            hash1 = hash_node("+", (parent1, parent2), DEFAULT_POLICY)
            hash2 = hash_node("+", (parent1, parent2), DEFAULT_POLICY)

            assert hash1 == hash2

    def test_hash_tamper_evidence(self):
        """Test that hashes change when inputs are tampered with."""
        parent1 = FinancialValue(100)
        parent2 = FinancialValue(50)

        original_hash = hash_node("+", (parent1, parent2), DEFAULT_POLICY)

        # Change one parent
        parent2_modified = FinancialValue(51)
        modified_hash = hash_node("+", (parent1, parent2_modified), DEFAULT_POLICY)

        assert original_hash != modified_hash

    def test_hash_cryptographic_properties(self):
        """Test basic cryptographic properties of hashes."""
        # Test that hashes look random (basic avalanche effect)
        hash1 = hash_literal(Decimal("100.00"), DEFAULT_POLICY)
        hash2 = hash_literal(Decimal("100.01"), DEFAULT_POLICY)

        # Should be completely different despite small input change
        assert hash1 != hash2

        # Count different characters (should be roughly half for good hash)
        different_chars = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        assert different_chars > 20  # At least 20 out of 64 chars different


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

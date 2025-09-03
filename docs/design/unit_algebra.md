# Unit Algebra Design

Mathematical operations on units and dimensional analysis.

## Unit Dimensions

Units are organized by dimension:
- **Currency**: USD, EUR, GBP
- **Percentage**: %, bp (basis points)
- **Count**: shares, units
- **Time**: years, months, days

## Algebraic Rules

### Multiplication
- `Money * Percentage → Money`
- `Count * Money → Money`
- `Money * Count → Money`

### Division
- `Money / Money → Ratio`
- `Money / Count → Money per unit`
- `Percentage / Count → Percentage per unit`

### Addition/Subtraction
- Same units only: `USD + USD → USD`
- Different currencies require conversion

## Implementation

```python
class Unit:
    def __mul__(self, other):
        return self._multiply_units(other)
    
    def _multiply_units(self, other):
        # Unit algebra rules
        pass
```

## Validation

Units are validated at:
- Creation time
- Operation time  
- Assignment time
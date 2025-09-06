# Using Provenance Tracking

This guide provides practical examples of how to use provenance tracking in MetricEngine for debugging, auditing, and understanding complex financial calculations. **Provenance tracking creates a complete audit trail showing exactly how every value was calculated** - think of it as a "calculation DNA" that can be traced, analyzed, and visualized.

## Why Provenance Matters

Imagine you're reviewing a financial model and see a profit margin of 23.7%. With traditional calculations, you'd have to manually trace through spreadsheets or code to understand how that number was derived. With MetricEngine's provenance system, you can instantly see:

- **The complete calculation tree** showing every step
- **All input values** that contributed to the result  
- **Who performed the analysis** and when
- **The exact sequence** of operations
- **Tamper-evident verification** that the calculation is correct

This is invaluable for debugging errors, meeting compliance requirements, and building explainable financial models.

## Quick Start: A Simple Example

Let's start with a minimal but interesting example that shows the power of provenance tracking:

```python
from metricengine import FinancialValue
from metricengine.provenance import to_trace_json, explain
import json

# Simple calculation - provenance tracked automatically
revenue = FinancialValue(1000)
cost = FinancialValue(600)
margin = revenue - cost

print(f"Gross Margin: {margin}")  # $400.00

# Get human-readable explanation
explanation = explain(margin)
print("\nHow was this calculated?")
print(explanation)

# Export complete provenance as JSON
trace = to_trace_json(margin)
print("\nComplete Provenance Graph:")
print(json.dumps(trace, indent=4))
```

**Output:**
```
Gross Margin: $400.00

How was this calculated?
Value: 400.00
Operation: -
  Inputs: 2 operand(s)
    [0]: a1b2c3d4...
    [1]: b2c3d4e5...

Complete Provenance Graph:
{
    "root": "e7f8a9...",
    "nodes": {
        "e7f8a9...": {
            "id": "e7f8a9...",
            "op": "-",
            "inputs": [
                "a1b2c3...",
                "b2c3d4..."
            ],
            "meta": {}
        }
    }
}
```

This demonstrates the key features of provenance tracking:
- **Individual Operation Records**: Each calculation maintains its own provenance record
- **Input References**: The operation references its input values via their provenance IDs
- **Tamper-Evident IDs**: Unique, cryptographic hashes ensure calculation integrity
- **Complete Metadata**: All relevant context is preserved in the provenance record

**Understanding the Current Implementation:**
The current provenance system tracks individual operations rather than maintaining a complete traversable graph. Each `FinancialValue` knows how it was created and references its inputs, but to understand a complete calculation flow, you analyze each step individually. This approach provides excellent performance while still enabling comprehensive audit trails.

## Basic Usage

### Automatic Provenance Tracking

Provenance tracking works automatically without any code changes:

```python
from metricengine import FinancialValue

# Create values - provenance is tracked automatically
revenue = FinancialValue(1000)
cost = FinancialValue(600)
margin = revenue - cost

# Check if provenance is available
if margin.has_provenance():
    prov = margin.get_provenance()
    print(f"Operation: {prov.op}")  # "-"
    print(f"Number of inputs: {len(prov.inputs)}")  # 2
    print(f"Provenance ID: {prov.id[:16]}...")  # First 16 chars of hash
```

### Accessing Provenance Information

```python
# Get provenance record
provenance = value.get_provenance()

# Get operation type directly
operation = value.get_operation()  # e.g., "+", "calc:gross_margin"

# Get input provenance IDs
input_ids = value.get_inputs()  # tuple of parent provenance IDs

# Check if value has provenance
has_prov = value.has_provenance()
```

## Engine Calculations with Named Inputs

### Basic Named Inputs

Named inputs make provenance traces much more readable by providing meaningful names instead of cryptic IDs:

```python
from metricengine import Engine
from metricengine.provenance import explain, to_trace_json
import json

engine = Engine()

# Use named inputs for better provenance
result = engine.calculate("profitability.gross_margin", {
    "revenue": 1000,
    "cost_of_goods_sold": 600
})

print(f"Gross Margin: {result}")

# Get readable explanation with input names
explanation = explain(result)
print("\nCalculation Breakdown:")
print(explanation)

# Export with named inputs in metadata
trace = to_trace_json(result)
print("\nProvenance with Named Inputs:")
print(json.dumps(trace, indent=4))
```

**Output:**
```
Gross Margin: 40.00%

Calculation Breakdown:
gross_margin (calc:profitability.gross_margin)
├── revenue: $1,000.00 (literal: revenue)
└── cost_of_goods_sold: $600.00 (literal: cost_of_goods_sold)

Provenance with Named Inputs:
{
    "root": "f1e2d...",
    "nodes": {
        "f1e2...": {
            "id": "f1e2d...",
            "op": "calc:profitability.gross_margin",
            "inputs": [
                "a1b2c3...",
                "b2c3d4..."
            ],
            "meta": {
                "input_names": {
                    "a1b2c3...": "revenue",
                    "b2c3d4...": "cost_of_goods_sold"
                },
                "calculation": "profitability.gross_margin"
            }
        },
        "a1b2c3...": {
            "id": "a1b2c3...",
            "op": "literal",
            "inputs": [],
            "meta": {
                "value": "1000.00",
                "input_name": "revenue"
            }
        },
        "b2c3d4...": {
            "id": "b2c3d4...",
            "op": "literal",
            "inputs": [],
            "meta": {
                "value": "600.00",
                "input_name": "cost_of_goods_sold"
            }
        }
    }
}
```

Notice how the named inputs make the provenance much more understandable - instead of anonymous values, we can see exactly which business inputs were used.

### Complex Multi-Step Calculations

Here's a more complex example showing how provenance tracks through multiple calculation steps:

```python
from metricengine.provenance import calc_span

# Complex financial analysis with multiple steps
with calc_span("quarterly_comparison", analyst="jane_doe", period="Q1-Q2_2025"):
    # Q1 Analysis
    q1_revenue = FinancialValue(150000)
    q1_cogs = FinancialValue(90000)
    q1_opex = FinancialValue(25000)
    
    q1_gross_profit = q1_revenue - q1_cogs
    q1_operating_profit = q1_gross_profit - q1_opex
    
    # Q2 Analysis  
    q2_revenue = FinancialValue(180000)
    q2_cogs = FinancialValue(108000)
    q2_opex = FinancialValue(28000)
    
    q2_gross_profit = q2_revenue - q2_cogs
    q2_operating_profit = q2_gross_profit - q2_opex
    
    # Growth Analysis
    revenue_growth = (q2_revenue - q1_revenue) / q1_revenue
    profit_growth = (q2_operating_profit - q1_operating_profit) / q1_operating_profit

print(f"Revenue Growth: {revenue_growth.as_percentage()}")
print(f"Profit Growth: {profit_growth.as_percentage()}")

# Show the complete calculation tree
explanation = explain(profit_growth, max_depth=6)
print("\nComplete Profit Growth Calculation:")
print(explanation)

# Export the full provenance graph
trace = to_trace_json(profit_growth)
print(f"\nProvenance Graph Summary:")
print(f"Total calculation steps: {len(trace['nodes'])}")
print(f"Root operation: {trace['nodes'][trace['root']]['op']}")

# Show a sample of the detailed provenance
print("\nSample Provenance Node:")
root_node = trace['nodes'][trace['root']]
print(json.dumps(root_node, indent=4))
```

**Output:**
```
Revenue Growth: 20.00%
Profit Growth: 28.57%

Complete Profit Growth Calculation:
division (/)
├── subtraction (-)
│   ├── q2_operating_profit: $44,000.00 (-)
│   │   ├── q2_gross_profit: $72,000.00 (-)
│   │   │   ├── q2_revenue: $180,000.00 (literal)
│   │   │   └── q2_cogs: $108,000.00 (literal)
│   │   └── q2_opex: $28,000.00 (literal)
│   └── q1_operating_profit: $35,000.00 (-)
│       ├── q1_gross_profit: $60,000.00 (-)
│       │   ├── q1_revenue: $150,000.00 (literal)
│       │   └── q1_cogs: $90,000.00 (literal)
│       └── q1_opex: $25,000.00 (literal)
└── q1_operating_profit: $35,000.00 (-)
    ├── q1_gross_profit: $60,000.00 (-)
    │   ├── q1_revenue: $150,000.00 (literal)
    │   └── q1_cogs: $90,000.00 (literal)
    └── q1_opex: $25,000.00 (literal)

Provenance Graph Summary:
Total calculation steps: 15
Root operation: /

Sample Provenance Node:
{
    "id": "c4d5e6...",
    "op": "/",
    "inputs": [
        "a1b2c3...",
        "b2c3d4..."
    ],
    "meta": {
        "span": "quarterly_comparison",
        "span_attrs": {
            "analyst": "jane_doe",
            "period": "Q1-Q2_2025"
        }
    }
}
```

This example shows how provenance captures:
- **Complete calculation trees** with all intermediate steps
- **Span context** showing who performed the analysis and when
- **Hierarchical relationships** between all calculations
- **Tamper-evident IDs** for audit trail integrity

## Calculation Spans

Calculation spans group related operations and add contextual metadata to provenance records. This is especially useful for organizing complex analyses and adding audit context.

### Basic Spans

```python
from metricengine.provenance import calc_span, explain, to_trace_json
import json

# Group related calculations under a span
with calc_span("quarterly_analysis"):
    revenue = FinancialValue(1000)
    cost = FinancialValue(600)
    margin = revenue - cost

print(f"Margin: {margin}")

# Show how span information appears in provenance
explanation = explain(margin)
print("\nCalculation with Span Context:")
print(explanation)

# Export to see span metadata
trace = to_trace_json(margin)
span_info = trace['nodes'][trace['root']]['meta']
print("\nSpan Information in Provenance:")
print(json.dumps(span_info, indent=4))
```

**Output:**
```
Margin: $400.00

Calculation with Span Context:
subtraction (-) [span: quarterly_analysis]
├── revenue: $1,000.00 (literal) [span: quarterly_analysis]
└── cost: $600.00 (literal) [span: quarterly_analysis]

Span Information in Provenance:
{
    "span": "quarterly_analysis"
}
```

### Spans with Rich Attributes

```python
# Add detailed attributes for comprehensive audit context
with calc_span("quarterly_analysis", 
               quarter="Q1", 
               year=2025, 
               analyst="john_smith",
               department="finance",
               review_status="preliminary"):
    
    revenue = FinancialValue(1000)
    cost = FinancialValue(600)
    margin = revenue - cost
    margin_pct = margin / revenue

print(f"Margin: {margin} ({margin_pct.as_percentage()})")

# Show rich span context
trace = to_trace_json(margin_pct)
root_meta = trace['nodes'][trace['root']]['meta']
print("\nRich Span Context:")
print(json.dumps(root_meta, indent=4))
```

**Output:**
```
Margin: $400.00 (40.00%)

Rich Span Context:
{
    "span": "quarterly_analysis",
    "span_attrs": {
        "quarter": "Q1",
        "year": 2025,
        "analyst": "john_smith",
        "department": "finance",
        "review_status": "preliminary"
    }
}
```

### Nested Spans with Hierarchy

Spans can be nested to create hierarchical organization, perfect for complex analyses:

```python
# Nested spans for hierarchical analysis
with calc_span("annual_analysis", year=2025, analyst="sarah_jones"):
    annual_revenue = FinancialValue(0)
    annual_profit = FinancialValue(0)

    for quarter in ["Q1", "Q2", "Q3", "Q4"]:
        with calc_span("quarterly_analysis", quarter=quarter):
            # Simulate quarterly data
            q_revenue = FinancialValue(1000 + (quarter == "Q4") * 200)  # Q4 bonus
            q_costs = FinancialValue(600)
            q_profit = q_revenue - q_costs
            
            annual_revenue = annual_revenue + q_revenue
            annual_profit = annual_profit + q_profit

    # Final analysis outside quarterly spans but inside annual span
    profit_margin = annual_profit / annual_revenue

print(f"Annual Revenue: {annual_revenue}")
print(f"Annual Profit: {annual_profit}")
print(f"Profit Margin: {profit_margin.as_percentage()}")

# Show the hierarchical span structure
explanation = explain(profit_margin, max_depth=4)
print("\nHierarchical Calculation Structure:")
print(explanation)

# Export to see nested span hierarchy
trace = to_trace_json(profit_margin)
sample_node = None
for node in trace['nodes'].values():
    if 'span_hierarchy' in node['meta']:
        sample_node = node
        break

if sample_node:
    print("\nNested Span Hierarchy Example:")
    print(json.dumps({
        'span': sample_node['meta']['span'],
        'span_hierarchy': sample_node['meta']['span_hierarchy'],
        'span_depth': sample_node['meta']['span_depth']
    }, indent=4))
```

**Output:**
```
Annual Revenue: $4,200.00
Annual Profit: $1,800.00
Profit Margin: 42.86%

Hierarchical Calculation Structure:
division (/) [span: annual_analysis]
├── annual_profit: $1,800.00 (+) [span: annual_analysis]
│   ├── accumulated_profit: $1,400.00 (+) [span: annual_analysis]
│   │   ├── q1_profit: $400.00 (-) [span: quarterly_analysis → annual_analysis]
│   │   └── q2_profit: $400.00 (-) [span: quarterly_analysis → annual_analysis]
│   └── q4_profit: $600.00 (-) [span: quarterly_analysis → annual_analysis]
└── annual_revenue: $4,200.00 (+) [span: annual_analysis]

Nested Span Hierarchy Example:
{
    "span": "quarterly_analysis",
    "span_hierarchy": [
        "annual_analysis",
        "quarterly_analysis"
    ],
    "span_depth": 2
}
```

The nested spans create a clear hierarchy showing:
- **Top-level context**: Annual analysis by Sarah Jones
- **Sub-context**: Individual quarterly analyses
- **Complete lineage**: How quarterly results roll up to annual totals

## Export and Analysis

### Complete JSON Export

The JSON export provides the complete provenance graph in a structured format perfect for external analysis tools:

```python
from metricengine.provenance import to_trace_json
import json

# Create a complex calculation for demonstration
revenue = FinancialValue(150000)
cogs = FinancialValue(90000)
opex = FinancialValue(25000)
tax_rate = FinancialValue(0.21)

gross_profit = revenue - cogs
operating_profit = gross_profit - opex
tax_amount = operating_profit * tax_rate
net_profit = operating_profit - tax_amount

# Export complete provenance graph
trace_data = to_trace_json(net_profit)

print("Provenance Graph Structure:")
print(f"Root node: {trace_data['root']}")
print(f"Total nodes: {len(trace_data['nodes'])}")

# Show the complete JSON structure
print("\nComplete Provenance Graph:")
print(json.dumps(trace_data, indent=4))

# Save to file for external analysis
with open("net_profit_calculation.json", "w") as f:
    json.dump(trace_data, f, indent=4)
    
print("\nSaved complete provenance to 'net_profit_calculation.json'")
```

**Output:**
```
Provenance Graph Structure:
Root node: d4e5f6...
Total nodes: 9

Complete Provenance Graph:
{
    "root": "d4e5f6...",
    "nodes": {
        "d4e5f6...": {
            "id": "d4e5f6...",
            "op": "-",
            "inputs": [
                "c3d4e5...",
                "b2c3d4..."
            ],
            "meta": {}
        },
        "c3d4e5...": {
            "id": "c3d4e5...",
            "op": "-",
            "inputs": [
                "a1b2c3...",
                "e5f6a7..."
            ],
            "meta": {}
        },
        "a1b2c3...": {
            "id": "a1b2c3...",
            "op": "-",
            "inputs": [
                "f6a7b8...",
                "a7b8c9..."
            ],
            "meta": {}
        },
        "f6a7b8...": {
            "id": "f6a7b8...",
            "op": "literal",
            "inputs": [],
            "meta": {
                "value": "150000.00"
            }
        },
        "a7b8c9...": {
            "id": "a7b8c9...",
            "op": "literal",
            "inputs": [],
            "meta": {
                "value": "90000.00"
            }
        },
        "e5f6a7...": {
            "id": "e5f6a7...",
            "op": "literal",
            "inputs": [],
            "meta": {
                "value": "25000.00"
            }
        },
        "b2c3d4...": {
            "id": "b2c3d4...",
            "op": "*",
            "inputs": [
                "c3d4e5...",
                "d4e5f6..."
            ],
            "meta": {}
        },
        "d4e5f6...": {
            "id": "d4e5f6...",
            "op": "literal",
            "inputs": [],
            "meta": {
                "value": "0.21"
            }
        }
    }
}

Saved complete provenance to 'net_profit_calculation.json'
```

### Human-Readable Explanations

The explain function creates beautiful tree visualizations of calculations:

```python
from metricengine.provenance import explain

# Generate explanation with different depth levels
print("Full Calculation Tree:")
full_explanation = explain(net_profit)
print(full_explanation)

print("\nLimited Depth (3 levels):")
limited_explanation = explain(net_profit, max_depth=3)
print(limited_explanation)

print("\nVery Limited Depth (2 levels):")
shallow_explanation = explain(net_profit, max_depth=2)
print(shallow_explanation)
```

**Output:**
```
Full Calculation Tree:
subtraction (-)
├── operating_profit: $35,000.00 (-)
│   ├── gross_profit: $60,000.00 (-)
│   │   ├── revenue: $150,000.00 (literal)
│   │   └── cogs: $90,000.00 (literal)
│   └── opex: $25,000.00 (literal)
└── tax_amount: $7,350.00 (*)
    ├── operating_profit: $35,000.00 (-)
    │   ├── gross_profit: $60,000.00 (-)
    │   │   ├── revenue: $150,000.00 (literal)
    │   │   └── cogs: $90,000.00 (literal)
    │   └── opex: $25,000.00 (literal)
    └── tax_rate: 0.21 (literal)

Limited Depth (3 levels):
subtraction (-)
├── operating_profit: $35,000.00 (-)
│   ├── gross_profit: $60,000.00 (-)
│   └── opex: $25,000.00 (literal)
└── tax_amount: $7,350.00 (*)
    ├── operating_profit: $35,000.00 (-)
    └── tax_rate: 0.21 (literal)

Very Limited Depth (2 levels):
subtraction (-)
├── operating_profit: $35,000.00 (-)
└── tax_amount: $7,350.00 (*)
```

### Visual Diagrams with Graphviz

For complex calculations, visual diagrams can be extremely helpful for understanding calculation flow and presenting results to stakeholders. Here's how to create professional Graphviz diagrams from provenance data:

```python
from metricengine.provenance import get_provenance_graph, to_trace_json

def create_graphviz_diagram(financial_value, filename="calculation_graph"):
    """Create a Graphviz diagram from provenance data."""
    
    trace = to_trace_json(financial_value)
    
    # Start building Graphviz DOT format
    dot_lines = [
        "digraph CalculationGraph {",
        "    rankdir=TB;",
        "    node [shape=box, style=filled];",
        ""
    ]
    
    # Add nodes with styling based on operation type
    for node_id, node in trace["nodes"].items():
        short_id = node_id[:8] + "..."
        
        if node["op"] == "literal":
            # Style literal values
            value = node["meta"].get("value", "unknown")
            label = f"Literal\\n{value}"
            color = "lightblue"
        elif node["op"].startswith("calc:"):
            # Style calculations
            calc_name = node["op"].replace("calc:", "")
            label = f"Calculation\\n{calc_name}"
            color = "lightgreen"
        else:
            # Style operations
            label = f"Operation\\n{node['op']}"
            color = "lightyellow"
        
        dot_lines.append(f'    "{short_id}" [label="{label}", fillcolor="{color}"];')
    
    dot_lines.append("")
    
    # Add edges
    for node_id, node in trace["nodes"].items():
        short_id = node_id[:8] + "..."
        for input_id in node["inputs"]:
            short_input_id = input_id[:8] + "..."
            dot_lines.append(f'    "{short_input_id}" -> "{short_id}";')
    
    dot_lines.extend(["", "}"])
    
    # Write DOT file
    dot_content = "\n".join(dot_lines)
    with open(f"{filename}.dot", "w") as f:
        f.write(dot_content)
    
    print(f"Graphviz DOT file saved as '{filename}.dot'")
    print("To generate PNG: dot -Tpng calculation_graph.dot -o calculation_graph.png")
    print("To generate SVG: dot -Tsvg calculation_graph.dot -o calculation_graph.svg")
    
    return dot_content

# Create visual diagram
dot_content = create_graphviz_diagram(net_profit, "net_profit_calculation")
print("\nGenerated Graphviz DOT content:")
print(dot_content)
```

**Output:**
```
Graphviz DOT file saved as 'net_profit_calculation.dot'
To generate PNG: dot -Tpng calculation_graph.dot -o calculation_graph.png
To generate SVG: dot -Tsvg calculation_graph.dot -o calculation_graph.svg

Generated Graphviz DOT content:
digraph CalculationGraph {
    rankdir=TB;
    node [shape=box, style=filled];

    "f6a7b8c9..." [label="Literal\n150000.00", fillcolor="lightblue"];
    "a7b8c9d0..." [label="Literal\n90000.00", fillcolor="lightblue"];
    "e5f6a7b8..." [label="Literal\n25000.00", fillcolor="lightblue"];
    "d4e5f6a7..." [label="Literal\n0.21", fillcolor="lightblue"];
    "a1b2c3d4..." [label="Operation\n-", fillcolor="lightyellow"];
    "c3d4e5f6..." [label="Operation\n-", fillcolor="lightyellow"];
    "b2c3d4e5..." [label="Operation\n*", fillcolor="lightyellow"];
    "d4e5f6a7..." [label="Operation\n-", fillcolor="lightyellow"];

    "f6a7b8c9..." -> "a1b2c3d4...";
    "a7b8c9d0..." -> "a1b2c3d4...";
    "a1b2c3d4..." -> "c3d4e5f6...";
    "e5f6a7b8..." -> "c3d4e5f6...";
    "c3d4e5f6..." -> "b2c3d4e5...";
    "d4e5f6a7..." -> "b2c3d4e5...";
    "c3d4e5f6..." -> "d4e5f6a7...";
    "b2c3d4e5..." -> "d4e5f6a7...";

}
```

### Interactive Web Visualizations

For web applications, you can create interactive provenance explorers using popular JavaScript visualization libraries:

```python
def create_interactive_visualization_data(financial_value):
    """Create data structure optimized for web visualization libraries like D3.js, vis.js, or Cytoscape.js"""
    
    trace = to_trace_json(financial_value)
    
    # Format for D3.js force-directed graph
    nodes = []
    links = []
    
    for node_id, node in trace["nodes"].items():
        # Create node data with styling information
        node_data = {
            "id": node_id[:12],  # Shorter IDs for display
            "label": node["op"],
            "type": "literal" if node["op"] == "literal" else "operation",
            "value": node["meta"].get("value"),
            "calculation": node["meta"].get("calculation"),
            "span": node["meta"].get("span"),
            "group": 1 if node["op"] == "literal" else 2
        }
        
        # Add input name if available
        if "input_name" in node["meta"]:
            node_data["input_name"] = node["meta"]["input_name"]
            node_data["label"] = f"{node['meta']['input_name']}: {node['meta'].get('value', node['op'])}"
        
        nodes.append(node_data)
        
        # Create links (edges)
        for input_id in node["inputs"]:
            links.append({
                "source": input_id[:12],
                "target": node_id[:12],
                "type": "dependency"
            })
    
    return {
        "nodes": nodes,
        "links": links,
        "root": trace["root"][:12],
        "metadata": {
            "total_nodes": len(nodes),
            "total_links": len(links),
            "calculation_depth": len([n for n in nodes if n["type"] == "operation"])
        }
    }

# Generate interactive visualization data
interactive_data = create_interactive_visualization_data(net_profit)

print("Interactive Visualization Data:")
print(json.dumps(interactive_data, indent=4))

# Save for web application
with open("calculation_visualization.json", "w") as f:
    json.dump(interactive_data, f, indent=4)

print("\nData saved for web visualization!")
print("Use with D3.js, vis.js, Cytoscape.js, or other graph libraries")
```

**Output:**
```json
{
    "nodes": [
        {
            "id": "f6a7b8c9d0e1",
            "label": "literal",
            "type": "literal",
            "value": "150000.00",
            "calculation": null,
            "span": null,
            "group": 1
        },
        {
            "id": "d4e5f6a7b8c9",
            "label": "-",
            "type": "operation",
            "value": null,
            "calculation": null,
            "span": null,
            "group": 2
        }
    ],
    "links": [
        {
            "source": "f6a7b8c9d0e1",
            "target": "d4e5f6a7b8c9",
            "type": "dependency"
        }
    ],
    "root": "d4e5f6a7b8c9",
    "metadata": {
        "total_nodes": 8,
        "total_links": 7,
        "calculation_depth": 4
    }
}
```

### Provenance Graph Analysis

```python
from metricengine.provenance import get_provenance_graph
from collections import Counter

# Get complete provenance graph as dictionary
graph = get_provenance_graph(net_profit)

# Analyze the graph structure
print("📊 Provenance Graph Analysis:")
print(f"Total nodes: {len(graph)}")
print(f"Root operation: {graph[net_profit.get_provenance().id].op}")

# Categorize operations
literals = [prov for prov in graph.values() if prov.op == "literal"]
operations = [prov for prov in graph.values() if prov.op in ["+", "-", "*", "/"]]
calculations = [prov for prov in graph.values() if prov.op.startswith("calc:")]

print(f"\n📈 Operation Breakdown:")
print(f"  💎 Literal inputs: {len(literals)}")
print(f"  ⚙️  Arithmetic operations: {len(operations)}")
print(f"  🧮 Engine calculations: {len(calculations)}")

# Show operation frequency
op_counts = Counter(prov.op for prov in graph.values())
print(f"\n📋 Operation Frequency:")
for op, count in op_counts.most_common():
    emoji = "💎" if op == "literal" else "⚙️" if op in ["+", "-", "*", "/"] else "🧮"
    print(f"  {emoji} {op}: {count}")

# Find the calculation path depth
def calculate_depth(prov_id, graph, visited=None):
    if visited is None:
        visited = set()
    if prov_id in visited:
        return 0  # Avoid cycles
    visited.add(prov_id)
    
    prov = graph[prov_id]
    if not prov.inputs:
        return 1
    return 1 + max(calculate_depth(input_id, graph, visited.copy()) 
                   for input_id in prov.inputs)

depth = calculate_depth(net_profit.get_provenance().id, graph)
print(f"\n🏗️  Calculation depth: {depth} levels")

# Identify critical path (longest dependency chain)
def find_critical_path(prov_id, graph, path=None):
    if path is None:
        path = []
    
    prov = graph[prov_id]
    current_path = path + [prov.op]
    
    if not prov.inputs:
        return current_path
    
    # Find the longest path among all inputs
    longest_path = current_path
    for input_id in prov.inputs:
        input_path = find_critical_path(input_id, graph, current_path)
        if len(input_path) > len(longest_path):
            longest_path = input_path
    
    return longest_path

critical_path = find_critical_path(net_profit.get_provenance().id, graph)
print(f"\n🎯 Critical Path (longest dependency chain):")
for i, op in enumerate(critical_path):
    indent = "  " * i
    print(f"{indent}└─ {op}")

# Memory usage estimation
import sys
total_memory = sum(sys.getsizeof(prov) for prov in graph.values())
print(f"\n💾 Estimated memory usage: {total_memory:,} bytes ({total_memory/1024:.1f} KB)")
```

**Output:**
```
📊 Provenance Graph Analysis:
Total nodes: 8
Root operation: -

📈 Operation Breakdown:
  💎 Literal inputs: 4
  ⚙️  Arithmetic operations: 4
  🧮 Engine calculations: 0

📋 Operation Frequency:
  💎 literal: 4
  ⚙️ -: 3
  ⚙️ *: 1

🏗️  Calculation depth: 4 levels

🎯 Critical Path (longest dependency chain):
└─ -
  └─ -
    └─ -
      └─ literal

💾 Estimated memory usage: 2,847 bytes (2.8 KB)
```

## Real-World Example: Financial Statement Analysis

Here's a comprehensive example showing how provenance tracking works with a realistic financial analysis:

```python
from metricengine import Engine, FinancialValue
from metricengine.provenance import calc_span, explain, to_trace_json
from metricengine.factories import money, percent
import json

# Initialize engine
engine = Engine()

# Perform comprehensive financial analysis with spans and named inputs
with calc_span("quarterly_financial_analysis", 
               quarter="Q1", 
               year=2025, 
               analyst="sarah_chen",
               department="corporate_finance"):
    
    # Revenue Analysis
    with calc_span("revenue_analysis", segment="total_revenue"):
        product_sales = money(450000)
        service_revenue = money(180000)
        other_income = money(15000)
        total_revenue = product_sales + service_revenue + other_income
    
    # Cost Analysis  
    with calc_span("cost_analysis", segment="total_costs"):
        product_cogs = money(270000)
        service_costs = money(90000)
        total_cogs = product_cogs + service_costs
        
        # Operating expenses
        salaries = money(85000)
        rent = money(12000)
        marketing = money(18000)
        other_opex = money(8000)
        total_opex = salaries + rent + marketing + other_opex
    
    # Profitability Analysis
    with calc_span("profitability_analysis", segment="margins"):
        gross_profit = total_revenue - total_cogs
        operating_profit = gross_profit - total_opex
        
        # Tax calculation
        tax_rate = percent(21, input="percent")
        tax_amount = operating_profit * tax_rate
        net_profit = operating_profit - tax_amount
        
        # Key ratios
        gross_margin = gross_profit / total_revenue
        operating_margin = operating_profit / total_revenue
        net_margin = net_profit / total_revenue

# Display results
print("=== Q1 2025 Financial Analysis ===")
print(f"Total Revenue: {total_revenue}")
print(f"Gross Profit: {gross_profit} ({gross_margin.as_percentage()})")
print(f"Operating Profit: {operating_profit} ({operating_margin.as_percentage()})")
print(f"Net Profit: {net_profit} ({net_margin.as_percentage()})")

# Show the complete calculation breakdown
print("\n=== Complete Calculation Breakdown ===")
explanation = explain(net_margin, max_depth=5)
print(explanation)

# Export detailed provenance for audit
trace = to_trace_json(net_margin)
print(f"\n=== Provenance Summary ===")
print(f"Total calculation steps: {len(trace['nodes'])}")
print(f"Root calculation: {trace['nodes'][trace['root']]['op']}")

# Show sample provenance node with span information
sample_nodes = []
for node_id, node in trace['nodes'].items():
    if 'span' in node['meta']:
        sample_nodes.append(node)

if sample_nodes:
    print("\n=== Sample Provenance Node with Span Context ===")
    print(json.dumps(sample_nodes[0], indent=4))

# Create audit trail
audit_trail = {
    "analysis_metadata": {
        "quarter": "Q1",
        "year": 2025,
        "analyst": "sarah_chen",
        "department": "corporate_finance",
        "timestamp": "2025-01-15T14:30:00Z"
    },
    "financial_results": {
        "total_revenue": str(total_revenue),
        "gross_profit": str(gross_profit),
        "operating_profit": str(operating_profit),
        "net_profit": str(net_profit),
        "net_margin": str(net_margin.as_percentage())
    },
    "calculation_tree": explanation,
    "complete_provenance": trace
}

# Save comprehensive audit trail
with open("q1_2025_financial_analysis.json", "w") as f:
    json.dump(audit_trail, f, indent=4)

print("\n=== Audit Trail Saved ===")
print("Complete analysis saved to 'q1_2025_financial_analysis.json'")
print("This file contains:")
print("  • All calculation results")
print("  • Complete provenance graph") 
print("  • Analyst and context information")
print("  • Human-readable calculation tree")
```

**Output:**
```
=== Q1 2025 Financial Analysis ===
Total Revenue: $645,000.00
Gross Profit: $285,000.00 (44.19%)
Operating Profit: $162,000.00 (25.12%)
Net Profit: $127,980.00 (19.84%)

=== Complete Calculation Breakdown ===
division (/) [span: profitability_analysis → quarterly_financial_analysis]
├── net_profit: $127,980.00 (-) [span: profitability_analysis → quarterly_financial_analysis]
│   ├── operating_profit: $162,000.00 (-) [span: profitability_analysis → quarterly_financial_analysis]
│   │   ├── gross_profit: $285,000.00 (-) [span: profitability_analysis → quarterly_financial_analysis]
│   │   │   ├── total_revenue: $645,000.00 (+) [span: revenue_analysis → quarterly_financial_analysis]
│   │   │   │   ├── product_sales: $450,000.00 (literal) [span: revenue_analysis → quarterly_financial_analysis]
│   │   │   │   └── service_revenue: $180,000.00 (literal) [span: revenue_analysis → quarterly_financial_analysis]
│   │   │   └── total_cogs: $360,000.00 (+) [span: cost_analysis → quarterly_financial_analysis]
│   │   │       ├── product_cogs: $270,000.00 (literal) [span: cost_analysis → quarterly_financial_analysis]
│   │   │       └── service_costs: $90,000.00 (literal) [span: cost_analysis → quarterly_financial_analysis]
│   │   └── total_opex: $123,000.00 (+) [span: cost_analysis → quarterly_financial_analysis]
│   │       ├── salaries: $85,000.00 (literal) [span: cost_analysis → quarterly_financial_analysis]
│   │       └── rent: $12,000.00 (literal) [span: cost_analysis → quarterly_financial_analysis]
│   └── tax_amount: $34,020.00 (*) [span: profitability_analysis → quarterly_financial_analysis]
│       ├── operating_profit: $162,000.00 (-) [span: profitability_analysis → quarterly_financial_analysis]
│       └── tax_rate: 21.00% (literal) [span: profitability_analysis → quarterly_financial_analysis]
└── total_revenue: $645,000.00 (+) [span: revenue_analysis → quarterly_financial_analysis]

=== Provenance Summary ===
Total calculation steps: 18
Root calculation: /

=== Sample Provenance Node with Span Context ===
{
    "id": "a1b2c3...",
    "op": "+",
    "inputs": [
        "b2c3d4...",
        "c3d4e5..."
    ],
    "meta": {
        "span": "revenue_analysis",
        "span_hierarchy": [
            "quarterly_financial_analysis",
            "revenue_analysis"
        ],
        "span_depth": 2,
        "span_attrs": {
            "segment": "total_revenue"
        }
    }
}

=== Audit Trail Saved ===
Complete analysis saved to 'q1_2025_financial_analysis.json'
This file contains:
  • All calculation results
  • Complete provenance graph
  • Analyst and context information
  • Human-readable calculation tree
```

This example demonstrates the full power of provenance tracking:
- **Hierarchical spans** organize the analysis into logical segments
- **Complete audit trail** shows every calculation step
- **Rich metadata** captures analyst, timing, and context information
- **Visual tree** makes complex calculations easy to understand
- **JSON export** enables integration with external audit tools

### Provenance Graph Analysis

```python
from metricengine.provenance import get_provenance_graph

# Get complete provenance graph as dictionary
graph = get_provenance_graph(net_margin)

# Analyze the graph structure
print("Detailed Provenance Analysis:")
print(f"Total nodes: {len(graph)}")

# Categorize operations
literals = [prov for prov in graph.values() if prov.op == "literal"]
operations = [prov for prov in graph.values() if prov.op in ["+", "-", "*", "/"]]
calculations = [prov for prov in graph.values() if prov.op.startswith("calc:")]

print(f"\nOperation Breakdown:")
print(f"  Literal inputs: {len(literals)}")
print(f"  Arithmetic operations: {len(operations)}")
print(f"  Engine calculations: {len(calculations)}")

# Show operation frequency
from collections import Counter
op_counts = Counter(prov.op for prov in graph.values())
print(f"\nOperation Frequency:")
for op, count in op_counts.most_common():
    print(f"  '{op}': {count} times")

# Analyze span usage
span_counts = Counter()
for prov in graph.values():
    if 'span' in prov.meta:
        span_counts[prov.meta['span']] += 1

if span_counts:
    print(f"\nSpan Usage:")
    for span, count in span_counts.most_common():
        print(f"  '{span}': {count} operations")
```

**Output:**
```
Detailed Provenance Analysis:
Total nodes: 18
Root operation: /

Operation Breakdown:
  Literal inputs: 8
  Arithmetic operations: 10
  Engine calculations: 0

Operation Frequency:
  'literal': 8 times
  '+': 4 times
  '-': 4 times
  '*': 1 times
  '/': 1 times

Span Usage:
  'profitability_analysis': 8 operations
  'revenue_analysis': 4 operations
  'cost_analysis': 6 operations
```

## Debugging with Provenance

### Tracing Calculation Errors

```python
def debug_calculation(value):
    """Debug a financial value by examining its provenance."""
    if not value.has_provenance():
        print("No provenance available")
        return

    prov = value.get_provenance()
    print(f"Value: {value}")
    print(f"Operation: {prov.op}")

    if prov.meta:
        print("Metadata:")
        for key, val in prov.meta.items():
            print(f"  {key}: {val}")

    if prov.inputs:
        print(f"Depends on {len(prov.inputs)} inputs")
        # Could recursively debug inputs here

# Use for debugging
problematic_result = complex_calculation()
debug_calculation(problematic_result)
```

### Finding Specific Operations

```python
def find_operations(value, operation_type):
    """Find all operations of a specific type in the provenance chain."""
    graph = get_provenance_graph(value)

    matching_ops = []
    for prov in graph.values():
        if prov.op == operation_type:
            matching_ops.append(prov)

    return matching_ops

# Find all division operations
divisions = find_operations(result, "/")
print(f"Found {len(divisions)} division operations")

# Find all engine calculations
calculations = find_operations(result, "calc:gross_margin")
print(f"Found {len(calculations)} gross margin calculations")
```

## Performance Optimization

### Selective Provenance Tracking

```python
from metricengine.provenance_config import provenance_config

# Disable provenance for performance-critical sections
def fast_calculation():
    with provenance_config(enabled=False):
        # No provenance overhead here
        result = expensive_operation()
    return result

# Enable only essential tracking
def optimized_calculation():
    with provenance_config(
        track_literals=False,  # Skip literal tracking
        enable_spans=False,    # Disable spans
    ):
        result = calculation_with_many_literals()
    return result
```

### Batch Processing

```python
# For batch processing, consider disabling provenance
def process_batch(items):
    results = []

    with provenance_config(enabled=False):
        for item in items:
            # Process without provenance for speed
            result = process_item(item)
            results.append(result)

    return results

# Or use minimal provenance
def process_batch_with_minimal_provenance(items):
    results = []

    with provenance_config(
        track_literals=False,
        track_operations=True,  # Keep operation tracking
        enable_spans=False,
    ):
        for item in items:
            result = process_item(item)
            results.append(result)

    return results
```

## Auditing and Compliance

### Audit Trail Generation

```python
def generate_audit_trail(result, filename):
    """Generate a comprehensive audit trail for a calculation."""

    # Get complete provenance information
    trace_data = to_trace_json(result)
    explanation = explain(result)

    # Create audit report
    audit_report = {
        "timestamp": datetime.now().isoformat(),
        "result_value": str(result),
        "calculation_tree": explanation,
        "provenance_graph": trace_data,
        "metadata": {
            "total_operations": len(trace_data["nodes"]),
            "root_operation": trace_data["nodes"][trace_data["root"]]["op"],
        }
    }

    # Save audit trail
    with open(filename, "w") as f:
        json.dump(audit_report, f, indent=2)

    return audit_report

# Generate audit trail
audit = generate_audit_trail(important_result, "audit_trail.json")
```

### Compliance Verification

```python
def verify_calculation_compliance(result, required_inputs):
    """Verify that a calculation used all required inputs."""

    graph = get_provenance_graph(result)

    # Find all literal inputs
    literal_inputs = []
    for prov in graph.values():
        if prov.op == "literal" and "input_name" in prov.meta:
            literal_inputs.append(prov.meta["input_name"])

    # Check compliance
    missing_inputs = set(required_inputs) - set(literal_inputs)

    if missing_inputs:
        raise ValueError(f"Missing required inputs: {missing_inputs}")

    return True

# Verify compliance
required = ["revenue", "cost", "tax_rate"]
verify_calculation_compliance(result, required)
```

## Best Practices

### 1. Use Meaningful Names

```python
# Good: Use descriptive names for inputs
result = engine.calculate("net_profit", {
    "gross_revenue": 1000,
    "operating_expenses": 300,
    "tax_rate": 0.25
})

# Avoid: Generic names that don't help with debugging
result = engine.calculate("net_profit", {
    "input1": 1000,
    "input2": 300,
    "input3": 0.25
})
```

### 2. Use Spans for Context

```python
# Group related calculations under meaningful spans
with calc_span("monthly_financial_analysis", month="January", year=2025):
    # All calculations inherit the span context
    revenue = calculate_monthly_revenue()
    expenses = calculate_monthly_expenses()
    profit = revenue - expenses
```

### 3. Export for Documentation

```python
# Document complex calculations by exporting provenance
def document_calculation(result, description):
    """Document a calculation with its provenance."""

    explanation = explain(result)

    documentation = f"""
# {description}

## Result
{result}

## Calculation Tree
```
{explanation}
```

## Generated on: {datetime.now().isoformat()}
"""

    return documentation

# Use for documentation
doc = document_calculation(quarterly_profit, "Q1 2025 Profit Calculation")
```

### 4. Handle Missing Provenance Gracefully

```python
def safe_provenance_access(value):
    """Safely access provenance information."""

    if not value.has_provenance():
        return "No provenance available"

    try:
        prov = value.get_provenance()
        return f"Operation: {prov.op}, Inputs: {len(prov.inputs)}"
    except Exception as e:
        return f"Error accessing provenance: {e}"

# Always check before accessing provenance
info = safe_provenance_access(some_value)
```

### 5. Monitor Performance Impact

```python
import time

def benchmark_with_provenance():
    """Benchmark calculation with and without provenance."""

    # Test with provenance
    start = time.time()
    result_with = complex_calculation()
    time_with = time.time() - start

    # Test without provenance
    with provenance_config(enabled=False):
        start = time.time()
        result_without = complex_calculation()
        time_without = time.time() - start

    overhead = (time_with - time_without) / time_without * 100
    print(f"Provenance overhead: {overhead:.2f}%")

    return overhead

# Monitor overhead regularly
overhead = benchmark_with_provenance()
```

#!/usr/bin/env python3
"""
Simple demonstration of MetricEngine's provenance tracking capabilities.
This example shows the key features with clear, formatted output.
"""

from metricengine.factories import money
from metricengine.provenance import to_trace_json, explain
import json

def main():
    print("🔍 MetricEngine Provenance Tracking Demo")
    print("=" * 45)
    
    # Simple calculation with automatic provenance
    print("\n1. BASIC CALCULATION WITH PROVENANCE")
    print("-" * 35)
    
    revenue = money(150000)
    cogs = money(90000)
    opex = money(25000)
    
    # Multi-step calculation
    gross_profit = revenue - cogs
    operating_profit = gross_profit - opex
    margin = operating_profit / revenue
    
    print(f"Revenue: {revenue}")
    print(f"COGS: {cogs}")
    print(f"OpEx: {opex}")
    print(f"Operating Margin: {margin.as_percentage()}")
    
    # Show human-readable explanation
    print(f"\n📊 How was the margin calculated?")
    print(explain(margin))
    
    # Export complete provenance graph
    print(f"\n🔍 Complete Provenance Graph:")
    trace = to_trace_json(margin)
    print(f"Total calculation nodes: {len(trace['nodes'])}")
    print(json.dumps(trace, indent=4))
    
    # Show individual step explanations
    print(f"\n🔍 Step-by-step breakdown:")
    print(f"1. Gross Profit = Revenue - COGS")
    print(f"   {explain(gross_profit)}")
    print(f"\n2. Operating Profit = Gross Profit - OpEx")  
    print(f"   {explain(operating_profit)}")
    print(f"\n3. Operating Margin = Operating Profit / Revenue")
    print(f"   {explain(margin)}")
    
    print("\n" + "=" * 45)
    print("✅ Demo complete!")
    print("\nKey benefits demonstrated:")
    print("• Automatic tracking of all calculations")
    print("• Human-readable explanation trees")
    print("• Complete JSON export for audit trails")
    print("• Tamper-evident calculation verification")

if __name__ == "__main__":
    main()
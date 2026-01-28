#!/usr/bin/env python3
"""
Interactive Visualization Generator - Creates an interactive HTML dashboard
with timeline slider for the repair scheduling system.
Visualizes product assignments from stock (based on tau_p dynamics) and shipping schedules.
"""

import sys
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.preproc import parse_repair_data
from mip_model import RepairMIP


def create_interactive_dashboard(model, preprocessor, output_file="scheduling_dashboard.html"):
    """
    Create an interactive HTML dashboard with timeline slider.
    
    Args:
        model: Optimized RepairMIP model
        preprocessor: DataPreprocessor with loaded data
        output_file: Output HTML filename
    """
    print(f"\nCreating interactive dashboard: {output_file}")
    
    # Get data
    schedule = model.get_product_schedule()
    batches = model.get_batch_schedule()
    basket_status = model.get_daily_basket_status()
    
    # Setup
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    num_days = len(model.T)
    colors = {'0': '#3498db', '1': '#e74c3c'}  # Blue and Red for repairers
    
    # Pre-calculate data
    arrivals_per_day = {t: 0 for t in range(num_days)}
    for t in range(num_days):
        count = 0
        for r in model.R:
             if (r, t) in model.vars['a']:
                 count += int(round(model.vars['a'][r, t].X))
        arrivals_per_day[t] = count
    
    # Calculate solution statistics
    total_products = len(model.P)
    total_batches = len(batches)
    total_shipped = sum(batch['batch_size'] for batch in batches)
    total_remaining = sum(basket_status[(r, num_days-1)]['accumulated'] for r in model.R)
    
    # Cost metrics
    total_repair_cost = sum(item['repair_cost'] for item in schedule)
    total_shipping_cost = sum(batch['shipping_cost'] for batch in batches)
    total_emissions = sum(batch['emissions'] for batch in batches)
    total_quality_drop = sum(item['quality_drop'] for item in schedule)
    avg_quality_drop = total_quality_drop / total_products if total_products > 0 else 0
    
    # Lead time metrics - use model's l variable for max_lead_time
    lead_times = [item['lead_time'] for item in schedule]
    avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
    max_lead_time = model.vars['l'].X  # Use the model's l variable
    min_lead_time = min(lead_times) if lead_times else 0
    
    # Repairer utilization
    products_per_repairer = {}
    for item in schedule:
        r = item['repairer_id']
        products_per_repairer[r] = products_per_repairer.get(r, 0) + 1
        
    # Calculate average repair cost per repairer
    avg_repair_cost = {}
    repair_costs_sum = {}
    repair_counts = {}
    
    for (d, p, r), cost in model.chi_dpr_r.items():
        repair_costs_sum[r] = repair_costs_sum.get(r, 0) + cost
        repair_counts[r] = repair_counts.get(r, 0) + 1
        
    for r in model.R:
        if r in repair_costs_sum and repair_counts.get(r, 0) > 0:
            avg_repair_cost[r] = repair_costs_sum[r] / repair_counts[r]
        else:
            avg_repair_cost[r] = 0.0
    
    # Objective value
    objective_value = (
        model.alpha1 * max_lead_time +
        model.alpha2 * total_shipping_cost +
        model.alpha3 * total_quality_drop +
        model.alpha4 * total_repair_cost +
        model.alpha5 * total_emissions
    )
    
    # Create statistics HTML - Pure black theme
    stats_html = f"""
    <div style="background: #000000; 
                padding: 40px 20px; 
                margin: 0 0 30px 0; 
                border-bottom: 1px solid #1a1a1a;">
        <h1 style="color: #ffffff; 
                   text-align: center; 
                   margin: 0 0 40px 0; 
                   font-size: 32px;
                   font-weight: 300;
                   letter-spacing: -0.5px;">
            Solution Statistics
        </h1>
        
        <div style="max-width: 900px; margin: 0 auto;">
            <!-- KPI Cards -->
            <div style="display: grid; 
                        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
                        gap: 20px; 
                        margin-bottom: 40px;">

                <!-- Product Inventory Card -->
                <div style="background: #1a1a1a; 
                            padding: 30px; 
                            border-radius: 8px; 
                            border: 1px solid #2a2a2a;">
                    <div style="font-size: 13px; 
                                color: #888; 
                                margin-bottom: 15px;
                                text-transform: uppercase;
                                letter-spacing: 1px;">Product Status</div>
                    <div style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #888; font-size: 11px; text-transform: uppercase;">Total Products</span>
                            <span style="color: #ffffff; font-size: 14px; font-weight: 300;">{total_products}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #888; font-size: 11px; text-transform: uppercase;">Shipped</span>
                            <span style="color: #ffffff; font-size: 14px; font-weight: 300;">{total_shipped}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #888; font-size: 11px; text-transform: uppercase;">In Baskets</span>
                            <span style="color: #ffffff; font-size: 14px; font-weight: 300;">{total_remaining}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Cost Breakdown Card -->
                <div style="background: #1a1a1a; 
                            padding: 30px; 
                            border-radius: 8px; 
                            border: 1px solid #2a2a2a;">
                    <div style="font-size: 13px; 
                                color: #888; 
                                margin-bottom: 15px;
                                text-transform: uppercase;
                                letter-spacing: 1px;">Cost Breakdown</div>
                    
                    <div style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #888; font-size: 11px; text-transform: uppercase;">Lead Time Cost</span>
                            <span style="color: #ffffff; font-size: 14px; font-weight: 300;">{model.alpha1 * max_lead_time:.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #888; font-size: 11px; text-transform: uppercase;">Shipping Cost</span>
                            <span style="color: #ffffff; font-size: 14px; font-weight: 300;">{model.alpha2 * total_shipping_cost:.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #888; font-size: 11px; text-transform: uppercase;">Quality Drop Cost</span>
                            <span style="color: #ffffff; font-size: 14px; font-weight: 300;">{model.alpha3 * total_quality_drop:.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #888; font-size: 11px; text-transform: uppercase;">Repair Cost</span>
                            <span style="color: #ffffff; font-size: 14px; font-weight: 300;">{model.alpha4 * total_repair_cost:.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #888; font-size: 11px; text-transform: uppercase;">Emissions Cost</span>
                            <span style="color: #ffffff; font-size: 14px; font-weight: 300;">{model.alpha5 * total_emissions:.2f}</span>
                        </div>
                    </div>
                    
                    <div style="border-top: 1px solid #2a2a2a; padding-top: 15px; margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <span style="color: #ffffff; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 500;">Total Objective</span>
                            <span style="color: #ffffff; font-size: 24px; font-weight: 200;">{objective_value:.2f}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Avg Lead Time Card -->
                <div style="background: #1a1a1a; 
                            padding: 30px; 
                            border-radius: 8px; 
                            border: 1px solid #2a2a2a;">
                    <div style="font-size: 13px; 
                                color: #888; 
                                margin-bottom: 8px;
                                text-transform: uppercase;
                                letter-spacing: 1px;">Avg Lead Time</div>
                    <div style="font-size: 42px; 
                                font-weight: 200; 
                                color: #ffffff;">{avg_lead_time:.1f} days</div>
                    <div style="color: #888; font-size: 12px; margin-top: 8px;">Range: {min_lead_time}-{max_lead_time} days</div>
                </div>
                
                <!-- Quality Drop Card -->
                <div style="background: #1a1a1a; 
                            padding: 30px; 
                            border-radius: 8px; 
                            border: 1px solid #2a2a2a;">
                    <div style="font-size: 13px; 
                                color: #888; 
                                margin-bottom: 8px;
                                text-transform: uppercase;
                                letter-spacing: 1px;">Quality Drop</div>
                    <div style="font-size: 42px; 
                                font-weight: 200; 
                                color: #ffffff;">{avg_quality_drop*100:.1f}%</div>
                    <div style="color: #888; font-size: 12px; margin-top: 8px;">Average per product</div>
                </div>
                
                <!-- Total Emissions Card -->
                <div style="background: #1a1a1a; 
                            padding: 30px; 
                            border-radius: 8px; 
                            border: 1px solid #2a2a2a;">
                    <div style="font-size: 13px; 
                                color: #888; 
                                margin-bottom: 8px;
                                text-transform: uppercase;
                                letter-spacing: 1px;">Total Emissions</div>
                    <div style="font-size: 42px; 
                                font-weight: 200; 
                                color: #ffffff;">{total_emissions:.2f} kg</div>
                    <div style="color: #888; font-size: 12px; margin-top: 8px;">CO₂ Equivalent</div>
                </div>
            </div>
            
            <!-- Detailed Breakdown -->
            <div class="detail-grid">
                
                <!-- Repairer Stats -->
                <div class="stat-card">
                    <h3 style="color: #ffffff; 
                               margin: 0 0 25px 0; 
                               font-size: 20px; 
                               font-weight: 400;
                               letter-spacing: -0.3px;">
                        Repairer Utilization
                    </h3>
                    <div style="margin: 0;">
                        {''.join([f'''
                        <div style="margin-bottom: 20px; border-bottom: 1px solid #2a2a2a; padding-bottom: 20px;">
                            <div style="display: flex; 
                                        justify-content: space-between; 
                                        margin-bottom: 8px;">
                                <span style="color: #888; font-size: 14px;">{preprocessor.repairers[r].name if r in preprocessor.repairers else f'Repairer {r}'}</span>
                                <span style="font-weight: 300; color: #ffffff; font-size: 14px;">
                                    {products_per_repairer.get(r, 0)} products 
                                    ({(products_per_repairer.get(r, 0)/total_products*100) if total_products > 0 else 0:.1f}%)
                                </span>
                            </div>
                            <div style="background: #0a0a0a; 
                                        height: 4px; 
                                        border-radius: 2px; 
                                        overflow: hidden;
                                        margin-bottom: 12px;">
                                <div style="background: #ffffff; 
                                            height: 100%; 
                                            width: {(products_per_repairer.get(r, 0)/total_products*100) if total_products > 0 else 0:.1f}%;
                                            transition: width 0.3s ease;"></div>
                            </div>
                            <div style="display: flex; gap: 20px; flex-wrap: wrap;" class="repairer-stats">
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span style="color: #666; font-size: 12px;">Basket Capacity:</span>
                                    <span style="color: #ccc; font-size: 12px;">{model.beta_r[r]} items</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span style="color: #666; font-size: 12px;">Repair Time:</span>
                                    <span style="color: #ccc; font-size: 12px;">{model.lambda_r[r]} days</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span style="color: #666; font-size: 12px;">Trip Emissions:</span>
                                    <span style="color: #ccc; font-size: 12px;">{model.pi_r[r]} kg CO₂</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span style="color: #666; font-size: 12px;">Avg Repair Cost:</span>
                                    <span style="color: #ccc; font-size: 12px;">€{avg_repair_cost.get(r, 0):.2f}</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span style="color: #666; font-size: 12px;">Shipping Cost:</span>
                                    <span style="color: #ccc; font-size: 12px;">€{model.chi_r_s[r]:.2f}</span>
                                </div>
                            </div>
                        </div>
                        ''' for r in model.R])}
                    </div>
                </div>
                
                <!-- Lead Time Distribution -->
                <div class="stat-card">
                    <h3 style="color: #ffffff; 
                               margin: 0 0 25px 0; 
                               font-size: 20px; 
                               font-weight: 400;
                               letter-spacing: -0.3px;">
                        Lead Time Distribution
                    </h3>
                    <div style="margin: 0;">
                        <div style="display: flex; 
                                    justify-content: space-between; 
                                    margin: 16px 0;
                                    padding-bottom: 16px;
                                    border-bottom: 1px solid #2a2a2a;">
                            <span style="color: #888; font-size: 14px;">Minimum</span>
                            <span style="font-weight: 300; color: #ffffff; font-size: 16px;">{min_lead_time:.1f} days</span>
                        </div>
                        <div style="display: flex; 
                                    justify-content: space-between; 
                                    margin: 16px 0;
                                    padding-bottom: 16px;
                                    border-bottom: 1px solid #2a2a2a;">
                            <span style="color: #888; font-size: 14px;">Average</span>
                            <span style="font-weight: 300; color: #ffffff; font-size: 16px;">{avg_lead_time:.1f} days</span>
                        </div>
                        <div style="display: flex; 
                                    justify-content: space-between; 
                                    margin: 16px 0;
                                    padding-bottom: 16px;
                                    border-bottom: 1px solid #2a2a2a;">
                            <span style="color: #888; font-size: 14px;">Maximum</span>
                            <span style="font-weight: 300; color: #ffffff; font-size: 16px;">{max_lead_time:.1f} days</span>
                        </div>
                        <div style="display: flex; 
                                    justify-content: space-between; 
                                    margin: 16px 0;">
                            <span style="color: #888; font-size: 14px;">Constraint</span>
                            <span style="font-weight: 300; color: #666; font-size: 16px;">{model.tau} days max</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """


    
    # Create figure with subplots - 2 rows now
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            'Basket Status',
            'Batch Shipments'
        ),
        vertical_spacing=0.12,
        specs=[[{"type": "bar"}], [{"type": "bar"}]]
    )
    
    # Create frames for animation
    frames = []
    
    for current_day in range(num_days):
        # SUB-FRAME A: ALLOCATION (Basket increases with a_rt)
        frame_data_a = []
        
        # Basket status pre-shipment: b[t-1] + a[t]
        for r in model.R:
            repairer = preprocessor.repairers.get(r)
            repairer_name = repairer.name if repairer else f'Repairer {r}'
            
            basket_levels = []
            for day in range(num_days):
                if day < current_day:
                    # Final level of previous days
                    basket_levels.append(basket_status.get((r, day), {}).get('accumulated', 0))
                elif day == current_day:
                    # Current day: previous day + new assignments
                    prev = basket_status.get((r, day-1), {}).get('accumulated', 0) if day > 0 else 0
                    newly = basket_status.get((r, day), {}).get('newly_assigned', 0)
                    basket_levels.append(prev + newly)
                else:
                    basket_levels.append(0)
            
            basket_trace = go.Bar(
                x=[days[i % 7] for i in range(num_days)],
                y=basket_levels,
                name=repairer_name,
                marker=dict(color=colors[str(r)], line=dict(color='black', width=1)),
                text=[str(level) if level > 0 and day <= current_day else '' for day, level in enumerate(basket_levels)],
                textposition='outside',
                legendgroup=repairer_name,
                showlegend=True,
                hoverinfo='none'
            )
            frame_data_a.append(basket_trace)
            
        # Shipments: Show shipments up to day t-1
        for r in model.R:
            shipment_sizes = [0] * num_days
            for batch in batches:
                if batch['repairer_id'] == r and batch['shipping_day'] < current_day:
                    shipment_sizes[batch['shipping_day']] = batch['batch_size']
            
            shipment_trace = go.Bar(
                x=[days[i % 7] for i in range(num_days)],
                y=shipment_sizes,
                marker=dict(color=colors[str(r)], line=dict(color='black', width=1)),
                text=[str(s) if s > 0 else '' for s in shipment_sizes],
                textposition='outside',
                showlegend=False,
                hoverinfo='none'
            )
            frame_data_a.append(shipment_trace)
            
        frames.append(go.Frame(data=frame_data_a, name=f"{current_day}_alloc"))
        
        # SUB-FRAME B: SHIPMENT (Basket decreases, shipment appears)
        frame_data_b = []
        
        # Basket status post-shipment: b[t]
        for r in model.R:
            repairer = preprocessor.repairers.get(r)
            repairer_name = repairer.name if repairer else f'Repairer {r}'
            
            basket_levels = []
            for day in range(num_days):
                if day <= current_day:
                    basket_levels.append(basket_status.get((r, day), {}).get('accumulated', 0))
                else:
                    basket_levels.append(0)
            
            basket_trace = go.Bar(
                x=[days[i % 7] for i in range(num_days)],
                y=basket_levels,
                name=repairer_name,
                marker=dict(color=colors[str(r)], line=dict(color='black', width=1)),
                text=[str(level) if level > 0 and day <= current_day else '' for day, level in enumerate(basket_levels)],
                textposition='outside',
                legendgroup=repairer_name,
                showlegend=True,
                hoverinfo='none'
            )
            frame_data_b.append(basket_trace)
            
        # Shipments: include current day t shipment
        for r in model.R:
            shipment_sizes = [0] * num_days
            for batch in batches:
                if batch['repairer_id'] == r and batch['shipping_day'] <= current_day:
                    shipment_sizes[batch['shipping_day']] = batch['batch_size']
            
            shipment_trace = go.Bar(
                x=[days[i % 7] for i in range(num_days)],
                y=shipment_sizes,
                marker=dict(color=colors[str(r)], line=dict(color='black', width=1)),
                text=[str(s) if s > 0 and day <= current_day else '' for day, s in enumerate(shipment_sizes)],
                textposition='outside',
                showlegend=False,
                hoverinfo='none'
            )
            frame_data_b.append(shipment_trace)
            
        frames.append(go.Frame(data=frame_data_b, name=f"{current_day}_ship"))
    
    # Initial data (day 0)
    initial_data = frames[0].data
    
    # Add traces to figure
    # We need as many traces as there are in each frame (R traces for Basket, R traces for Shipment)
    for i, trace in enumerate(initial_data):
        if i < len(model.R):
            fig.add_trace(trace, row=1, col=1)
        else:
            fig.add_trace(trace, row=2, col=1)
    
    # Update layout - Black theme matching reference
    fig.update_layout(
        title={
            'text': 'Optimal Repair Scheduling',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#ffffff', 'family': '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto'}
        },
        height=750,
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        margin=dict(t=100, b=80, l=60, r=60),
        showlegend=True,
        font=dict(color='#ffffff', family='-apple-system, BlinkMacSystemFont, Segoe UI, Roboto'),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="right",
            x=1,
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='#333',
            borderwidth=1
        ),
        sliders=[{
            'active': 0,
            'yanchor': 'top',
            'y': -0.05,
            'xanchor': 'center',
            'currentvalue': {
                'visible': False
            },
            'pad': {'b': 10, 't': 50},
            'len': 0.4,
            'x': 0.5,
            'steps': [
                {
                    'args': [[f.name], {
                        'frame': {'duration': 1200, 'redraw': True},
                        'mode': 'immediate',
                        'transition': {'duration': 400, 'easing': 'cubic-in-out'}
                    }],
                    'label': f"{days[int(f.name.split('_')[0]) % 7]}",
                    'method': 'animate'
                }
                for f in frames
            ]
        }],
        barmode='group',
        bargap=0.5,
        bargroupgap=0.25,
        dragmode=False,
        hovermode=False
    )
    
    # Update axes - Black theme with fixed Y ranges
    fig.update_xaxes(title_text="", row=1, col=1, gridcolor='#1a1a1a', gridwidth=0.5, color='#ffffff', fixedrange=True, showline=True, linewidth=1, linecolor='#333')
    fig.update_xaxes(title_text="Day of Week", row=2, col=1, gridcolor='#1a1a1a', gridwidth=0.5, color='#ffffff', fixedrange=True, showline=True, linewidth=1, linecolor='#333')
    
    fig.update_yaxes(title_text="Basket Size", row=1, col=1, gridcolor='#1a1a1a', gridwidth=0.5, color='#ffffff', fixedrange=True, showline=True, linewidth=1, linecolor='#333', range=[0, 30])
    fig.update_yaxes(title_text="Batch Size", row=2, col=1, gridcolor='#1a1a1a', gridwidth=0.5, color='#ffffff', fixedrange=True, showline=True, linewidth=1, linecolor='#333', range=[0, 30])
    
    # Add frames
    fig.frames = frames
    
    # Save to HTML with statistics - minimal controls
    html_string = fig.to_html(
        config={
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': [
                'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d',
                'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 
                'hoverCompareCartesian', 'toggleSpikelines'
            ],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'scheduling_dashboard',
                'height': 900,
                'width': 1400,
                'scale': 2
            },
            'scrollZoom': False
        },
        include_plotlyjs='cdn'
    )
    
    # Try to embed GIF as base64 if it exists
    gif_html = ""
    try:
        import base64
        gif_path = "scheduling_animation.gif"
        if os.path.exists(gif_path):
            with open(gif_path, "rb") as gif_file:
                encoded_string = base64.b64encode(gif_file.read()).decode('utf-8')
                
            gif_html = f"""
            <style>
                .mobile-gif-container {{
                    display: none;
                }}
                /* Increased breakpoint to cover high-res phones and landscape mode */
                @media (max-width: 1024px) {{
                    .mobile-gif-container {{
                        display: block !important;
                        margin: 20px auto;
                        padding: 0 15px;
                    }}
                }}
            </style>
            <script>
                // JavaScript fallback: Force show on mobile user agents regardless of screen width
                document.addEventListener('DOMContentLoaded', function() {{
                    var isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
                    if (isMobile) {{
                        var container = document.querySelector('.mobile-gif-container');
                        if (container) {{
                            container.style.display = 'block';
                            // Optional: hide plotly on strict mobile devices to save memory
                            // var plotlyDiv = document.querySelector('.plotly-graph-div');
                            // if (plotlyDiv) plotlyDiv.style.display = 'none';
                        }}
                    }}
                }});
            </script>
            <div class="mobile-gif-container" style="max-width: 900px;">
                <div style="background: #1a1a1a; 
                            padding: 15px; 
                            border-radius: 8px; 
                            border: 1px solid #2a2a2a;
                            text-align: center;">
                    <h3 style="color: #ffffff; margin: 0 0 15px 0; font-size: 18px; font-weight: 400;">
                        Mobile Animation Preview
                    </h3>
                    <img src="data:image/gif;base64,{encoded_string}" 
                         alt="Scheduling Animation" 
                         style="max-width: 100%; height: auto; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                    <p style="color: #666; font-size: 12px; margin-top: 10px;">
                        (Detected Mobile Device)
                    </p>
                </div>
            </div>
            """
    except Exception as e:
        print(f"Could not embed GIF: {e}")
    
    # Inject statistics HTML before the plot with responsive design
    html_parts = html_string.split('<body>')
    if len(html_parts) == 2:
        # Add responsive meta tag and styles
        responsive_head = '''
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @media (max-width: 768px) {
                .stats-grid { grid-template-columns: 1fr !important; }
                .detail-grid { grid-template-columns: 1fr !important; }
                h1 { font-size: 24px !important; }
                .kpi-card { padding: 20px !important; }
                .detail-card { padding: 20px !important; }
            }
        </style>
        '''
        html_parts[0] = html_parts[0].replace('</head>', responsive_head + '</head>')
        
        # Apply dark theme to entire page and wrap plotly chart in container
        # Find the plotly div and wrap it
        body_content = html_parts[1]
        # Add wrapper div around plotly content
        plotly_wrapper_start = '<div style="max-width: 900px; margin: 0 auto; padding: 0 20px;">'
        plotly_wrapper_end = '</div>'
        
        # Insert wrapper before first script tag (plotly content starts there)
        if '<script' in body_content:
            script_pos = body_content.find('<script')
            body_content = body_content[:script_pos] + plotly_wrapper_start + body_content[script_pos:]
            # Close wrapper before </body>
            body_content = body_content.replace('</body>', plotly_wrapper_end + '</body>')
        
        # Add auto-play script when chart is visible
        auto_play_script = '''
        <script>
        // Auto-play animation when chart becomes visible
        document.addEventListener('DOMContentLoaded', function() {
            const chartDiv = document.querySelector('.plotly-graph-div');
            let hasPlayed = false;
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !hasPlayed) {
                        hasPlayed = true;
                        // Start animation after a short delay
                        setTimeout(() => {
                            Plotly.animate(chartDiv.id, null, {
                                frame: {duration: 1000, redraw: true},
                                transition: {duration: 500},
                                fromcurrent: true,
                                mode: 'immediate'
                            });
                        }, 500);
                    }
                });
            }, {
                threshold: 0.3 // Trigger when 30% of chart is visible
            });
            
            if (chartDiv) {
                observer.observe(chartDiv);
            }
        });
        </script>
        '''
        
        # Insert auto-play script before </body>
        body_content = body_content.replace('</body>', auto_play_script + '</body>')
        
        html_string = html_parts[0] + '''<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
                     margin: 0; 
                     padding: 0; 
                     background: #000000; 
                     color: #ffffff;">''' + gif_html + body_content.replace('</body>', stats_html + '</body>')
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_string)
    
    print(f"Interactive dashboard created: {output_file}")
    


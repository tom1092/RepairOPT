import csv
import sys
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import numpy as np

from utils.preproc import parse_repair_data
from mip_model import RepairMIP


def generate_scheduling_csv(model, preprocessor, output_file="scheduling_results.csv"):
    """Generate CSV with scheduling results."""
    print(f"\nGenerating scheduling CSV: {output_file}")
    
    schedule = model.get_product_schedule()
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Product ID', 'Product Category', 'Product Color',
            'Assigned Repairer', 'Repairer Name',
            'Repair Cost (€)', 'Quality Drop (%)', 'Emissions (g CO2)',
            'Time in Stock (days)', 'Shipping Day', 'Lead Time (days)', 'Return Day'
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in schedule:
            product = preprocessor.products.get(item['product_id'])
            repairer = preprocessor.repairers.get(item['repairer_id'])
            return_day = item['shipping_day'] + model.lambda_r[item['repairer_id']]
            
            writer.writerow({
                'Product ID': item['product_id'],
                'Product Category': product.category if product else 'Unknown',
                'Product Color': product.color if product else 'Unknown',
                'Assigned Repairer': item['repairer_id'],
                'Repairer Name': repairer.name if repairer else 'Unknown',
                'Repair Cost (€)': f"{item['repair_cost']:.2f}",
                'Quality Drop (%)': f"{item['quality_drop'] * 100:.2f}",
                'Emissions (g CO2)': f"{item['emissions']:.2f}",
                'Time in Stock (days)': f"{item['time_in_stock']:.1f}",
                'Shipping Day': item['shipping_day'],
                'Lead Time (days)': f"{item['lead_time']:.1f}",
                'Return Day': return_day
            })
    
    print(f"CSV generated with {len(schedule)} products")


def create_gif_animation(model, preprocessor, duration_seconds=60):
    """Create GIF animation of the scheduling system."""
    print(f"\nCreating GIF animation ({duration_seconds}s)...")
    
    schedule = model.get_product_schedule()
    batches = model.get_batch_schedule()
    basket_status = model.get_daily_basket_status()
    
    # Setup
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))
    fig.suptitle('Optimal Repair Scheduling - Weekly Simulation', fontsize=16, fontweight='bold')
    
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
    repairer_colors = {r: colors[r % len(colors)] for r in model.R}
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    num_days = len(model.T)
    
    # Animation parameters
    fps = 10  # Lower FPS for smaller file
    total_frames = duration_seconds * fps
    frames_per_day = total_frames // num_days
    
    # Pre-calculate data
    arrivals_per_day = {t: 0 for t in range(num_days)}
    for t in range(num_days):
        count = 0
        for r in model.R:
             if (r, t) in model.vars['a']:
                 count += int(round(model.vars['a'][r, t].X))
        arrivals_per_day[t] = count
    
    def animate(frame):
        current_day = min(frame // frames_per_day, num_days - 1)
        day_progress = (frame % frames_per_day) / frames_per_day
        
        for ax in [ax1, ax2, ax3]:
            ax.clear()
        
        # Plot 1: Product Arrivals
        ax1.set_title(f'Product Arrivals - Day {current_day} ({days[current_day % 7]})', 
                     fontsize=12, fontweight='bold')
        ax1.set_xlabel('Day')
        ax1.set_ylabel('Number of Products')
        ax1.set_xlim(-0.5, num_days - 0.5)
        ax1.set_ylim(0, max(arrivals_per_day.values()) + 5)
        ax1.grid(True, alpha=0.3)
        
        for day in range(current_day + 1):
            alpha = 1.0 if day < current_day else day_progress
            ax1.bar(day, arrivals_per_day[day], color='#3498db', alpha=alpha, edgecolor='black')
            if arrivals_per_day[day] > 0:
                ax1.text(day, arrivals_per_day[day] + 0.5, str(arrivals_per_day[day]), 
                        ha='center', va='bottom', fontweight='bold')
        
        ax1.set_xticks(range(num_days))
        ax1.set_xticklabels([days[i % 7] for i in range(num_days)])
        
        # Plot 2: Basket Status
        ax2.set_title(f'Basket Status by Repairer - Day {current_day}', 
                     fontsize=12, fontweight='bold')
        ax2.set_xlabel('Day')
        ax2.set_ylabel('Products in Basket')
        ax2.set_xlim(-0.5, num_days - 0.5)
        ax2.grid(True, alpha=0.3)
        
        bar_width = 0.35
        repairer_names = ['A', 'B']
        for idx, r in enumerate(model.R):
            repairer = preprocessor.repairers.get(r)
            #repairer_name = repairer.name if repairer else f'Repairer {r}'
            repairer_name = repairer_names[idx]
            
            basket_levels = []
            for day in range(num_days):
                if day <= current_day:
                    level = basket_status.get((r, day), {}).get('accumulated', 0)
                    basket_levels.append(level)
                else:
                    basket_levels.append(0)
            
            positions = np.arange(num_days) + idx * bar_width - bar_width / 2
            ax2.bar(positions, basket_levels, bar_width, 
                   label=repairer_name, color=repairer_colors[r], 
                   alpha=0.8, edgecolor='black')
            
            capacity = model.beta_r[r]
            ax2.axhline(y=capacity, color=repairer_colors[r], 
                       linestyle='--', alpha=0.5, linewidth=1)
        
        ax2.set_xticks(range(num_days))
        ax2.set_xticklabels([days[i % 7] for i in range(num_days)])
        ax2.legend(loc='upper left', fontsize=9)
        
        # Plot 3: Batch Shipments
        ax3.set_title(f'Batch Shipments - Day {current_day}', 
                     fontsize=12, fontweight='bold')
        ax3.set_xlabel('Day')
        ax3.set_ylabel('Batch Size')
        ax3.set_xlim(-0.5, num_days - 0.5)
        ax3.grid(True, alpha=0.3)
        
        for batch in batches:
            if batch['shipping_day'] <= current_day:
                r = batch['repairer_id']
                day = batch['shipping_day']
                size = batch['batch_size']
                alpha = 1.0 if day < current_day else day_progress
                
                ax3.bar(day + r * bar_width - bar_width / 2, size, bar_width,
                       color=repairer_colors[r], alpha=alpha, edgecolor='black', linewidth=2)
                
                if alpha > 0.5:
                    ax3.annotate('', xy=(day, size + 1), xytext=(day, size + 3),
                               arrowprops=dict(arrowstyle='->', color='red', lw=2))
                    ax3.text(day, size + 3.5, f'{size}', ha='center', 
                            fontsize=8, fontweight='bold', color='red')
        
        ax3.set_xticks(range(num_days))
        ax3.set_xticklabels([days[i % 7] for i in range(num_days)])
        
        # Current day indicator
        for ax in [ax1, ax2, ax3]:
            ax.axvline(x=current_day, color='red', linestyle='--', 
                      linewidth=2, alpha=0.7)
        
        plt.tight_layout()
        return []
    
    print(f"Rendering {total_frames} frames at {fps} FPS...")
    anim = FuncAnimation(fig, animate, frames=total_frames,
                        interval=1000/fps, blit=True, repeat=True)
    
    output_file = 'scheduling_animation.gif'
    print(f"Saving to {output_file}... (this may take 2-3 minutes)")
    anim.save(output_file, writer='pillow', fps=fps)
    
    plt.close('all')
    print(f"✓ Animation saved: {output_file}")

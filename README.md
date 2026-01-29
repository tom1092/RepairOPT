# A Mixed-Integer Programming Model for Sustainable Textile Repair Operations

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Gurobi](https://img.shields.io/badge/Solver-Gurobi%209.5%2B-red)
[![license](https://img.shields.io/badge/license-apache_2.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)

## Authors

<table>
<tr>
<td width="50%">

**Tommaso Aldinucci**  
Department of Information Engineering,  
University of Florence, Italy  
[tommaso.aldinucci@unifi.it](mailto:tommaso.aldinucci@unifi.it)

</td>
<td width="50%">

**Paola Cappanera**  
Department of Information Engineering,  
University of Florence, Italy  
[paola.cappanera@unifi.it](mailto:paola.cappanera@unifi.it)

</td>
</tr>
<tr>
<td width="50%">

**Filippo Visintin**  
Department of Industrial Engineering,  
University of Florence, Italy  
[filippo.visintin@unifi.it](mailto:filippo.visintin@unifi.it)

</td>
<td width="50%">

**Vittoria Rosseti**  
Department of Industrial Engineering,  
University of Florence, Italy  
[vittoria.rosseti@edu.unifi.it](mailto:vittoria.rosseti@edu.unifi.it)

</td>
</tr>
</table>

---

## Overview

This repository implements an optimization model for the assignment and scheduling of product repairs across multiple repair centers. The model minimizes total costs, lead times, quality degradation, and carbon emissions while respecting capacity constraints and service level requirements.

## Setup & Installation

> This project uses **Conda** for environment management. If you don't have it installed, you can download it here:
>
> - [**Miniconda**](https://docs.conda.io/en/latest/miniconda.html) (Lightweight, recommended)
> - [**Anaconda**](https://www.anaconda.com/products/individual) (Full featured)

### 1. Create Conda Environment

It is recommended (but not mandatory) to use a dedicated Conda environment to avoid dependency conflicts:

```bash
# Create a new environment
conda create -n repairopt python=3.9

# Activate the environment
conda activate repairopt
```

### 2. Install Dependencies

Install all required Python packages using `pip`:

```bash
# Install from requirements.txt
pip install -r requirements.txt
```

> **Note:** A valid **Gurobi License** is required. Ensure your `gurobipy` is correctly configured with your license key (`grbgetkey`).

---

## Usage

### Run Optimization

Execute the main script to solve the MIP model and generate outputs:

```bash
python3 main.py
```

Generate scheduling results and visualization:

Output files:

- `scheduling_results.csv` - Detailed scheduling table
- `scheduling_dashboard.html` - interactive HTML dashboard with temporal controls and statistics [**SEE HERE A PREVIEW**](https://tom1092.github.io/RepairOPT/scheduling_dashboard.html)

## Repository Structure

```
RepairOPT/
├── DOM/                    Domain object models
│   ├── product.py         Product entity
│   ├── defect.py          Defect entity
│   ├── repairer.py        Repairer entity
│   ├── customer.py        Customer entity
│   └── repair_request.py  Repair request entity
│
├── data/                   Input data files
│   ├── products.csv
│   ├── defects.csv
│   ├── repairers.csv
│   ├── customers.csv
│   └── repair_request.csv
│
├── utils/                  Utility modules
│   └── preproc.py         Data preprocessing and parsing
│
├── mip_model.py           MIP optimization model
├── main.py                Main execution script
├── generate_results.py    Results generator
└── create_interactive_dashboard.py  Dashboard generator
```

---

## Results

### Scheduling Table

The `scheduling_results.csv` file contains the following fields:

| Field | Description |
|-------|-------------|
| Product ID | Unique product identifier |
| Product Category | Product classification (Sweater, Trousers, etc.) |
| Product Color | Color of the product |
| Assigned Repairer | Numeric ID of the assigned repairer |
| Repairer Name | Name of the repair facility |
| Repair Cost (€) | Total repair cost in EUR |
| Quality Drop (%) | Quality degradation percentage |
| Emissions (g CO2) | Carbon emissions in grams of CO₂ |
| Time in Stock (days) | Days the product spent in stock before optimization |
| Shipping Day | Day when the product is shipped to the repairer |
| Lead Time (days) | Total processing time from arrival to return |
| Return Day | Calculated day of return to the customer |

---

## Customization

You can customize the optimization parameters and objective function weights by modifying the `utils/preproc.py` file. Look for the following tagged sections:

### 1. Model Parameters

Under the `#------------PARAMS------------#` section, you can define:

- **`tau`**: Maximum admissible lead time for all products.
- **`beta_r`**: Maximum batch capacity for each repairer.
- **`lambda_r`**: Fixed lead time (days) for each repairer facility.
- **`chi_r_s`**: Shipping cost per batch for each repairer.
- **`pi_r`**: CO₂ emissions per batch shipment.
- **Repair Costs & Quality**: Customize `chi_dpr_r` (unit costs) and `sigma_dpr` (quality degradation) logic.

### 2. Objective Weights

Under the `#------------OBJECTIVE PARAMS------------#` section, you can adjust the weights ($\alpha_1$ to $\alpha_5$) to prioritize different optimization goals:

- `alpha1`: Lead Time
- `alpha2`: Shipping Cost
- `alpha3`: Quality Degradation
- `alpha4`: Repair Cost
- `alpha5`: Carbon Emissions

---

## License

This project is licensed under the Apache License 2.0.

Copyright (c) 2026 Tommaso Aldinucci.

---

## References

For methodological details see the attached `draft.pdf`.

---

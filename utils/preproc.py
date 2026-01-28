import csv
import os
from typing import Dict, List, Tuple, Set
import sys
from random import uniform, randint, seed
import numpy as np

# Set random seed for reproducibility
seed(42)
np.random.seed(42)

# Add parent directory to path to import DOM classes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DOM.product import Product
from DOM.defect import Defect
from DOM.repairer import Repairer
from DOM.repair_request import RepairRequest
from DOM.customer import Customer


class DataPreprocessor:
    """
    Parser for reading CSV files and building DOM objects and data structures
    required by the MIP model.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the preprocessor with the data directory path.
        
        Args:
            data_dir: Path to the directory containing CSV files
        """
        self.data_dir = data_dir
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # DOM objects
        self.products: Dict[int, Product] = {}
        self.defects: Dict[int, Defect] = {}
        self.repairers: Dict[int, Repairer] = {}
        self.customers: Dict[int, Customer] = {}
        self.repair_requests: Dict[int, RepairRequest] = {}
    

    def load_all_data(self) -> Tuple[Dict, Dict, List, List, List, List, Dict, Dict]:
        """
        Load all CSV files and build the data structures needed for the MIP model.
        
        Returns:
            Tuple containing:
            - products: Dict[int, Product] - Product objects indexed by ID
            - repair_requests: Dict[int, RepairRequest] - RepairRequest objects
            - R: List[int] - Set of repairer IDs
            - D: List[int] - Set of defect IDs
            - P: List[int] - Set of product IDs
            - T: List[int] - Set of time periods
            - D_p: Dict[int, Set[int]] - Mapping product -> set of defects
        """
        # Load all CSV files
        self._load_products()
        self._load_defects()
        self._load_repairers()
        self._load_customers()
        self._load_repair_requests()
        
        # Build index sets
        R = list(self.repairers.keys())
        D = list(self.defects.keys())
        P = list(self.products.keys())
        
        # Build D_p: mapping product -> set of defects
        D_p = self._build_product_defect_mapping()
        
        # Build P_t: mapping time -> products (for simplicity, assume all arrive at t=0)
        # This can be modified based on actual arrival time data
        T = list(range(10))  # Time periods 0-9 (can be adjusted)

        return (
            self.products,
            self.repair_requests,
            R,
            D,
            P,
            T,
            D_p,
        )
    
    def _load_products(self):
        """Load products from products.csv"""
        csv_path = os.path.join(self.base_path, self.data_dir, "products.csv")
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                product = Product(
                    id=int(row['id']),
                    category=row['category'],
                    size=row['size'],
                    color=row['color'],
                    composition=row['composition'],
                    description=row['description']
                )
                self.products[product.id] = product
    
    def _load_defects(self):
        """Load defects from defects.csv"""
        csv_path = os.path.join(self.base_path, self.data_dir, "defects.csv")
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                defect = Defect(
                    id=int(row['id']),
                    description=row['description']
                )
                self.defects[defect.id] = defect
    
    def _load_repairers(self):
        """Load repairers from repairers.csv"""
        csv_path = os.path.join(self.base_path, self.data_dir, "repairers.csv")
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                repairer = Repairer(
                    id=int(row['id']),
                    name=row['name'],
                    specialization=row['specialization'],
                    status=row['status'],
                    contactEmail=row['contactEmail'],
                    notes=row['notes']
                )
                self.repairers[repairer.id] = repairer
    
    def _load_customers(self):
        """Load customers from customers.csv"""
        csv_path = os.path.join(self.base_path, self.data_dir, "customers.csv")
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Skip empty rows
                    if not row['id']:
                        continue
                    customer = Customer(
                        id=int(row['id']),
                        firstName=row['firstName'],
                        lastName=row['lastName'],
                        email=row['email'],
                        phone=row['phone'],
                        address=row['address'],
                        city=row['city'],
                        country=row['country'],
                        registrationDate=row['registrationDate'],
                        customerStatus=row['customerStatus']
                    )
                    self.customers[customer.id] = customer
        except FileNotFoundError:
            print(f"Warning: customers.csv not found, skipping customer data")
    
    def _load_repair_requests(self):
        """Load repair requests from repair_request.csv"""
        csv_path = os.path.join(self.base_path, self.data_dir, "repair_request.csv")
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip empty rows
                if not row['id']:
                    continue
                    
                repair_request = RepairRequest(
                    id=int(row['id']),
                    customerId=int(row['customerId']),
                    productId=int(row['productId']),
                    defectId=int(row['defectId'])
                )
                self.repair_requests[repair_request.id] = repair_request
    
    def _build_product_defect_mapping(self) -> Dict[int, Set[int]]:
        """
        Build mapping from product ID to set of defect IDs.
        
        Returns:
            Dict mapping product ID -> set of defect IDs for that product
        """
        D_p = {p_id: set() for p_id in self.products.keys()}
        
        for req in self.repair_requests.values():
            if req.productId in D_p:
                D_p[req.productId].add(req.defectId)
        
        return D_p
    
    def get_model_parameters(self, num_repairers: int = None) -> Dict:
        """
        Generate sample parameters for the MIP model.
        These are placeholder values and should be replaced with real data.
        
        Args:
            num_repairers: Number of repairers to use (default: all available)
            
        Returns:
            Dictionary containing all model parameters
        """
        if num_repairers is None:
            num_repairers = len(self.repairers)
        
        R = list(range(num_repairers))
        D = list(self.defects.keys())
        P = list(self.products.keys())
        T = list(range(7))
        
        # Build D_p mapping
        D_p = self._build_product_defect_mapping()
        
        


        #------------PARAMS------------#
        #-----HERE YOU CAN SHOULD READ YOUR DATA AND SET THE PARAMS----#

        chi_r_s = {r: 8.0 for r in R}  # Shipping cost per batch (round trip)
        tau = 15 # Maximum lead time

        #tau_p is the stock time of product p is uniform int [0,6]
        tau_p = {p: randint(0, 6) for p in P}  # Product stock times (uniform in [0,6])
        beta_r = {0: 15, 1: 9}  # Batch capacity per repairer
        lambda_r = {0: 12, 1: 6}  # Lead time of repairer
        
        # Quality degradation (0-1 scale)
        sigma_dpr = {}
        for p in P:
            for d in D_p.get(p, []):
                sigma_dpr[d, p, 0] = 0.08  # 8% degradation for Arte del Rammendo
                sigma_dpr[d, p, 1] = 0.05  # 5% degradation for Nicole

        # Unit repair cost
        chi_dpr_r = {}
        for p in P:
            for d in D_p.get(p, []):
                #Base cost for Nicole sampled from a normal distribution with mean 10 and std 2
                chi_dpr_r[d, p, 1] = np.random.normal(10, 2)
                #Arte del rammendo is Nicole plus uniform int in (2, 10)
                chi_dpr_r[d, p, 0] = chi_dpr_r[d, p, 1] + randint(2, 10)
        
        # Carbon emissions per batch
        pi_r = {0: 8, 1: 1.360} #8000 g/round trip arte del rammendo, 1360 g/round trip nicole
        

        #------------OBJECTIVE PARAMS------------#
        #-----HERE YOU CAN SHOULD CHANGE FOR SENSITIVITY ANALYSIS----#
        
        alpha1 = 1.0  # Lead time weight
        alpha2 = 1.0  # Shipping cost weight
        alpha3 = 1.0  # Quality degradation weight
        alpha4 = 1.0  # Repair cost weight
        alpha5 = 1.0  # Carbon emission weight
        


        
        return {
            'R': R,
            'D': D,
            'P': P,
            'T': T,
            'D_p': D_p,
            'chi_r_s': chi_r_s,
            'tau': tau,
            'tau_p': tau_p,
            'beta_r': beta_r,
            'lambda_r': lambda_r,
            'sigma_dpr': sigma_dpr,
            'chi_dpr_r': chi_dpr_r,
            'pi_r': pi_r,
            'alpha1': alpha1,
            'alpha2': alpha2,
            'alpha3': alpha3,
            'alpha4': alpha4,
            'alpha5': alpha5
        }


def parse_repair_data(data_dir: str = "data"):
    """
    Main function to parse all repair data and return structures needed for MIP model.
    
    Args:
        data_dir: Path to directory containing CSV files
        
    Returns:
        Tuple containing:
        - preprocessor: DataPreprocessor object with all loaded data
        - model_params: Dictionary with all parameters for MIP model
    """
    preprocessor = DataPreprocessor(data_dir)
    
    # Load all data
    products, repair_requests, R, D, P, T, D_p = preprocessor.load_all_data()
    
    # Get model parameters
    model_params = preprocessor.get_model_parameters()
    
    print(f"Loaded {len(products)} products")
    print(f"Loaded {len(repair_requests)} repair requests")
    print(f"Loaded {len(preprocessor.defects)} defects")
    print(f"Loaded {len(preprocessor.repairers)} repairers")
    
    return preprocessor, model_params

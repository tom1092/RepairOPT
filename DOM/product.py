class Product:
    """
    Represents a single garment or item requiring repair.
    Corresponds to the cleaned 'products.csv' file structure (without customer_id).
    """
    
    def __init__(self, id: int, category: str, size: str, color: str, 
                 composition: str, description: str):
        """
        Initializes a Product object.

        Args:
            id (int): Unique identifier for the product (starts at 0).
            category (str): The type of garment (e.g., Sweater, Cardigan).
            size (str): The size of the product (e.g., M, XL).
            color (str): The color of the product.
            composition (str): The material composition (e.g., 100% cotton).
            description (str): A general description of the product.
        """
        self.id = id
        self.category = category
        self.size = size
        self.color = color
        self.composition = composition
        self.description = description
        
    def __repr__(self):
        """Returns a string representation of the Product object."""
        return f"Product(id={self.id}, category='{self.category}', color='{self.color}')"

    def __str__(self):
        """Returns a string representation of the Product object."""
        return f"Product(id={self.id}, category='{self.category}', color='{self.color}')"
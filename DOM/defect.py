class Defect:
    """
    Represents a type of defect or damage found on a product.
    Corresponds to the 'defects.csv' file structure.
    """
    
    def __init__(self, id: int, description: str):
        """
        Initializes a Defect object.

        Args:
            id (int): Unique identifier for the defect type (starts at 0).
            description (str): A detailed description of the defect (e.g., HoleLessThan1cm).
        """
        self.id = id
        self.description = description

    def __repr__(self):
        """Returns a string representation of the Defect object."""
        return f"Defect(id={self.id}, description='{self.description}')"

    def __str__(self):
        """Returns a string representation of the Defect object."""
        return f"Defect(id={self.id}, description='{self.description}')"


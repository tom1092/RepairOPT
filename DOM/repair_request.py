class RepairRequest:
    """
    Represents a specific repair request, linking the customer, product, and defect.
    Corresponds to the 'repair_request.csv' file structure.
    """
    
    def __init__(self, id: int, customerId: int, productId: int, defectId: int):
        """
        Initializes a RepairRequest object.

        Args:
            id (int): Unique identifier for the repair request itself (starts at 0).
            customerId (int): Foreign key linking to the Customer.id.
            productId (int): Foreign key linking to the Product.id.
            defectId (int): Foreign key linking to the Defect.id.
        """
        self.id = id
        self.customerId = customerId
        self.productId = productId
        self.defectId = defectId

    def __repr__(self):
        """Returns a string representation of the RepairRequest object."""
        return (f"RepairRequest(id={self.id}, customerId={self.customerId}, "
                f"productId={self.productId}, defectId={self.defectId})")

    def __str__(self):
        """Returns a string representation of the RepairRequest object."""
        return (f"RepairRequest(id={self.id}, customerId={self.customerId}, "
                f"productId={self.productId}, defectId={self.defectId})")
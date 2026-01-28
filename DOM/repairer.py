class Repairer:
    """
    Represents an internal repair technician or an external repair center.
    Corresponds to the 'repairers.csv' file structure.
    """
    
    def __init__(self, id: int, name: str, specialization: str, status: str, 
                 contactEmail: str, notes: str):
        """
        Initializes a Repairer object.

        Args:
            id (int): Unique identifier for the repairer (starts at 0).
            name (str): Name of the repairer or center.
            specialization (str): Area of expertise (e.g., Cucitura&Orli, Generale).
            status (str): Current operational status (e.g., Attivo, Inattivo).
            contactEmail (str): Contact email address.
            notes (str): Any relevant notes about the repairer.
        """
        self.id = id
        self.name = name
        self.specialization = specialization
        self.status = status
        self.contactEmail = contactEmail
        self.notes = notes

    def __repr__(self):
        """Returns a string representation of the Repairer object."""
        return f"Repairer(id={self.id}, name='{self.name}', status='{self.status}')"

    def __str__(self):
        """Returns a string representation of the Repairer object."""
        return f"Repairer(id={self.id}, name='{self.name}', status='{self.status}')"
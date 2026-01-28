class Customer:
    """
    Represents a customer in the system.
    Corresponds to the 'customers.csv' file structure.
    """
    
    def __init__(self, id: int, firstName: str, lastName: str, email: str, 
                 phone: str, address: str, city: str, country: str, 
                 registrationDate: str, customerStatus: str):
        """
        Initializes a Customer object.

        Args:
            id (int): Unique identifier for the customer (starts at 0).
            firstName (str): Customer's first name.
            lastName (str): Customer's last name.
            email (str): Customer's email address.
            phone (str): Customer's phone number.
            address (str): Customer's street address.
            city (str): Customer's city.
            country (str): Customer's country.
            registrationDate (str): Date of customer registration (YYYY-MM-DD).
            customerStatus (str): Current status of the customer (e.g., Active, VIP).
        """
        self.id = id
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.phone = phone
        self.address = address
        self.city = city
        self.country = country
        self.registrationDate = registrationDate
        self.customerStatus = customerStatus

    def __repr__(self):
        """Returns a string representation of the Customer object."""
        return f"Customer(id={self.id}, name='{self.firstName} {self.lastName}')"

    def __str__(self):
        """Returns a string representation of the Customer object."""
        return f"Customer(id={self.id}, name='{self.firstName} {self.lastName}')"
        
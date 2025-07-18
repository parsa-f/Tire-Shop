from .models import User,Employee,Admin,Manager,Order,Customer,Product,Size,Brand, ProductsOrder
from sqlalchemy.orm import Session, InstrumentedAttribute
from sqlalchemy import select, exists, func
from .connection import session
from utilities import hashing
from .Exeptions import NationalNumberAlreadyExistsException, UsernameAlreadyExistsException, UsernameNotExistsException, ProductAlreadyExistsException, ProductNotExistsException, CustomerNotExistsException
from datetime import datetime, timedelta

# A generic function to check if a record with a specific value in a specific column exists.
def exist_check(session:Session, by:InstrumentedAttribute, pat):
    """
    Checks if a value exists in a given table column.

    Args:
        session: The database session object.
        by: The SQLAlchemy model attribute (column) to search in (e.g., User.user_name).
        pat: The pattern or value to search for.

    Returns:
        True if the value exists, False otherwise.
    """
    # Creates a subquery to check for the existence of the pattern.
    subq = exists(by).where(by == pat).select()
    # Executes the subquery and returns the boolean result.
    exist_check = session.execute(subq).scalar()
    return exist_check

# Fetches a user from the database by their username.
def user_by_username(db:Session, username:str):
    """
    Retrieves a single user object by their username.

    Args:
        db: The database session object.
        username: The username to search for.

    Raises:
        UsernameNotExistsException: If no user with the given username is found.

    Returns:
        The User object if found.
    """
    query = select(User).where(User.user_name == username)
    user = db.execute(query).first()
    # If the query returns no result, raise an exception.
    if not user or not user[0]:
        raise UsernameNotExistsException(username)
    
    # The result of .first() is a tuple-like Row object, so we return the first element.
    return user[0]

# Fetches a user by their username and a plain-text password.
def user_by_username_pass(session:Session, username:str, passwd:str):
    """
    Finds a user by username and verifies their password.

    Args:
        session: The database session object.
        username: The user's username.
        passwd: The user's plain-text password.

    Returns:
        The User object if the username and password match, otherwise None.
    """
    with session as db:
        # The password is hashed before being used in the query for comparison.
        query = select(User).where(User.user_name == username).where(User.hashed_passwd == hashing(passwd))
        # .scalar() is used to get a single value from the first row of the result.
        user = db.execute(query).scalar()
        return user
    return None

def get_all_users(session:Session):
    """Get all users from the database"""
    query = select(User)
    result = session.execute(query).all()
    # The result is a list of Row objects, so we extract the User object from each row.
    return [user[0] for user in result]

def user_by_national_id_phone(session:Session, national_id:str, phone:str) -> User:
    """Retrieve a user by their national ID and phone number"""
    try:
        query = select(User).where(
            User.national_number == national_id,
            User.phone == phone
        )
        result = session.execute(query).first()
        if result:
            return result[0]  # Return the first element of the tuple (the User object)
        return None
    except Exception as e:
        raise e

# Creates a new user (Admin, Manager, or Employee) in the database.
def create_new_user(session: Session, name:str, lastname:str, phone:str, national_number:str, level_type:str, username:str, passwd:str) -> User:
    """
    Creates a new user with a specific role (Admin, Manager, or Employee).

    Args:
        session: The database session object.
        name: The user's first name.
        lastname: The user's last name.
        phone: The user's phone number.
        national_number: The user's national ID number.
        level_type: The user's role ('admin', 'manager', or 'employee').
        username: The desired username.
        passwd: The desired plain-text password.

    Raises:
        NationalNumberAlreadyExistsException: If the national number is already in use.
        UsernameAlreadyExistsException: If the username is already in use.

    Returns:
        None. The function has a side effect of adding a user to the database.
    """
    level_type = level_type.lower()
    # Create the appropriate user object based on the level_type.
    if level_type == 'admin':
        new_user = Admin(name=name, lastname=lastname, phone=phone, national_number=national_number, user_name=username)
    elif level_type == 'manager':
        new_user = Manager(name=name, lastname=lastname, phone=phone, national_number=national_number, user_name=username)
    elif level_type == 'employee':
        new_user = Employee(name=name, lastname=lastname, phone=phone, national_number=national_number, user_name=username)
    else:
        return None
    
    
    
    with session as db:
        # Check for uniqueness constraints before adding the new user.
        exist_national_id_check = exist_check(session, User.national_number, national_number)
        exist_username_check = exist_check(session, User.user_name, username)

        if exist_national_id_check:
            raise NationalNumberAlreadyExistsException(national_number)
        
        if exist_username_check:
            raise UsernameAlreadyExistsException(username)

        # Hash the password before storing it.
        new_user.hashed_passwd = hashing(passwd)
        db.add(new_user)
        db.commit()
            
    # TODO rais an error that the national code already exist
    # NOTE: This function returns None even on successful creation.
    return None
        

# A simple wrapper to check login credentials.
def login_permission(session, username, passwd) -> bool:
    """
    Checks if a given username and password are valid.

    Returns:
        True if the credentials are correct, False otherwise.
    """
    user = user_by_username_pass(session, username, passwd)
    if user:
        return True
    else:
        return False
    
    
# Retrieves all records from the Employee table.
def get_all_employees(session:Session):
    """
    Fetches all employee records from the database.

    Returns:
        A list of Row objects, where each row contains an Employee object.
    """
    stmt = select(Employee)
    
    content = session.execute(stmt).fetchall()
    return content

# Retrieves all employees and formats them as a list of dictionaries.
def get_all_employees_json(session:Session):
    """
    Fetches all employees and converts their data to a JSON-like format (list of dicts).

    Returns:
        A list of dictionaries, where each dictionary represents an employee.
    """
    rows = get_all_employees(session)
    json = []
    
    # Iterate through the rows and call the to_dict() method on each Employee object.
    for row in rows:
        json.append(row[0].to_dict())
    
    return json

def remove_user_by_username(db:Session, username:str):
    user = user_by_username(db, username)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


def update_user_by_username(
    session: Session,
    username: str,
    name: str = None,
    lastname: str = None,
    phone: str = None,
    national:str = None,
    new_username: str = None,
    password: str = None
) -> User:
    # Fetch the user by current username
    user = user_by_username(session, username)
    if not user:
        raise UsernameNotExistsException(f"Username '{username}' does not exist.")

    # Check if the new username is different and not taken
    if new_username and new_username != user.user_name:
        existing_user = session.query(User).filter(User.user_name == new_username).first()
        if existing_user:
            raise UsernameAlreadyExistsException(f"Username '{new_username}' is already taken.")
        user.user_name = new_username

    # Apply other updates if provided
    if name is not None:
        user.name = name
    if lastname is not None:
        user.lastname = lastname
    if phone is not None:
        user.phone = phone
    if national is not None:
        user.national_number = national
    if password is not None:
        user.hashed_passwd = hashing(password)

    # Save changes
    session.commit()
    session.refresh(user)

    return user

def get_all_username(session=Session):
    
    users = get_all_employees_json(session)
    
    return [user['username'] for user in users]


def create_product(session: Session, brand_name: str, price: float, quantity: int, width: int, ratio: int, rim: int) -> Product:
    is_new_product = False
    # Find or create brand
    brand = session.query(Brand).filter_by(name=brand_name).first()
    if not brand:
        brand = Brand(name=brand_name)
        session.add(brand)
        session.commit()  # Get the brand ID
        is_new_product = True

    # Find or create size
    size = session.query(Size).filter_by(width=width, ratio=ratio, rim=rim).first()
    if not size:
        size = Size(width=width, ratio=ratio, rim=rim)
        session.add(size)
        session.commit()  # Get the size ID
        is_new_product = True

    # Create product
    if not is_new_product:
        raise ProductAlreadyExistsException(f"Product with brand '{brand_name}' and size '{width}/{ratio}/{rim}' already exists.")
    else:
        product = Product(
            brand_id=brand.id,
            size_id=size.id,
            price=price,
            quantity=quantity
        )
        session.add(product)
        session.commit()  # Get the product ID

    return product

def search_product_by_size(session: Session, width: int = None, ratio: int = None, rim: int = None):
    query = session.query(Product).join(Size, Product.size_id == Size.id)
    if width is not None:
        query = query.filter(Size.width == width)
    if ratio is not None:
        query = query.filter(Size.ratio == ratio)
    if rim is not None:
        query = query.filter(Size.rim == rim)
    return query.all()

def search_product_by_brand(session: Session, brand_name: str):
    query = session.query(Product).join(Brand, Product.brand_id == Brand.id).filter(Brand.name == brand_name)
    return query.all()

def search_product_by_size_json(session: Session, width: int = None, ratio: int = None, rim: int = None):
    products = search_product_by_size(session, width, ratio, rim)
    result = []
    for product in products:
        result.append(product.to_dict())
    return result

def search_product_by_brand_json(session: Session, brand_name: str):
    products = search_product_by_brand(session, brand_name)
    result = []
    for product in products:
        result.append(product.to_dict())
    return result

def get_all_products(session: Session):
    return session.query(Product).all()

def get_all_products_json(session: Session):
    products = get_all_products(session)
    return [product.to_dict() for product in products]

def get_product_by_id(session: Session, product_id: int) -> Product:
    product = session.query(Product).filter_by(id=product_id).first()
    if not product:
        raise ProductNotExistsException(product_id)
    return product
def get_product_by_id_json(session: Session, product_id: int) -> dict:
    product = get_product_by_id(session, product_id)
    return product.to_dict()

def delete_product_by_name_and_size(session: Session, brand_name: str, width: int, ratio: int, rim: int) -> bool:
    brand = session.query(Brand).filter_by(name=brand_name).first()
    size = session.query(Size).filter_by(width=width, ratio=ratio, rim=rim).first()
    if not brand or not size:
        return False
    product = session.query(Product).filter_by(brand_id=brand.id, size_id=size.id).first()
    if not product:
        return False
    session.delete(product)
    session.commit()
    return True

def update_product_by_id(session: Session, product_id: int, new_brand_name: str, new_width: int, new_ratio: int, new_rim: int, new_quantity: int, new_price: float) -> Product:
    # Find the product by ID
    product = session.query(Product).filter_by(id=product_id).first()
    if not product:
        raise ProductNotExistsException(f"Product with id '{product_id}' does not exist.")

    # Find or create the new brand
    brand = session.query(Brand).filter_by(name=new_brand_name).first()
    if not brand:
        brand = Brand(name=new_brand_name)
        session.add(brand)
        session.commit()

    # Find or create the new size
    size = session.query(Size).filter_by(width=new_width, ratio=new_ratio, rim=new_rim).first()
    if not size:
        size = Size(width=new_width, ratio=new_ratio, rim=new_rim)
        session.add(size)
        session.commit()

    # Update product's price and quantity
    product.price = new_price
    product.quantity = new_quantity
    
    # Update product's brand and size
    product.brand_id = brand.id
    product.size_id = size.id

    session.commit()
    session.refresh(product)
    return product


def get_all_employee_usernames(session: Session):
    employees = session.query(Employee).all()
    return [employee.user_name for employee in employees]

def get_all_employee_and_manager_usernames(session: Session):
    employees = session.query(Employee).all()
    managers = session.query(Manager).all()
    usernames = [employee.user_name for employee in employees] + [manager.user_name for manager in managers]
    return usernames

def get_all_employee_and_manager(session: Session):
    employees = session.query(Employee).all()
    managers = session.query(Manager).all()
    return employees + managers

def get_all_employee_and_manager_json(session: Session):
    users = get_all_employee_and_manager(session)
    return [user.to_dict() for user in users]



def get_all_customers(session: Session):
    return session.query(Customer).all()

def get_all_customers_json(session: Session):
    customers = get_all_customers(session)
    return [customer.to_dict() for customer in customers]

def get_customer_by_id(session: Session, customer_id: int) -> Customer:
    customer = session.query(Customer).filter_by(id=customer_id).first()
    if not customer:
        raise CustomerNotExistsException(customer_id)
    return customer

def get_customer_by_id_json(session: Session, customer_id: int) -> dict:
    customer = get_customer_by_id(session, customer_id)
    return customer.to_dict()




def create_customer(session: Session, name: str, address: str, phone: str, national_number: str) -> Customer:
    # Check if customer with same national number exists
    exist = exist_check(session, Customer.national_number, national_number)
    if exist:
        raise NationalNumberAlreadyExistsException(national_number)

    # Create new customer
    new_customer = Customer(
        name=name, 
        phone=phone,
        national_number=national_number,
        address=address
    )

    session.add(new_customer)
    session.commit()
    session.refresh(new_customer)
    

def create_order(session: Session, customer: Customer, product: Product, quantity: int) -> Order:
    # Check if customer exists
    if not customer:
        raise ValueError("Customer does not exist.")

    # Check if product exists
    if not product:
        raise ValueError("Product does not exist.")

    # Create new order
    new_order = Order(
        customer=customer,
    )

    session.add(new_order)
    session.commit()
    session.refresh(new_order)

    # Create ProductsOrder association
    products_order = ProductsOrder(
        order_id=new_order.id,
        price=product.price,
        width=product.size.width,
        ratio=product.size.ratio,
        rim=product.size.rim,
        brand=product.brand.name,
        quantity=quantity
    )
    decrease_product_quantity(session, product.id, quantity)  # Decrease product quantity

    session.add(products_order)
    session.commit()

    return new_order


def decrease_product_quantity(session: Session, product_id: int, quantity: int) -> Product:
    product = session.query(Product).filter_by(id=product_id).first()
    if not product:
        raise ProductNotExistsException(product_id)
    
    if product.quantity < quantity:
        raise ValueError("Not enough product quantity available.")
    
    product.quantity -= quantity
    session.commit()
    session.refresh(product)
    
    return product

def check_customer_equal(customer: Customer, name: str, phone: str, national_number: str) -> bool:
    return (customer.name == name and
            customer.phone == phone and
            customer.national_number == national_number)

def get_customer_by_national_id(session: Session, national_id: str) -> Customer:
    customer = session.query(Customer).filter_by(national_number=national_id).first()
    if not customer:
        raise CustomerNotExistsException(national_id)
    return customer

def get_or_create_customer(session: Session, name: str, address: str, phone: str, national_number: str) -> Customer:
    # Try to find existing customer
    try:
        customer = get_customer_by_national_id(session, national_number)
        if not check_customer_equal(customer, name, phone, national_number):
            raise NationalNumberAlreadyExistsException(national_number)
        # If customer exists and matches, return it
        return customer
    except CustomerNotExistsException:
        # Create new customer if not found
        create_customer(session, name, address, phone, national_number)
        return get_customer_by_national_id(session, national_number)

def get_all_orders(session: Session):
    return session.query(Order).all()

def get_all_orders_json(session: Session):
    orders = get_all_orders(session)
    return [order.to_dict() for order in orders]

def get_customers_count(session: Session) -> int:
    return session.query(Customer).count()

def get_sizes_count(session: Session) -> int:
    return session.query(Size).count()

def get_brands_count(session: Session) -> int:
    return session.query(Brand).count()

def get_total_product_quantity(session: Session) -> int:
    return session.query(Product).with_entities(func.sum(Product.quantity)).scalar() or 0

def get_employees_count(session: Session) -> int:
    return session.query(Employee).count()

def get_monthly_sales(session: Session) -> float:
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    total_sales = session.query(
        func.sum(ProductsOrder.price * ProductsOrder.quantity)
    ).join(Order).filter(
        Order.date >= thirty_days_ago
    ).scalar()
    
    return total_sales or 0.0

def get_daily_sales(session: Session) -> float:
    today = datetime.now().date()
    
    total_sales = session.query(
        func.sum(ProductsOrder.price * ProductsOrder.quantity)
    ).join(Order).filter(
        func.date(Order.date) == today
    ).scalar()
    
    return total_sales or 0.0


def admin_exists(session: Session) -> bool:
    return session.query(exists().where(User.type == 'admin')).scalar()
import sqlite3
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import random

logger = logging.getLogger(__name__)

class DatabaseService:
    """SQLite database service for the SQL chatbot"""
    
    def __init__(self, db_path: str = "asset_management.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def init_database(self):
        """Initialize database with schema and sample data"""
        logger.info("Initializing SQLite database...")
        
        try:
            with self.get_connection() as conn:
                # Create tables
                self._create_tables(conn)
                # Insert sample data
                self._insert_sample_data(conn)
                
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create database tables (SQLite compatible)"""
        
        # SQLite compatible schema (adjusted from SQL Server)
        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS Customers (
                CustomerId INTEGER PRIMARY KEY AUTOINCREMENT,
                CustomerCode VARCHAR(50) UNIQUE NOT NULL,
                CustomerName TEXT NOT NULL,
                Email TEXT NULL,
                Phone TEXT NULL,
                BillingAddress1 TEXT NULL,
                BillingCity TEXT NULL,
                BillingCountry TEXT NULL,
                CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UpdatedAt DATETIME NULL,
                IsActive BOOLEAN NOT NULL DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Vendors (
                VendorId INTEGER PRIMARY KEY AUTOINCREMENT,
                VendorCode VARCHAR(50) UNIQUE NOT NULL,
                VendorName TEXT NOT NULL,
                Email TEXT NULL,
                Phone TEXT NULL,
                AddressLine1 TEXT NULL,
                City TEXT NULL,
                Country TEXT NULL,
                CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UpdatedAt DATETIME NULL,
                IsActive BOOLEAN NOT NULL DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Sites (
                SiteId INTEGER PRIMARY KEY AUTOINCREMENT,
                SiteCode VARCHAR(50) UNIQUE NOT NULL,
                SiteName TEXT NOT NULL,
                AddressLine1 TEXT NULL,
                City TEXT NULL,
                Country TEXT NULL,
                TimeZone TEXT NULL,
                CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UpdatedAt DATETIME NULL,
                IsActive BOOLEAN NOT NULL DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Locations (
                LocationId INTEGER PRIMARY KEY AUTOINCREMENT,
                SiteId INTEGER NOT NULL,
                LocationCode VARCHAR(50) NOT NULL,
                LocationName TEXT NOT NULL,
                ParentLocationId INTEGER NULL,
                CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UpdatedAt DATETIME NULL,
                IsActive BOOLEAN NOT NULL DEFAULT 1,
                UNIQUE(SiteId, LocationCode),
                FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
                FOREIGN KEY (ParentLocationId) REFERENCES Locations(LocationId)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Items (
                ItemId INTEGER PRIMARY KEY AUTOINCREMENT,
                ItemCode TEXT UNIQUE NOT NULL,
                ItemName TEXT NOT NULL,
                Category TEXT NULL,
                UnitOfMeasure TEXT NULL,
                CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UpdatedAt DATETIME NULL,
                IsActive BOOLEAN NOT NULL DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Assets (
                AssetId INTEGER PRIMARY KEY AUTOINCREMENT,
                AssetTag VARCHAR(100) UNIQUE NOT NULL,
                AssetName TEXT NOT NULL,
                SiteId INTEGER NOT NULL,
                LocationId INTEGER NULL,
                SerialNumber TEXT NULL,
                Category TEXT NULL,
                Status VARCHAR(30) NOT NULL DEFAULT 'Active',
                Cost DECIMAL(18,2) NULL,
                PurchaseDate DATE NULL,
                VendorId INTEGER NULL,
                CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UpdatedAt DATETIME NULL,
                FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
                FOREIGN KEY (LocationId) REFERENCES Locations(LocationId),
                FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Bills (
                BillId INTEGER PRIMARY KEY AUTOINCREMENT,
                VendorId INTEGER NOT NULL,
                BillNumber VARCHAR(100) NOT NULL,
                BillDate DATE NOT NULL,
                DueDate DATE NULL,
                TotalAmount DECIMAL(18,2) NOT NULL,
                Currency VARCHAR(10) NOT NULL DEFAULT 'USD',
                Status VARCHAR(30) NOT NULL DEFAULT 'Open',
                CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UpdatedAt DATETIME NULL,
                UNIQUE(VendorId, BillNumber),
                FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS PurchaseOrders (
                POId INTEGER PRIMARY KEY AUTOINCREMENT,
                PONumber VARCHAR(100) NOT NULL UNIQUE,
                VendorId INTEGER NOT NULL,
                PODate DATE NOT NULL,
                Status VARCHAR(30) NOT NULL DEFAULT 'Open',
                SiteId INTEGER NULL,
                CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UpdatedAt DATETIME NULL,
                FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId),
                FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS PurchaseOrderLines (
                POLineId INTEGER PRIMARY KEY AUTOINCREMENT,
                POId INTEGER NOT NULL,
                LineNumber INTEGER NOT NULL,
                ItemId INTEGER NULL,
                ItemCode TEXT NOT NULL,
                Description TEXT NULL,
                Quantity DECIMAL(18,4) NOT NULL,
                UnitPrice DECIMAL(18,4) NOT NULL,
                UNIQUE(POId, LineNumber),
                FOREIGN KEY (POId) REFERENCES PurchaseOrders(POId),
                FOREIGN KEY (ItemId) REFERENCES Items(ItemId)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS SalesOrders (
                SOId INTEGER PRIMARY KEY AUTOINCREMENT,
                SONumber VARCHAR(100) NOT NULL UNIQUE,
                CustomerId INTEGER NOT NULL,
                SODate DATE NOT NULL,
                Status VARCHAR(30) NOT NULL DEFAULT 'Open',
                SiteId INTEGER NULL,
                CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UpdatedAt DATETIME NULL,
                FOREIGN KEY (CustomerId) REFERENCES Customers(CustomerId),
                FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS SalesOrderLines (
                SOLineId INTEGER PRIMARY KEY AUTOINCREMENT,
                SOId INTEGER NOT NULL,
                LineNumber INTEGER NOT NULL,
                ItemId INTEGER NULL,
                ItemCode TEXT NOT NULL,
                Description TEXT NULL,
                Quantity DECIMAL(18,4) NOT NULL,
                UnitPrice DECIMAL(18,4) NOT NULL,
                UNIQUE(SOId, LineNumber),
                FOREIGN KEY (SOId) REFERENCES SalesOrders(SOId),
                FOREIGN KEY (ItemId) REFERENCES Items(ItemId)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS AssetTransactions (
                AssetTxnId INTEGER PRIMARY KEY AUTOINCREMENT,
                AssetId INTEGER NOT NULL,
                FromLocationId INTEGER NULL,
                ToLocationId INTEGER NULL,
                TxnType VARCHAR(30) NOT NULL,
                Quantity INTEGER NOT NULL DEFAULT 1,
                TxnDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                Note TEXT NULL,
                FOREIGN KEY (AssetId) REFERENCES Assets(AssetId),
                FOREIGN KEY (FromLocationId) REFERENCES Locations(LocationId),
                FOREIGN KEY (ToLocationId) REFERENCES Locations(LocationId)
            )
            """
        ]
        
        # Create indexes
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS IX_Customers_Code ON Customers(CustomerCode)",
            "CREATE INDEX IF NOT EXISTS IX_Vendors_Code ON Vendors(VendorCode)",
            "CREATE INDEX IF NOT EXISTS IX_Sites_Code ON Sites(SiteCode)",
            "CREATE INDEX IF NOT EXISTS IX_Locations_Site_Code ON Locations(SiteId, LocationCode)",
            "CREATE INDEX IF NOT EXISTS IX_Assets_Site_Status ON Assets(SiteId, Status)",
            "CREATE INDEX IF NOT EXISTS IX_Assets_Location ON Assets(LocationId)",
            "CREATE INDEX IF NOT EXISTS IX_Bills_BillDate ON Bills(BillDate)",
            "CREATE INDEX IF NOT EXISTS IX_POs_Status_Date ON PurchaseOrders(Status, PODate)",
            "CREATE INDEX IF NOT EXISTS IX_SOs_Customer_Date ON SalesOrders(CustomerId, SODate)",
            "CREATE INDEX IF NOT EXISTS IX_POL_Item ON PurchaseOrderLines(ItemCode)",
            "CREATE INDEX IF NOT EXISTS IX_SOL_Item ON SalesOrderLines(ItemCode)"
        ]
        
        # Execute table creation
        for sql in tables_sql:
            conn.execute(sql)
        
        # Execute index creation
        for sql in indexes_sql:
            conn.execute(sql)
            
        conn.commit()
        logger.info("Database tables and indexes created successfully")
    def _insert_sample_data(self, conn: sqlite3.Connection):
        """Insert comprehensive sample data with dates from last 2 months"""
        
        # Check if data already exists
        cursor = conn.execute("SELECT COUNT(*) as count FROM Customers")
        if cursor.fetchone()['count'] > 0:
            logger.info("Sample data already exists, skipping insertion")
            return
        
        logger.info("Inserting comprehensive sample data with recent dates...")
        
        # Generate date range for last 2 months
        today = datetime.now().date()
        two_months_ago = today - timedelta(days=60)
        
        def random_date_in_range(start_date, end_date):
            time_between = end_date - start_date
            days_between = time_between.days
            random_days = random.randrange(days_between)
            return start_date + timedelta(days=random_days)
        
        # Enhanced Sample Customers (25 customers)
        customers = [
            ('CUST001', 'Tech Solutions Inc', 'contact@techsolutions.com', '+1-555-0101', '123 Tech St', 'San Francisco', 'USA'),
            ('CUST002', 'Global Manufacturing', 'orders@globalmanuf.com', '+1-555-0102', '456 Industrial Ave', 'Chicago', 'USA'),
            ('CUST003', 'Healthcare Systems', 'procurement@healthsys.com', '+1-555-0103', '789 Medical Blvd', 'Boston', 'USA'),
            ('CUST004', 'Education Corp', 'purchasing@educorp.com', '+1-555-0104', '321 Campus Dr', 'Austin', 'USA'),
            ('CUST005', 'Retail Chain Ltd', 'supply@retailchain.com', '+1-555-0105', '654 Mall Way', 'Denver', 'USA'),
            ('CUST006', 'Financial Services', 'procurement@finservices.com', '+1-555-0106', '888 Bank Plaza', 'New York', 'USA'),
            ('CUST007', 'Logistics Partners', 'orders@logpartners.com', '+1-555-0107', '999 Transport Ave', 'Memphis', 'USA'),
            ('CUST008', 'Energy Solutions', 'purchasing@energysol.com', '+1-555-0108', '777 Power St', 'Houston', 'USA'),
            ('CUST009', 'Construction Corp', 'supply@constructcorp.com', '+1-555-0109', '555 Builder Way', 'Phoenix', 'USA'),
            ('CUST010', 'Media Group', 'procurement@mediagroup.com', '+1-555-0110', '333 Studio Blvd', 'Los Angeles', 'USA'),
            ('CUST011', 'Insurance Alliance', 'orders@insalliance.com', '+1-555-0111', '222 Coverage Dr', 'Hartford', 'USA'),
            ('CUST012', 'Restaurant Chain', 'supply@restaurantchain.com', '+1-555-0112', '111 Food Court', 'Miami', 'USA'),
            ('CUST013', 'Hotel Management', 'procurement@hotelmanage.com', '+1-555-0113', '444 Hospitality Ave', 'Las Vegas', 'USA'),
            ('CUST014', 'Software Development', 'orders@softdev.com', '+1-555-0114', '666 Code St', 'Seattle', 'USA'),
            ('CUST015', 'Pharmaceutical Inc', 'supply@pharma.com', '+1-555-0115', '888 Research Blvd', 'San Diego', 'USA'),
            ('CUST016', 'Automotive Parts', 'procurement@autoparts.com', '+1-555-0116', '777 Motor Way', 'Detroit', 'USA'),
            ('CUST017', 'Aerospace Systems', 'orders@aerospace.com', '+1-555-0117', '999 Aviation Dr', 'Orlando', 'USA'),
            ('CUST018', 'Consulting Group', 'supply@consulting.com', '+1-555-0118', '555 Advisory St', 'Washington', 'USA'),
            ('CUST019', 'Fashion Retail', 'procurement@fashion.com', '+1-555-0119', '333 Style Ave', 'New York', 'USA'),
            ('CUST020', 'Sports Equipment', 'orders@sportsequip.com', '+1-555-0120', '222 Athletic Way', 'Portland', 'USA'),
            ('CUST021', 'Electronics Manufacturer', 'supply@electronics.com', '+1-555-0121', '111 Circuit Blvd', 'San Jose', 'USA'),
            ('CUST022', 'Food Distribution', 'procurement@fooddist.com', '+1-555-0122', '444 Fresh St', 'Kansas City', 'USA'),
            ('CUST023', 'Chemical Company', 'orders@chemco.com', '+1-555-0123', '666 Formula Dr', 'Houston', 'USA'),
            ('CUST024', 'Transportation Inc', 'supply@transport.com', '+1-555-0124', '888 Fleet Ave', 'Nashville', 'USA'),
            ('CUST025', 'Mining Operations', 'procurement@mining.com', '+1-555-0125', '777 Extract Way', 'Salt Lake City', 'USA')
        ]
        
        conn.executemany(
            "INSERT INTO Customers (CustomerCode, CustomerName, Email, Phone, BillingAddress1, BillingCity, BillingCountry) VALUES (?, ?, ?, ?, ?, ?, ?)",
            customers
        )
        
        # Enhanced Sample Vendors (20 vendors)
        vendors = [
            ('VEND001', 'Office Supplies Co', 'sales@officesupply.com', '+1-555-0201', '100 Supply St', 'New York', 'USA'),
            ('VEND002', 'Tech Equipment Ltd', 'orders@techequip.com', '+1-555-0202', '200 Hardware Ave', 'Seattle', 'USA'),
            ('VEND003', 'Industrial Tools Inc', 'sales@indtools.com', '+1-555-0203', '300 Tool Blvd', 'Detroit', 'USA'),
            ('VEND004', 'Medical Devices Corp', 'contact@meddevices.com', '+1-555-0204', '400 Medical Way', 'Atlanta', 'USA'),
            ('VEND005', 'Furniture Solutions', 'info@furniture.com', '+1-555-0205', '500 Furniture Dr', 'Phoenix', 'USA'),
            ('VEND006', 'Computer Systems Inc', 'sales@compsys.com', '+1-555-0206', '600 Technology Rd', 'Austin', 'USA'),
            ('VEND007', 'Safety Equipment Co', 'orders@safety.com', '+1-555-0207', '700 Safety Blvd', 'Chicago', 'USA'),
            ('VEND008', 'Network Solutions', 'info@netsol.com', '+1-555-0208', '800 Network Ave', 'Denver', 'USA'),
            ('VEND009', 'Printing Services', 'sales@printing.com', '+1-555-0209', '900 Print St', 'Portland', 'USA'),
            ('VEND010', 'Electrical Supply', 'orders@electrical.com', '+1-555-0210', '1000 Electric Way', 'Tampa', 'USA'),
            ('VEND011', 'Cleaning Supplies', 'info@cleaning.com', '+1-555-0211', '1100 Clean Ave', 'Minneapolis', 'USA'),
            ('VEND012', 'Security Systems', 'sales@security.com', '+1-555-0212', '1200 Secure Blvd', 'Dallas', 'USA'),
            ('VEND013', 'Vehicle Fleet', 'orders@vehiclefleet.com', '+1-555-0213', '1300 Fleet Dr', 'Cleveland', 'USA'),
            ('VEND014', 'Telecommunications', 'info@telecom.com', '+1-555-0214', '1400 Comm St', 'San Antonio', 'USA'),
            ('VEND015', 'Manufacturing Parts', 'sales@manuparts.com', '+1-555-0215', '1500 Parts Way', 'Milwaukee', 'USA'),
            ('VEND016', 'Laboratory Equipment', 'orders@labequip.com', '+1-555-0216', '1600 Lab Ave', 'Raleigh', 'USA'),
            ('VEND017', 'Building Materials', 'info@buildmat.com', '+1-555-0217', '1700 Build Blvd', 'Oklahoma City', 'USA'),
            ('VEND018', 'Food Service Equipment', 'sales@foodservice.com', '+1-555-0218', '1800 Kitchen Dr', 'Louisville', 'USA'),
            ('VEND019', 'Software Licensing', 'orders@softlicense.com', '+1-555-0219', '1900 Software St', 'Richmond', 'USA'),
            ('VEND020', 'Maintenance Supplies', 'info@maintenance.com', '+1-555-0220', '2000 Service Ave', 'Buffalo', 'USA')
        ]
        
        conn.executemany(
            "INSERT INTO Vendors (VendorCode, VendorName, Email, Phone, AddressLine1, City, Country) VALUES (?, ?, ?, ?, ?, ?, ?)",
            vendors
        )
        
        # Enhanced Sample Sites (12 sites)
        sites = [
            ('SITE001', 'Headquarters', '1000 Main St', 'New York', 'USA', 'EST'),
            ('SITE002', 'West Coast Office', '2000 Pacific Ave', 'Los Angeles', 'USA', 'PST'),
            ('SITE003', 'Manufacturing Plant', '3000 Factory Rd', 'Chicago', 'USA', 'CST'),
            ('SITE004', 'Distribution Center', '4000 Warehouse Blvd', 'Dallas', 'USA', 'CST'),
            ('SITE005', 'Research Facility', '5000 Innovation Way', 'Boston', 'USA', 'EST'),
            ('SITE006', 'Regional Office North', '6000 Business Park Dr', 'Seattle', 'USA', 'PST'),
            ('SITE007', 'Regional Office South', '7000 Commerce Blvd', 'Atlanta', 'USA', 'EST'),
            ('SITE008', 'Training Center', '8000 Education Ave', 'Denver', 'USA', 'MST'),
            ('SITE009', 'Service Center', '9000 Support St', 'Phoenix', 'USA', 'MST'),
            ('SITE010', 'Data Center', '10000 Server Way', 'Austin', 'USA', 'CST'),
            ('SITE011', 'Quality Control Lab', '11000 Testing Rd', 'San Diego', 'USA', 'PST'),
            ('SITE012', 'Customer Support', '12000 Help Desk Ave', 'Orlando', 'USA', 'EST')
        ]
        
        conn.executemany(
            "INSERT INTO Sites (SiteCode, SiteName, AddressLine1, City, Country, TimeZone) VALUES (?, ?, ?, ?, ?, ?)",
            sites
        )
        
        # Enhanced Sample Items (50 items)
        items = [
            ('ITM001', 'Desktop Computer - Intel i7', 'Electronics', 'Each'),
            ('ITM002', 'Office Chair - Ergonomic', 'Furniture', 'Each'),
            ('ITM003', 'Printer Paper - 500 Sheets', 'Office Supplies', 'Box'),
            ('ITM004', 'Network Switch - 24 Port', 'Electronics', 'Each'),
            ('ITM005', 'Conference Table - 12 Person', 'Furniture', 'Each'),
            ('ITM006', 'Laptop Computer - Dell', 'Electronics', 'Each'),
            ('ITM007', 'Filing Cabinet - 4 Drawer', 'Furniture', 'Each'),
            ('ITM008', 'Wireless Router - Enterprise', 'Electronics', 'Each'),
            ('ITM009', 'Monitor 27inch - 4K', 'Electronics', 'Each'),
            ('ITM010', 'Office Desk - Standing', 'Furniture', 'Each'),
            ('ITM011', 'Server Rack - 42U', 'Electronics', 'Each'),
            ('ITM012', 'Projector - HD', 'Electronics', 'Each'),
            ('ITM013', 'Whiteboard - Magnetic', 'Office Supplies', 'Each'),
            ('ITM014', 'UPS Battery Backup', 'Electronics', 'Each'),
            ('ITM015', 'Security Camera - IP', 'Electronics', 'Each'),
            ('ITM016', 'Printer - Laser Color', 'Electronics', 'Each'),
            ('ITM017', 'Scanner - Document', 'Electronics', 'Each'),
            ('ITM018', 'Phone System - VoIP', 'Electronics', 'Each'),
            ('ITM019', 'Keyboard - Mechanical', 'Electronics', 'Each'),
            ('ITM020', 'Mouse - Wireless', 'Electronics', 'Each'),
            ('ITM021', 'Headset - Noise Canceling', 'Electronics', 'Each'),
            ('ITM022', 'Webcam - HD', 'Electronics', 'Each'),
            ('ITM023', 'Tablet - 10 inch', 'Electronics', 'Each'),
            ('ITM024', 'Smartphone - Business', 'Electronics', 'Each'),
            ('ITM025', 'Hard Drive - 2TB', 'Electronics', 'Each'),
            ('ITM026', 'RAM Memory - 16GB', 'Electronics', 'Each'),
            ('ITM027', 'Graphics Card - Professional', 'Electronics', 'Each'),
            ('ITM028', 'Motherboard - Server Grade', 'Electronics', 'Each'),
            ('ITM029', 'Power Supply - 750W', 'Electronics', 'Each'),
            ('ITM030', 'CPU Cooler - Liquid', 'Electronics', 'Each'),
            ('ITM031', 'Cable Management Kit', 'Electronics', 'Each'),
            ('ITM032', 'Ethernet Cable - Cat6', 'Electronics', 'Each'),
            ('ITM033', 'Power Strip - Surge Protected', 'Electronics', 'Each'),
            ('ITM034', 'Bookshelf - 5 Tier', 'Furniture', 'Each'),
            ('ITM035', 'Lounge Chair - Modern', 'Furniture', 'Each'),
            ('ITM036', 'Coffee Table - Glass', 'Furniture', 'Each'),
            ('ITM037', 'Reception Desk', 'Furniture', 'Each'),
            ('ITM038', 'Storage Cabinet - Lockable', 'Furniture', 'Each'),
            ('ITM039', 'Meeting Room Table', 'Furniture', 'Each'),
            ('ITM040', 'Office Partition - Glass', 'Furniture', 'Each'),
            ('ITM041', 'Stationery Set - Premium', 'Office Supplies', 'Set'),
            ('ITM042', 'Notebook - A4 Lined', 'Office Supplies', 'Each'),
            ('ITM043', 'Pen Set - Executive', 'Office Supplies', 'Set'),
            ('ITM044', 'Folder - Legal Size', 'Office Supplies', 'Box'),
            ('ITM045', 'Sticky Notes - Multi Color', 'Office Supplies', 'Pack'),
            ('ITM046', 'Stapler - Heavy Duty', 'Office Supplies', 'Each'),
            ('ITM047', 'Paper Shredder - Cross Cut', 'Office Supplies', 'Each'),
            ('ITM048', 'Laminator - A3 Size', 'Office Supplies', 'Each'),
            ('ITM049', 'Calendar - Wall Planner', 'Office Supplies', 'Each'),
            ('ITM050', 'Clock - Digital Display', 'Office Supplies', 'Each')
        ]
        
        conn.executemany(
            "INSERT INTO Items (ItemCode, ItemName, Category, UnitOfMeasure) VALUES (?, ?, ?, ?)",
            items
        )
        
        # Get site IDs for foreign keys
        sites_data = conn.execute("SELECT SiteId, SiteCode FROM Sites").fetchall()
        site_ids = {row['SiteCode']: row['SiteId'] for row in sites_data}
        
        # Enhanced Sample Locations (multiple per site)
        locations = []
        location_types = ['Reception', 'Office Floor 1', 'Office Floor 2', 'Office Floor 3', 'Conference Room A', 'Conference Room B', 
                         'Storage Room', 'IT Room', 'Server Room', 'Kitchen', 'Lobby', 'Training Room', 'Manager Office', 'Warehouse A', 'Warehouse B']
        
        for site_code, site_id in site_ids.items():
            # 8-12 locations per site
            num_locations = random.randint(8, 12)
            selected_types = random.sample(location_types, min(num_locations, len(location_types)))
            
            for i, loc_type in enumerate(selected_types, 1):
                locations.append((site_id, f'LOC{i:03d}', f'{loc_type} - {site_code}'))
        
        conn.executemany(
            "INSERT INTO Locations (SiteId, LocationCode, LocationName) VALUES (?, ?, ?)",
            locations
        )
        
        # Get vendor IDs for foreign keys
        vendors_data = conn.execute("SELECT VendorId, VendorCode FROM Vendors").fetchall()
        vendor_ids = {row['VendorCode']: row['VendorId'] for row in vendors_data}
        
        # Get location IDs for foreign keys
        locations_data = conn.execute("SELECT LocationId, SiteId, LocationCode, LocationName FROM Locations").fetchall()
        
        # Enhanced Sample Assets (300+ assets)
        asset_counter = 1
        statuses = ['Active', 'InRepair', 'Disposed', 'InTransit', 'Reserved']
        status_weights = [0.6, 0.15, 0.1, 0.1, 0.05]  # Most assets are active
        categories = ['Computer Equipment', 'Office Furniture', 'Network Equipment', 'Office Supplies', 'Security Equipment', 'Audiovisual Equipment']
        
        for location in locations_data:
            # 2-8 assets per location
            num_assets = random.randint(2, 8)
            for i in range(num_assets):
                asset_tag = f'ASSET{asset_counter:05d}'
                asset_name = f'{random.choice(["Desktop", "Laptop", "Monitor", "Chair", "Desk", "Printer", "Scanner", "Router", "Switch", "Phone"])} {asset_counter}'
                status = random.choices(statuses, weights=status_weights)[0]
                category = random.choice(categories)
                cost = round(random.uniform(50, 8000), 2)
                purchase_date = random_date_in_range(two_months_ago, today)
                vendor_id = random.choice(list(vendor_ids.values()))
                
                conn.execute(
                    """INSERT INTO Assets (AssetTag, AssetName, SiteId, LocationId, SerialNumber, 
                       Category, Status, Cost, PurchaseDate, VendorId) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (asset_tag, asset_name, location['SiteId'], location['LocationId'], 
                     f'SN{asset_counter:08d}', category, status, cost, purchase_date.strftime('%Y-%m-%d'), vendor_id)
                )
                asset_counter += 1
        
        # Enhanced Purchase Orders (50 POs)
        po_statuses = ['Open', 'Approved', 'Closed', 'Cancelled']
        po_weights = [0.3, 0.4, 0.25, 0.05]
        
        for i in range(1, 51):
            po_number = f'PO{today.year}{i:04d}'
            vendor_id = random.choice(list(vendor_ids.values()))
            site_id = random.choice(list(site_ids.values()))
            po_date = random_date_in_range(two_months_ago, today)
            status = random.choices(po_statuses, weights=po_weights)[0]
            
            po_id = conn.execute(
                "INSERT INTO PurchaseOrders (PONumber, VendorId, PODate, Status, SiteId) VALUES (?, ?, ?, ?, ?)",
                (po_number, vendor_id, po_date.strftime('%Y-%m-%d'), status, site_id)
            ).lastrowid
            
            # Add 1-5 line items per PO
            item_ids = [row[0] for row in conn.execute("SELECT ItemId FROM Items ORDER BY RANDOM() LIMIT ?", (random.randint(1, 5),)).fetchall()]
            for line_num, item_id in enumerate(item_ids, 1):
                item_code = conn.execute("SELECT ItemCode FROM Items WHERE ItemId = ?", (item_id,)).fetchone()[0]
                conn.execute(
                    """INSERT INTO PurchaseOrderLines (POId, LineNumber, ItemId, ItemCode, Description, Quantity, UnitPrice) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (po_id, line_num, item_id, item_code, f'Purchase of {item_code}', 
                     random.randint(1, 10), round(random.uniform(10, 1000), 2))
                )
        
        # Enhanced Sales Orders (75 SOs) 
        customer_ids = [row[0] for row in conn.execute("SELECT CustomerId FROM Customers").fetchall()]
        so_statuses = ['Open', 'Shipped', 'Closed', 'Cancelled']
        so_weights = [0.25, 0.35, 0.35, 0.05]
        
        for i in range(1, 76):
            so_number = f'SO{today.year}{i:04d}'
            customer_id = random.choice(customer_ids)
            site_id = random.choice(list(site_ids.values()))
            so_date = random_date_in_range(two_months_ago, today)
            status = random.choices(so_statuses, weights=so_weights)[0]
            
            so_id = conn.execute(
                "INSERT INTO SalesOrders (SONumber, CustomerId, SODate, Status, SiteId) VALUES (?, ?, ?, ?, ?)",
                (so_number, customer_id, so_date.strftime('%Y-%m-%d'), status, site_id)
            ).lastrowid
            
            # Add 1-3 line items per SO
            item_ids = [row[0] for row in conn.execute("SELECT ItemId FROM Items ORDER BY RANDOM() LIMIT ?", (random.randint(1, 3),)).fetchall()]
            for line_num, item_id in enumerate(item_ids, 1):
                item_code = conn.execute("SELECT ItemCode FROM Items WHERE ItemId = ?", (item_id,)).fetchone()[0]
                conn.execute(
                    """INSERT INTO SalesOrderLines (SOId, LineNumber, ItemId, ItemCode, Description, Quantity, UnitPrice) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (so_id, line_num, item_id, item_code, f'Sale of {item_code}', 
                     random.randint(1, 5), round(random.uniform(50, 2000), 2))
                )
        
        # Enhanced Bills (40 bills)
        bill_statuses = ['Open', 'Paid', 'Void', 'Overdue']
        bill_weights = [0.3, 0.5, 0.05, 0.15]
        
        for i in range(1, 41):
            bill_number = f'BILL{today.year}{i:04d}'
            vendor_id = random.choice(list(vendor_ids.values()))
            bill_date = random_date_in_range(two_months_ago, today)
            due_date = bill_date + timedelta(days=random.randint(15, 45))
            total_amount = round(random.uniform(500, 25000), 2)
            currency = 'USD'
            status = random.choices(bill_statuses, weights=bill_weights)[0]
            
            conn.execute(
                """INSERT INTO Bills (VendorId, BillNumber, BillDate, DueDate, TotalAmount, Currency, Status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (vendor_id, bill_number, bill_date.strftime('%Y-%m-%d'), due_date.strftime('%Y-%m-%d'), 
                 total_amount, currency, status)
            )
        
        # Enhanced Asset Transactions (200+ transactions)
        asset_ids = [row[0] for row in conn.execute("SELECT AssetId FROM Assets").fetchall()]
        location_ids = [row[0] for row in conn.execute("SELECT LocationId FROM Locations").fetchall()]
        txn_types = ['Move', 'Adjust', 'Dispose', 'Create', 'Repair', 'Return']
        txn_weights = [0.4, 0.15, 0.1, 0.15, 0.15, 0.05]
        
        for i in range(200):
            asset_id = random.choice(asset_ids)
            txn_type = random.choices(txn_types, weights=txn_weights)[0]
            txn_date = random_date_in_range(two_months_ago, today)
            quantity = 1
            
            if txn_type == 'Move':
                from_location = random.choice(location_ids)
                to_location = random.choice([loc for loc in location_ids if loc != from_location])
                note = f'Asset moved from location {from_location} to {to_location}'
            else:
                from_location = random.choice(location_ids) if txn_type != 'Create' else None
                to_location = random.choice(location_ids) if txn_type != 'Dispose' else None
                note = f'{txn_type} transaction for asset maintenance'
            
            conn.execute(
                """INSERT INTO AssetTransactions (AssetId, FromLocationId, ToLocationId, TxnType, Quantity, TxnDate, Note) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (asset_id, from_location, to_location, txn_type, quantity, 
                 txn_date.strftime('%Y-%m-%d %H:%M:%S'), note)
            )
        
        conn.commit()
        logger.info("Comprehensive sample data inserted successfully with recent dates")
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute a SQL query and return results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(sql)
                
                if sql.strip().upper().startswith('SELECT'):
                    # For SELECT queries, fetch results
                    rows = cursor.fetchall()
                    columns = [description[0] for description in cursor.description] if cursor.description else []
                    
                    # Convert rows to list of dictionaries
                    results = []
                    for row in rows:
                        results.append(dict(row))
                    
                    return {
                        'success': True,
                        'results': results,
                        'columns': columns,
                        'row_count': len(results),
                        'error': None
                    }
                else:
                    # For non-SELECT queries (shouldn't happen in our case)
                    conn.commit()
                    return {
                        'success': True,
                        'results': [],
                        'columns': [],
                        'row_count': cursor.rowcount,
                        'error': None
                    }
                    
        except sqlite3.Error as e:
            logger.error(f"SQL execution error: {e}")
            return {
                'success': False,
                'results': [],
                'columns': [],
                'row_count': 0,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error executing SQL: {e}")
            return {
                'success': False,
                'results': [],
                'columns': [],
                'row_count': 0,
                'error': f"Unexpected error: {str(e)}"
            }

# Global database service instance
database_service = DatabaseService()

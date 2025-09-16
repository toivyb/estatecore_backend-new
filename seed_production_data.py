from app import create_app, db, User, Property, Tenant, Payment, MaintenanceRequest, AccessLog
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    
    # Clear existing data
    db.session.query(AccessLog).delete()
    db.session.query(Payment).delete()
    db.session.query(MaintenanceRequest).delete()
    db.session.query(Tenant).delete()
    db.session.query(Property).delete()
    db.session.query(User).delete()
    db.session.commit()
    
    print("Creating users...")
    # Create users
    super_admin = User(
        email='toivybraun@gmail.com',
        username='Toivy Braun',
        password_hash='hashed_password',
        role='super_admin'
    )
    
    demo_user = User(
        email='demo@estatecore.com',
        username='Demo User',
        password_hash='hashed_password',
        role='admin'
    )
    
    # Create tenant users
    tenants_data = [
        ('john.doe@email.com', 'John Doe'),
        ('jane.smith@email.com', 'Jane Smith'),
        ('mike.johnson@email.com', 'Mike Johnson'),
        ('sarah.wilson@email.com', 'Sarah Wilson'),
        ('david.brown@email.com', 'David Brown'),
        ('lisa.davis@email.com', 'Lisa Davis'),
        ('chris.miller@email.com', 'Chris Miller'),
        ('amanda.taylor@email.com', 'Amanda Taylor'),
    ]
    
    tenant_users = []
    for email, name in tenants_data:
        user = User(
            email=email,
            username=name,
            password_hash='hashed_password',
            role='tenant'
        )
        tenant_users.append(user)
    
    all_users = [super_admin, demo_user] + tenant_users
    db.session.add_all(all_users)
    db.session.commit()
    
    print("Creating properties...")
    # Create properties
    properties_data = [
        ('Maple Grove Apartments', '123 Maple Street, Downtown', 'apartment', 2, 1.5, 1200, 24, '92%'),
        ('Oak Ridge Complex', '456 Oak Avenue, Midtown', 'apartment', 1, 1.0, 900, 16, '87%'),
        ('Pine Valley Condos', '789 Pine Road, Uptown', 'condo', 3, 2.0, 1800, 12, '100%'),
        ('Cedar Park Homes', '321 Cedar Lane, Suburbs', 'house', 4, 3.0, 2200, 8, '75%'),
        ('Elm Street Lofts', '654 Elm Street, Arts District', 'loft', 2, 2.0, 1600, 10, '80%'),
        ('Birch Tower', '987 Birch Boulevard, Financial District', 'apartment', 1, 1.0, 1100, 30, '95%'),
        ('Willow Creek Townhomes', '147 Willow Creek Drive, Riverside', 'townhouse', 3, 2.5, 1900, 15, '93%'),
        ('Aspen Heights', '258 Aspen Way, Mountain View', 'apartment', 2, 2.0, 1400, 20, '85%'),
    ]
    
    properties = []
    for name, address, prop_type, bedrooms, bathrooms, rent, units, occupancy in properties_data:
        prop = Property(
            name=name,
            address=address,
            type=prop_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            rent=rent,
            units=units,
            occupancy=occupancy,
            description=f'Modern {prop_type} with {bedrooms} bedrooms and {bathrooms} bathrooms.',
            is_available=random.choice([True, False]),
            owner_id=super_admin.id
        )
        properties.append(prop)
    
    db.session.add_all(properties)
    db.session.commit()
    
    print("Creating tenants...")
    # Create tenant assignments
    for i, user in enumerate(tenant_users[:6]):  # Assign 6 tenants to properties
        tenant = Tenant(
            user_id=user.id,
            property_id=properties[i].id,
            lease_start=datetime.now() - timedelta(days=random.randint(30, 365)),
            lease_end=datetime.now() + timedelta(days=random.randint(90, 365)),
            rent_amount=properties[i].rent,
            deposit=properties[i].rent * 1.5,
            status='active'
        )
        db.session.add(tenant)
    
    db.session.commit()
    
    print("Creating payments...")
    # Create payments
    tenants = Tenant.query.all()
    for tenant in tenants:
        # Create multiple payments for each tenant
        for month_offset in range(6):  # 6 months of payments
            due_date = datetime.now() - timedelta(days=30*month_offset)
            payment_date = due_date + timedelta(days=random.randint(0, 10))
            
            payment = Payment(
                tenant_id=tenant.id,
                amount=tenant.rent_amount,
                payment_date=payment_date,
                due_date=due_date,
                status=random.choice(['completed', 'pending'] if month_offset < 2 else ['completed']),
                payment_method=random.choice(['credit_card', 'bank_transfer', 'check']),
                transaction_id=f'TXN{random.randint(100000, 999999)}'
            )
            db.session.add(payment)
    
    db.session.commit()
    
    print("Creating maintenance requests...")
    # Create maintenance requests
    maintenance_data = [
        ('Leaky Faucet', 'Kitchen faucet is dripping constantly', 'low'),
        ('Broken AC Unit', 'Air conditioning not working in unit 2A', 'high'),
        ('Clogged Drain', 'Bathroom sink draining slowly', 'medium'),
        ('Broken Window', 'Window lock is broken in bedroom', 'medium'),
        ('Electrical Issue', 'Light switch not working in living room', 'high'),
        ('Heating Problem', 'Heater making strange noises', 'medium'),
        ('Door Lock Issue', 'Front door lock is sticky', 'low'),
        ('Water Pressure', 'Low water pressure in shower', 'medium'),
    ]
    
    for i, (title, description, priority) in enumerate(maintenance_data):
        request = MaintenanceRequest(
            property_id=properties[i % len(properties)].id,
            tenant_id=tenants[i % len(tenants)].id if i < len(tenants) else None,
            title=title,
            description=description,
            priority=priority,
            status=random.choice(['open', 'in_progress', 'completed']),
            created_at=datetime.now() - timedelta(days=random.randint(1, 30))
        )
        db.session.add(request)
    
    db.session.commit()
    
    print("Creating access logs...")
    # Create access logs
    visitor_names = ['John Smith', 'Mary Johnson', 'Bob Wilson', 'Sarah Lee', 'Mike Brown', 'Lisa White']
    access_types = ['keycard', 'visitor_pass', 'maintenance', 'delivery', 'guest']
    
    for i in range(50):  # Create 50 access log entries
        log = AccessLog(
            property_id=properties[random.randint(0, len(properties)-1)].id,
            visitor_name=random.choice(visitor_names),
            access_time=datetime.now() - timedelta(hours=random.randint(1, 720)),  # Last 30 days
            access_type=random.choice(access_types),
            granted=random.choice([True, True, True, False])  # Mostly granted
        )
        db.session.add(log)
    
    db.session.commit()
    
    print("\n=== DATABASE SEEDED SUCCESSFULLY ===")
    print(f"Users: {User.query.count()}")
    print(f"Properties: {Property.query.count()}")
    print(f"Tenants: {Tenant.query.count()}")
    print(f"Payments: {Payment.query.count()}")
    print(f"Maintenance Requests: {MaintenanceRequest.query.count()}")
    print(f"Access Logs: {AccessLog.query.count()}")
    
    # Print summary stats
    total_revenue = sum(p.amount for p in Payment.query.filter_by(status='completed').all())
    pending_revenue = sum(p.amount for p in Payment.query.filter_by(status='pending').all())
    open_maintenance = MaintenanceRequest.query.filter_by(status='open').count()
    
    print(f"\nFinancial Summary:")
    print(f"Total Revenue: ${total_revenue:,.2f}")
    print(f"Pending Revenue: ${pending_revenue:,.2f}")
    print(f"Open Maintenance Requests: {open_maintenance}")
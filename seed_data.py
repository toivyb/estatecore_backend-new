from estatecore_backend import create_app, db
from estatecore_backend.models import User, Property, Payment
from datetime import datetime

app = create_app()

with app.app_context():
    # Just create tables if they don't exist (don't drop existing data)
    db.create_all()
    
    # Create sample users
    admin = User(username='admin', email='admin@estatecore.com', role='admin')
    admin.set_password('admin123')
    
    tenant1 = User(username='john_doe', email='john@example.com', role='tenant')
    tenant1.set_password('password123')
    
    tenant2 = User(username='jane_smith', email='jane@example.com', role='tenant')
    tenant2.set_password('password123')
    
    owner = User(username='property_owner', email='owner@example.com', role='owner')
    owner.set_password('owner123')
    
    db.session.add_all([admin, tenant1, tenant2, owner])
    db.session.commit()
    
    # Create sample properties
    prop1 = Property(
        address='123 Main St, Apt 1A',
        type='apartment',
        bedrooms=2,
        bathrooms=1.5,
        rent=1200.00,
        description='Beautiful 2-bedroom apartment with modern amenities',
        is_available=False,
        owner_id=owner.id
    )
    
    prop2 = Property(
        address='456 Oak Ave, Unit 2B',
        type='apartment',
        bedrooms=1,
        bathrooms=1.0,
        rent=800.00,
        description='Cozy 1-bedroom apartment in quiet neighborhood',
        is_available=True,
        owner_id=owner.id
    )
    
    prop3 = Property(
        address='789 Elm St, House',
        type='house',
        bedrooms=3,
        bathrooms=2.0,
        rent=1800.00,
        description='Spacious 3-bedroom house with backyard',
        is_available=False,
        owner_id=owner.id
    )
    
    prop4 = Property(
        address='321 Pine Rd, Condo',
        type='condo',
        bedrooms=2,
        bathrooms=2.0,
        rent=1400.00,
        description='Modern condo with pool and gym access',
        is_available=True,
        owner_id=owner.id
    )
    
    db.session.add_all([prop1, prop2, prop3, prop4])
    db.session.commit()
    
    # Create sample payments
    payment1 = Payment(
        amount=1200.00,
        status='completed',
        payment_date=datetime(2024, 11, 1),
        tenant_id=tenant1.id,
        property_id=prop1.id,
        stripe_payment_id='pi_completed_1'
    )
    
    payment2 = Payment(
        amount=1800.00,
        status='completed',
        payment_date=datetime(2024, 11, 1),
        tenant_id=tenant2.id,
        property_id=prop3.id,
        stripe_payment_id='pi_completed_2'
    )
    
    payment3 = Payment(
        amount=1200.00,
        status='pending',
        payment_date=datetime(2024, 12, 1),
        tenant_id=tenant1.id,
        property_id=prop1.id,
        stripe_payment_id='pi_pending_1'
    )
    
    payment4 = Payment(
        amount=1800.00,
        status='pending',
        payment_date=datetime(2024, 12, 1),
        tenant_id=tenant2.id,
        property_id=prop3.id,
        stripe_payment_id='pi_pending_2'
    )
    
    db.session.add_all([payment1, payment2, payment3, payment4])
    db.session.commit()
    
    print("Sample data created successfully!")
    print(f"Users: {User.query.count()}")
    print(f"Properties: {Property.query.count()}")
    print(f"Payments: {Payment.query.count()}")
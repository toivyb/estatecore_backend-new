#!/usr/bin/env python3
"""
Initialize RBAC System
This script sets up the Role-Based Access Control system with default roles and permissions.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from estatecore_backend import create_app, db
from models.rbac import Role, Permission, UserRole
from services.rbac_service import RBACService
from estatecore_backend.models import User
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_rbac_system():
    """Initialize the RBAC system with default roles and permissions"""
    try:
        app = create_app()
        
        with app.app_context():
            logger.info("Starting RBAC system initialization...")
            
            # Create database tables
            logger.info("Creating database tables...")
            db.create_all()
            
            # Initialize default permissions
            logger.info("Creating default permissions...")
            RBACService.create_default_permissions()
            
            # Initialize default roles
            logger.info("Creating default roles...")
            RBACService.create_default_roles()
            
            # Assign super_admin role to existing admin users
            logger.info("Assigning super_admin role to existing admin users...")
            admin_users = User.query.filter(
                User.role.in_(['admin', 'super_admin'])
            ).all()
            
            super_admin_role = Role.query.filter_by(name='super_admin').first()
            
            if super_admin_role:
                for admin_user in admin_users:
                    success = RBACService.assign_role(
                        user_id=admin_user.id,
                        role_id=super_admin_role.id
                    )
                    if success:
                        logger.info(f"Assigned super_admin role to user {admin_user.username}")
                    else:
                        logger.warning(f"Failed to assign super_admin role to user {admin_user.username}")
            
            # Assign tenant role to existing tenant users
            logger.info("Assigning tenant role to existing tenant users...")
            tenant_users = User.query.filter_by(role='tenant').all()
            tenant_role = Role.query.filter_by(name='tenant').first()
            
            if tenant_role:
                for tenant_user in tenant_users:
                    success = RBACService.assign_role(
                        user_id=tenant_user.id,
                        role_id=tenant_role.id
                    )
                    if success:
                        logger.info(f"Assigned tenant role to user {tenant_user.username}")
                    else:
                        logger.warning(f"Failed to assign tenant role to user {tenant_user.username}")
            
            # Assign property_manager role to existing manager users
            logger.info("Assigning property_manager role to existing manager users...")
            manager_users = User.query.filter(
                User.role.in_(['manager', 'property_manager'])
            ).all()
            
            property_manager_role = Role.query.filter_by(name='property_manager').first()
            
            if property_manager_role:
                for manager_user in manager_users:
                    success = RBACService.assign_role(
                        user_id=manager_user.id,
                        role_id=property_manager_role.id
                    )
                    if success:
                        logger.info(f"Assigned property_manager role to user {manager_user.username}")
                    else:
                        logger.warning(f"Failed to assign property_manager role to user {manager_user.username}")
            
            logger.info("RBAC system initialization completed successfully!")
            
            # Print summary
            role_count = Role.query.filter_by(is_active=True).count()
            permission_count = Permission.query.count()
            user_role_count = UserRole.query.filter_by(is_active=True).count()
            
            print("\n" + "="*60)
            print("RBAC SYSTEM INITIALIZATION SUMMARY")
            print("="*60)
            print(f"Roles created: {role_count}")
            print(f"Permissions created: {permission_count}")
            print(f"User role assignments: {user_role_count}")
            print("="*60)
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to initialize RBAC system: {str(e)}")
        return False

def create_custom_role():
    """Interactive function to create a custom role"""
    try:
        app = create_app()
        
        with app.app_context():
            print("\n" + "="*40)
            print("CREATE CUSTOM ROLE")
            print("="*40)
            
            role_name = input("Enter role name: ").strip()
            if not role_name:
                print("Role name is required!")
                return
            
            description = input("Enter role description: ").strip()
            
            # Check if role already exists
            existing_role = Role.query.filter_by(name=role_name).first()
            if existing_role:
                print(f"Role '{role_name}' already exists!")
                return
            
            # Create the role
            role = Role(
                name=role_name,
                description=description,
                is_system_role=False
            )
            
            db.session.add(role)
            db.session.flush()
            
            # Show available permissions
            permissions = Permission.query.all()
            print(f"\nAvailable permissions ({len(permissions)} total):")
            for i, perm in enumerate(permissions, 1):
                print(f"{i:2d}. {perm.name} - {perm.description}")
            
            # Allow user to select permissions
            print("\nEnter permission numbers to assign (comma-separated), or 'all' for all permissions:")
            perm_input = input("Permissions: ").strip()
            
            if perm_input.lower() == 'all':
                for permission in permissions:
                    role.add_permission(permission)
                print("All permissions assigned to role.")
            elif perm_input:
                try:
                    perm_numbers = [int(x.strip()) for x in perm_input.split(',')]
                    for num in perm_numbers:
                        if 1 <= num <= len(permissions):
                            permission = permissions[num - 1]
                            role.add_permission(permission)
                            print(f"Added permission: {permission.name}")
                        else:
                            print(f"Invalid permission number: {num}")
                except ValueError:
                    print("Invalid input format!")
                    return
            
            db.session.commit()
            print(f"\nRole '{role_name}' created successfully!")
            
    except Exception as e:
        logger.error(f"Failed to create custom role: {str(e)}")
        db.session.rollback()

def assign_role_to_user():
    """Interactive function to assign a role to a user"""
    try:
        app = create_app()
        
        with app.app_context():
            print("\n" + "="*40)
            print("ASSIGN ROLE TO USER")
            print("="*40)
            
            # Show all users
            users = User.query.filter_by(is_active=True).all()
            print("Available users:")
            for i, user in enumerate(users, 1):
                current_roles = [ur.role.name for ur in user.user_roles if ur.is_active]
                print(f"{i:2d}. {user.username} ({user.email}) - Current roles: {', '.join(current_roles) or 'None'}")
            
            user_num = int(input("\nSelect user number: ").strip())
            if not 1 <= user_num <= len(users):
                print("Invalid user number!")
                return
            
            selected_user = users[user_num - 1]
            
            # Show all roles
            roles = Role.query.filter_by(is_active=True).all()
            print("\nAvailable roles:")
            for i, role in enumerate(roles, 1):
                print(f"{i:2d}. {role.name} - {role.description}")
            
            role_num = int(input("\nSelect role number: ").strip())
            if not 1 <= role_num <= len(roles):
                print("Invalid role number!")
                return
            
            selected_role = roles[role_num - 1]
            
            # Assign the role
            success = RBACService.assign_role(
                user_id=selected_user.id,
                role_id=selected_role.id
            )
            
            if success:
                print(f"\nRole '{selected_role.name}' assigned to user '{selected_user.username}' successfully!")
            else:
                print(f"\nFailed to assign role to user!")
                
    except Exception as e:
        logger.error(f"Failed to assign role to user: {str(e)}")
    except ValueError:
        print("Invalid input! Please enter a number.")

def main():
    """Main function to run RBAC initialization or management tasks"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'init':
            init_rbac_system()
        elif command == 'create-role':
            create_custom_role()
        elif command == 'assign-role':
            assign_role_to_user()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: init, create-role, assign-role")
    else:
        print("RBAC System Management")
        print("=====================")
        print("1. Initialize RBAC system")
        print("2. Create custom role")
        print("3. Assign role to user")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            init_rbac_system()
        elif choice == '2':
            create_custom_role()
        elif choice == '3':
            assign_role_to_user()
        else:
            print("Invalid choice!")

if __name__ == '__main__':
    main()
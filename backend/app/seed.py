import os

from sqlalchemy import or_

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import (
    User,
    UserRole,
    Address,
    ProviderProfile,
    VerificationStatus,
    ServiceCategory,
    Service,
    ProviderService
)

CATEGORIES_DATA = [
    {
        "name": "Plumbing",
        "slug": "plumbing",
        "description": "Pipe repair, drain unblocking, tap fitting, leak detection",
        "services": [
            {"name": "Tap / Shower Repair", "slug": "tap-shower-repair", "base_charge": 199.0, "min_charge": 149.0, "duration": 45, "emergency_surcharge": 150.0},
            {"name": "Drain Unblocking & Clog Removal", "slug": "drain-unblocking", "base_charge": 299.0, "min_charge": 249.0, "duration": 60, "emergency_surcharge": 200.0},
            {"name": "Water Tank / Pipe Leak Fixing", "slug": "pipe-leak-repair", "base_charge": 399.0, "min_charge": 299.0, "duration": 90, "emergency_surcharge": 250.0},
        ]
    },
    {
        "name": "Electrical",
        "slug": "electrical",
        "description": "Wiring, switchboard repair, MCB tripping, fan/light installation",
        "services": [
            {"name": "Switchboard / Socket Repair", "slug": "switchboard-repair", "base_charge": 149.0, "min_charge": 99.0, "duration": 30, "emergency_surcharge": 150.0},
            {"name": "Ceiling Fan Installation & Repair", "slug": "ceiling-fan-repair", "base_charge": 199.0, "min_charge": 149.0, "duration": 45, "emergency_surcharge": 150.0},
            {"name": "Complete Electrical Tripping / Fuse Inspection", "slug": "fuse-mcb-inspection", "base_charge": 349.0, "min_charge": 299.0, "duration": 60, "emergency_surcharge": 250.0},
        ]
    },
    {
        "name": "AC & Appliance Repair",
        "slug": "appliance-repair",
        "description": "AC servicing, refrigerator repair, washing machine diagnostics",
        "services": [
            {"name": "Split AC Service & Filter Cleaning", "slug": "ac-servicing", "base_charge": 499.0, "min_charge": 399.0, "duration": 60, "emergency_surcharge": 200.0},
            {"name": "Refrigerator Cooling Diagnostics", "slug": "refrigerator-repair", "base_charge": 349.0, "min_charge": 249.0, "duration": 60, "emergency_surcharge": 150.0},
            {"name": "Washing Machine Motor & Drain Repair", "slug": "washing-machine-repair", "base_charge": 399.0, "min_charge": 299.0, "duration": 60, "emergency_surcharge": 150.0},
        ]
    },
    {
        "name": "Mechanic & Vehicle Assist",
        "slug": "mechanic",
        "description": "On-demand roadside bike/car jumpstart, tire puncture, basic breakdown",
        "services": [
            {"name": "Car Battery Jumpstart", "slug": "car-jumpstart", "base_charge": 299.0, "min_charge": 249.0, "duration": 30, "emergency_surcharge": 200.0},
            {"name": "Tubeless Tyre Puncture Assistance", "slug": "tyre-puncture-repair", "base_charge": 249.0, "min_charge": 199.0, "duration": 45, "emergency_surcharge": 150.0},
        ]
    },
    {
        "name": "Locksmith",
        "slug": "locksmith",
        "description": "Door lockout, lock cylinder replacement, key duplication",
        "services": [
            {"name": "Emergency Door Lockout Unlock", "slug": "emergency-door-unlock", "base_charge": 399.0, "min_charge": 349.0, "duration": 30, "emergency_surcharge": 300.0},
            {"name": "Main Door Lock Installation", "slug": "door-lock-installation", "base_charge": 499.0, "min_charge": 399.0, "duration": 60, "emergency_surcharge": 200.0},
        ]
    },
    {
        "name": "Carpentry",
        "slug": "carpentry",
        "description": "Furniture assembly, hinge alignment, custom wooden repair",
        "services": [
            {"name": "Door Hinge / Latch Alignment", "slug": "door-hinge-repair", "base_charge": 249.0, "min_charge": 199.0, "duration": 45, "emergency_surcharge": 100.0},
            {"name": "Modular Furniture Assembly", "slug": "furniture-assembly", "base_charge": 499.0, "min_charge": 399.0, "duration": 90, "emergency_surcharge": 150.0},
        ]
    },
    {
        "name": "Cleaning",
        "slug": "cleaning",
        "description": "Bathroom deep cleaning, kitchen sanitation, sofa shampooing",
        "services": [
            {"name": "Intensive Bathroom Deep Clean", "slug": "bathroom-deep-clean", "base_charge": 399.0, "min_charge": 349.0, "duration": 60, "emergency_surcharge": 100.0},
            {"name": "Full Kitchen Degreasing & Sanitation", "slug": "kitchen-deep-clean", "base_charge": 699.0, "min_charge": 599.0, "duration": 120, "emergency_surcharge": 150.0},
        ]
    },
]


def seed_database():
    db = SessionLocal()
    try:
        print("🌱 Seeding V1 Service Categories and Services...")
        category_map = {}
        for cat_data in CATEGORIES_DATA:
            category = db.query(ServiceCategory).filter(ServiceCategory.slug == cat_data["slug"]).first()
            if not category:
                category = ServiceCategory(
                    name=cat_data["name"],
                    slug=cat_data["slug"],
                    description=cat_data["description"],
                    is_active=True
                )
                db.add(category)
                db.flush()
            category_map[cat_data["slug"]] = category

            for s_data in cat_data["services"]:
                service = db.query(Service).filter(Service.slug == s_data["slug"]).first()
                if not service:
                    service = Service(
                        category_id=category.id,
                        name=s_data["name"],
                        slug=s_data["slug"],
                        base_visit_charge=s_data["base_charge"],
                        min_charge=s_data["min_charge"],
                        estimated_duration_mins=s_data["duration"],
                        emergency_surcharge_rate=s_data["emergency_surcharge"],
                        is_active=True
                    )
                    db.add(service)

        admin_password = os.getenv("HAAZIR_BOOTSTRAP_ADMIN_PASSWORD")
        admin_phone = os.getenv("HAAZIR_BOOTSTRAP_ADMIN_PHONE")
        admin_email = os.getenv("HAAZIR_BOOTSTRAP_ADMIN_EMAIL")
        if admin_password and admin_phone:
            if len(admin_password) < 12:
                raise ValueError("Bootstrap admin password must be at least 12 characters")
            print("🌱 Provisioning configured bootstrap admin account...")
            identity_filters = [User.phone == admin_phone]
            if admin_email:
                identity_filters.append(User.email == admin_email)
            matching_admins = db.query(User).filter(or_(*identity_filters)).all()
            if len(matching_admins) > 1:
                raise ValueError(
                    "Bootstrap admin email and phone belong to different accounts; "
                    "resolve the conflict before provisioning"
                )
            admin = matching_admins[0] if matching_admins else None
        else:
            admin = None
            print("ℹ️  Admin bootstrap skipped; provision securely out of band.")
        if admin_password and admin_phone:
            if not admin:
                admin = User(full_name="Haazir Platform Admin")
                db.add(admin)
            admin.phone = admin_phone
            admin.email = admin_email
            admin.hashed_password = get_password_hash(admin_password)
            admin.role = UserRole.ADMIN
            admin.is_active = True
            admin.is_suspended = False

        db.commit()
        print("✅ Database successfully seeded!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

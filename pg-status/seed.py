"""
Seed data — Auto-run on first startup if DB is empty.
Creates demo owners, students, properties, floors, rooms, beds, amenities, and active holds.
"""
import logging
from datetime import datetime, timedelta
import bcrypt
from extensions import db
from models.user import User
from models.property import Property
from models.floor import Floor
from models.room import Room
from models.bed import Bed
from models.hold import Hold
from models.amenity import Amenity

logger = logging.getLogger(__name__)

BED_LABELS = ['Bed A', 'Bed B', 'Bed C']


def hash_pw(password):
    return bcrypt.hashpw(password.encode('utf-8'),
                         bcrypt.gensalt()).decode('utf-8')


def seed_database():
    """Seed the database with demo data."""
    if User.query.first() is not None:
        logger.info('Database already seeded, skipping.')
        return

    logger.info('Seeding database...')
    now = datetime.utcnow()

    # --- OWNERS ---
    rajesh = User(
        full_name='Rajesh Sharma', email='rajesh@staysync.com',
        phone='+919876543210', password_hash=hash_pw('owner123'),
        role='owner', bio='Experienced PG owner in Pune with 8+ years.',
        city='Pune', college_or_work='StaySync Properties',
        reliability_score=100, is_profile_complete=True, created_at=now
    )
    meena = User(
        full_name='Meena Patil', email='meena@staysync.com',
        phone='+919876543211', password_hash=hash_pw('owner456'),
        role='owner', bio='Managing hostels across Pune since 2018.',
        city='Pune', college_or_work='Patil Accommodations',
        reliability_score=100, is_profile_complete=True, created_at=now
    )
    db.session.add_all([rajesh, meena])
    db.session.flush()

    # --- STUDENTS ---
    arjun = User(
        full_name='Arjun Singh', email='arjun@student.com',
        phone='+919123456780', password_hash=hash_pw('student123'),
        role='student', bio='CS student at COEP.',
        city='Pune', college_or_work='COEP Technological University',
        reliability_score=87, is_profile_complete=True, created_at=now
    )
    priya = User(
        full_name='Priya Desai', email='priya@student.com',
        phone='+919123456781', password_hash=hash_pw('student456'),
        role='student', bio='MBA student at Symbiosis.',
        city='Pune', college_or_work='Symbiosis International',
        reliability_score=92, is_profile_complete=True, created_at=now
    )
    rohan = User(
        full_name='Rohan Mehta', email='rohan@student.com',
        phone='+919123456782', password_hash=hash_pw('student789'),
        role='student', bio='Engineering student.',
        city='Pune', college_or_work='MIT Pune',
        reliability_score=65, is_profile_complete=True, created_at=now
    )
    sneha = User(
        full_name='Sneha Joshi', email='sneha@student.com',
        phone='+919123456783', password_hash=hash_pw('student000'),
        role='student', bio='Design student at NID.',
        city='Pune', college_or_work='NID Pune',
        reliability_score=100, is_profile_complete=True, created_at=now
    )
    db.session.add_all([arjun, priya, rohan, sneha])
    db.session.flush()

    # --- PROPERTY 1: Sunrise Boys PG ---
    sunrise = Property(
        owner_id=rajesh.id, name='Sunrise Boys PG', property_type='PG',
        description='Premium boys PG in the heart of Kothrud with modern amenities and home-cooked meals.',
        address_line='42, Lane 7, Kothrud', locality='Kothrud',
        city='Pune', pincode='411038', gender_allowed='Male',
        is_active=True, created_at=now
    )
    db.session.add(sunrise)
    db.session.flush()

    # Amenities
    for name in ['WiFi', 'Hot Water', 'CCTV',
                 'Laundry', 'RO Water', 'Housekeeping']:
        db.session.add(Amenity(property_id=sunrise.id, name=name))

    # Floors and rooms
    sunrise_beds = []
    statuses_p1 = [
        ['green', 'yellow', 'red', 'green', 'red', 'green'],
        ['green', 'red', 'green', 'red', 'yellow', 'red']
    ]
    for fi in range(2):
        floor = Floor(property_id=sunrise.id, floor_number=fi,
                      floor_label=f'{"Ground" if fi == 0 else "First"} Floor')
        db.session.add(floor)
        db.session.flush()
        for ri in range(3):
            room = Room(floor_id=floor.id, room_number=f'{fi}0{ri + 1}',
                        sharing_type=2, rent_per_bed=7500,
                        has_ac=ri == 0, has_attached_bath=ri < 2)
            db.session.add(room)
            db.session.flush()
            for bi in range(2):
                idx = ri * 2 + bi
                status = statuses_p1[fi][idx]
                bed = Bed(room_id=room.id, bed_label=BED_LABELS[bi],
                          status=status, last_status_change=now)
                if status == 'red':
                    bed.occupied_since = now - timedelta(days=30)
                db.session.add(bed)
                db.session.flush()
                sunrise_beds.append(bed)

    # --- PROPERTY 2: Green Valley Hostel ---
    green_valley = Property(
        owner_id=rajesh.id, name='Green Valley Hostel', property_type='Hostel',
        description='Spacious hostel near Aundh with gym, AC rooms, and delicious meals included.',
        address_line='15, ITI Road, Aundh', locality='Aundh',
        city='Pune', pincode='411007', gender_allowed='Any',
        is_active=True, created_at=now
    )
    db.session.add(green_valley)
    db.session.flush()

    for name in ['WiFi', 'AC', 'Meals', 'Gym',
                 'Security', 'Generator', 'Study Room']:
        db.session.add(Amenity(property_id=green_valley.id, name=name))

    gv_beds = []
    for fi in range(3):
        labels = ['Ground', 'First', 'Second']
        floor = Floor(property_id=green_valley.id, floor_number=fi,
                      floor_label=f'{labels[fi]} Floor')
        db.session.add(floor)
        db.session.flush()
        for ri in range(4):
            room = Room(floor_id=floor.id, room_number=f'{fi}0{ri + 1}',
                        sharing_type=3, rent_per_bed=5000,
                        has_ac=True, has_attached_bath=ri < 2)
            db.session.add(room)
            db.session.flush()
            for bi in range(3):
                # Mix of statuses
                status_options = ['green', 'green', 'yellow', 'red', 'green',
                                  'red', 'green', 'red', 'yellow', 'green', 'green', 'red']
                sidx = (fi * 12 + ri * 3 + bi) % len(status_options)
                status = status_options[sidx]
                bed = Bed(room_id=room.id, bed_label=BED_LABELS[bi],
                          status=status, last_status_change=now)
                if status == 'red':
                    bed.occupied_since = now - timedelta(days=15)
                db.session.add(bed)
                db.session.flush()
                gv_beds.append(bed)

    # --- PROPERTY 3: Harmony 2BHK Flat ---
    harmony = Property(
        owner_id=rajesh.id, name='Harmony 2BHK Flat', property_type='Flat',
        description='Modern fully furnished 2BHK flat in Baner, perfect for female students.',
        address_line='201, Harmony Residency, Baner Road', locality='Baner',
        city='Pune', pincode='411045', gender_allowed='Female',
        is_active=True, created_at=now
    )
    db.session.add(harmony)
    db.session.flush()

    for name in ['WiFi', 'AC', 'Parking', 'Hot Water', 'Security']:
        db.session.add(Amenity(property_id=harmony.id, name=name))

    h_floor = Floor(
        property_id=harmony.id,
        floor_number=0,
        floor_label='Main Floor')
    db.session.add(h_floor)
    db.session.flush()

    h_statuses = [['yellow', 'red'], ['red', 'red']]
    for ri in range(2):
        room = Room(floor_id=h_floor.id, room_number=f'10{ri + 1}',
                    sharing_type=2, rent_per_bed=12000,
                    has_ac=True, has_attached_bath=True)
        db.session.add(room)
        db.session.flush()
        for bi in range(2):
            status = h_statuses[ri][bi]
            bed = Bed(room_id=room.id, bed_label=BED_LABELS[bi],
                      status=status, last_status_change=now)
            if status == 'red':
                bed.occupied_since = now - timedelta(days=45)
            db.session.add(bed)
            db.session.flush()

    # --- ACTIVE HOLDS ---
    # Arjun -> Bed A, Room 001, Sunrise PG (first green->yellow bed at index 1)
    # Find a yellow bed in sunrise
    yellow_sunrise = [b for b in sunrise_beds if b.status == 'yellow']
    if yellow_sunrise:
        hold1 = Hold(
            bed_id=yellow_sunrise[0].id, student_id=arjun.id, owner_id=rajesh.id,
            hold_days=3, requested_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=2),
            responded_at=now - timedelta(days=1), status='active'
        )
        db.session.add(hold1)

    # Priya -> a yellow bed in Green Valley
    yellow_gv = [b for b in gv_beds if b.status == 'yellow']
    if yellow_gv:
        hold2 = Hold(
            bed_id=yellow_gv[0].id, student_id=priya.id, owner_id=rajesh.id,
            hold_days=5, requested_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=4),
            responded_at=now - timedelta(days=1), status='active'
        )
        db.session.add(hold2)

    db.session.commit()
    logger.info('Database seeded successfully!')

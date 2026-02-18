from flask import current_app
from models import db, User
from auth import hash_password


def create_default_admin():
    admin = User.query.filter_by(email='admin@example.com').first()

    if not admin:
        admin = User(
            name='admin',
            email='admin@example.com',
            password_hash=hash_password('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

        print('\n' + '='*50)
        print('DEFAULT ADMIN USER CREATED:')
        print('Email:    admin@example.com')
        print('Password: admin123')
        print('='*50 + '\n')
    else:
        print('\n' + '='*50)
        print('ADMIN LOGIN:')
        print('Email:    admin@example.com')
        print('Password: admin123')
        print('='*50 + '\n')

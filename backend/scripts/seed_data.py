"""
Seed Data Script - Exam Prep BD
Creates initial admin user, base categories, and default folders
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from passlib.hash import bcrypt
from database.connection import AsyncSessionLocal
from models import User, UserRole, SubscriptionTier, Folder, Category


async def seed():
    print("Seeding data...")
    
    async with AsyncSessionLocal() as db:
        # Check if admin exists
        result = await db.execute(select(User).where(User.email == "admin@examprepbd.com"))
        admin = result.scalar_one_or_none()
        
        if not admin:
            admin = User(
                email="admin@examprepbd.com",
                password_hash=bcrypt.hash("admin123"),
                full_name="Admin",
                role=UserRole.ADMIN,
                subscription_tier=SubscriptionTier.PREMIUM,
                is_active=True,
                is_verified=True,
            )
            db.add(admin)
            print("Created admin user: admin@examprepbd.com / admin123")
        else:
            print("Admin user already exists")
        
        # Create default categories
        categories = [
            ("জাতীয়", "national"),
            ("আন্তর্জাতিক", "international"),
            ("রাজনীতি", "politics"),
            ("অর্থনীতি", "economy"),
            ("খেলাধুলা", "sports"),
            ("শিক্ষা", "education"),
            ("চাকরি", "job_news"),
            ("বিজ্ঞান ও প্রযুক্তি", "science-tech"),
            ("বিনোদন", "entertainment"),
            ("সাক্ষাৎকার", "interview"),
        ]
        
        for name, slug in categories:
            existing = await db.execute(
                select(Category).where(Category.slug == slug)
            )
            if not existing.scalar_one_or_none():
                db.add(Category(name=name, slug=slug))
                print(f"Created category: {name}")
            else:
                print(f"Category exists: {name}")
        
        # Create default folders
        default_folders = [
            ("BCS Preparation", None, "folder", 0),
            ("NTRCA Preparation", None, "folder", 1),
            ("Bank Jobs", None, "folder", 2),
            ("General Knowledge", None, "folder", 3),
        ]
        
        for name, parent, icon, order in default_folders:
            existing = await db.execute(select(Folder).where(Folder.name == name))
            if not existing.scalar_one_or_none():
                db.add(Folder(name=name, parent_id=parent, icon=icon, order=order))
                print(f"Created folder: {name}")
        
        await db.commit()
    
    print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())

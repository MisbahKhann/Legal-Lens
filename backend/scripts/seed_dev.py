"""
Database seed script for local development.
Populates sample matters and user memberships.
"""

from typing import Any, Dict, List
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine, Base  # noqa: E402
from app.core.models import Matter, MatterMember  # noqa: E402


def seed() -> None:
    """Seed sample matters and memberships."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        sample_matters: List[Dict[str, Any]] = [
            {
                "id": "matter-acme-2026",
                "name": "Acme Corp v. Global Logistics",
                "case_number": "CV-2026-0842",
                "client_name": "Acme Corp",
                "status": "active",
                "members": [
                    {"user_id": "user-dev-1", "role": "owner"},
                    {"user_id": "user-dev-2", "role": "attorney"},
                    {"user_id": "user-attorney", "role": "owner"},
                ],
            },
            {
                "id": "matter-henderson-2026",
                "name": "State of California v. Henderson",
                "case_number": "CR-2026-0199",
                "client_name": "David Henderson",
                "status": "active",
                "members": [
                    {"user_id": "user-dev-1", "role": "attorney"},
                    {"user_id": "user-dev-3", "role": "owner"},
                    {"user_id": "user-attorney", "role": "attorney"},
                ],
            },
            {
                "id": "matter-apex-isolated",
                "name": "In re Apex Biotech Patent Dispute",
                "case_number": "IP-2026-4401",
                "client_name": "Apex Biotech",
                "status": "active",
                "members": [
                    {"user_id": "user-dev-2", "role": "owner"},
                ],
            },
        ]

        for m_data in sample_matters:
            existing = db.get(Matter, m_data["id"])
            if not existing:
                matter = Matter(
                    id=m_data["id"],
                    name=m_data["name"],
                    case_number=m_data["case_number"],
                    client_name=m_data["client_name"],
                    status=m_data["status"],
                )
                db.add(matter)
                for mem in m_data["members"]:
                    member = MatterMember(
                        matter_id=m_data["id"],
                        user_id=mem["user_id"],
                        role=mem["role"],
                    )
                    db.add(member)
                print(f"Seeded matter: {m_data['name']} ({m_data['id']})")
            else:
                print(f"Matter already exists: {m_data['id']}")

        db.commit()
        print("Development seed completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

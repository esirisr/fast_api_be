import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from server.config import db as database
from server.models.Payment import Payment
from server.models.User import User


async def migrate():
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        raise RuntimeError("MONGODB_URI is required to read the existing database.")

    client = AsyncIOMotorClient(mongo_uri)
    try:
        mongo_db = client.get_default_database()
        await database.init_db()
        if database.SessionLocal is None:
            raise RuntimeError("PostgreSQL session was not initialized.")

        user_docs = await mongo_db["users"].find({}).to_list(length=None)
        payment_docs = await mongo_db["payments"].find({}).to_list(length=None)
        imported_users = 0
        imported_payments = 0
        skipped_users = 0
        skipped_payments = 0

        async with database.SessionLocal() as session:
            async with session.begin():
                for document in user_docs:
                    phone = document.get("phone")
                    if not phone or await session.get(User, phone):
                        skipped_users += 1
                        continue
                    session.add(User(
                        phone=phone,
                        password=document["password"],
                        deviceId=document.get("deviceId"),
                        storeNumber=document.get("storeNumber"),
                        createdAt=document.get("createdAt") or datetime.utcnow(),
                    ))
                    imported_users += 1

                for document in payment_docs:
                    phone = document.get("phone")
                    if not phone or await session.get(Payment, phone):
                        skipped_payments += 1
                        continue
                    session.add(Payment(
                        phone=phone,
                        isPaid=document.get("isPaid", False),
                        isSuspended=document.get("isSuspended", False),
                        expiryDate=document.get("expiryDate"),
                        lastUpdated=document.get("lastUpdated") or datetime.utcnow(),
                    ))
                    imported_payments += 1

        print(
            "Migration complete: "
            f"users imported={imported_users}, skipped={skipped_users}; "
            f"payments imported={imported_payments}, skipped={skipped_payments}."
        )
    finally:
        client.close()
        await database.close_db()


if __name__ == "__main__":
    asyncio.run(migrate())
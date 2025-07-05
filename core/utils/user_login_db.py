from datetime import datetime
from typing import Optional, Dict

class UserLoginDB:
    def __init__(self, collection):
        self.collection = collection

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def create_user(self,
                    telegram_id: str,
                    telegram_username: Optional[str] = None,
                    telegram_first_name: Optional[str] = None,
                    telegram_last_name: Optional[str] = None,
                    telegram_chat_id: Optional[str] = None,
                    instagram_username: Optional[str] = None,
                    instagram_password: Optional[str] = None,
                    instagram_session: Optional[Dict] = None,
                    subscription_type: str = "free") -> None:
        now = self._now()
        user_data = {
            "telegram_id": telegram_id,
            "telegram_username": telegram_username,
            "telegram_first_name": telegram_first_name,
            "telegram_last_name": telegram_last_name,
            "telegram_chat_id": telegram_chat_id,

            "instagram_username": instagram_username,
            "instagram_password": instagram_password,
            "instagram_session": instagram_session or {},

            "subscription_type": subscription_type,
            "subscription_start_date": now,
            "subscription_exp_date": None,

            "first_login_date": now,
            "last_login_date": now,
            "last_session_date": now
        }
        self.collection.insert_one(user_data)

    def get_user(self, telegram_id: str) -> Optional[Dict]:
        telegram_id = int(telegram_id)
        user = self.collection.find_one({"telegram_id": telegram_id})
        return user

    def update_instagram_session(self, telegram_id: str, session_data: Dict) -> None:
        self.collection.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"instagram_session": session_data, "last_session_date": self._now()}}
        )

    def update_login_dates(self, telegram_id: str) -> None:
        now = self._now()
        self.collection.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"last_login_date": now}}
        )

    def update_subscription(self, telegram_id: str, sub_type: str, exp_date: str) -> None:
        self.collection.update_one(
            {"telegram_id": telegram_id},
            {
                "$set": {
                    "subscription_type": sub_type,
                    "subscription_start_date": self._now(),
                    "subscription_exp_date": exp_date
                }
            }
        )

    def delete_user(self, telegram_id: str) -> None:
        self.collection.delete_one({"telegram_id": telegram_id})

    def update_or_create_user(self, telegram_id: str, user_data: Dict) -> bool:
        """
        Updates an existing user if found, otherwise creates a new one.
        Returns True if created, False if updated.
        """
        now = self._now()
        update_fields = {
            **user_data,
            "last_login_date": now,
            "last_session_date": now
        }

        result = self.collection.update_one(
            {"telegram_id": telegram_id},
            {
                "$set": update_fields,
                "$setOnInsert": {
                    "first_login_date": now,
                    "subscription_type": "free",
                    "subscription_start_date": now,
                    "subscription_exp_date": None,
                }
            },
            upsert=True
        )
        return result.upserted_id is not None
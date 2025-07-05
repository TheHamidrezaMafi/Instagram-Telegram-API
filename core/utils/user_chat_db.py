from datetime import datetime
from typing import List, Dict

class UserChatDB:
    def __init__(self, collection):
        self.collection = collection

    def _now(self):
        return datetime.utcnow().isoformat() + "Z"

    def _clean_message(self, msg: Dict) -> Dict:
        # Convert media_url to string if necessary
        if 'media_url' in msg and not isinstance(msg['media_url'], str):
            msg['media_url'] = str(msg['media_url'])

        # Handle unsupported message types
        unsupported_types = {'xma_reel_share', 'expired_placeholder', 'generic_xma'}
        if msg.get('type') in unsupported_types:
            msg['text'] = f"[Unsupported type: {msg['type']}]"
            msg['media_url'] = ''
            msg['media_type'] = ''
        
        return msg

    def save_or_update_chat(self, telegram_id: str, thread_id: str, new_messages: List[Dict]):
        """
        Merge and save messages, avoiding duplicates.
        """
        try:
            # Step 1: Fetch existing chat
            existing = self.collection.find_one({"telegram_id": telegram_id, "thread_id": thread_id})
            existing_msg_ids = set()

            if existing and "messages" in existing:
                existing_msg_ids = {msg.get("id") for msg in existing["messages"] if "id" in msg}

            # Step 2: Clean and filter new unique messages
            unique_messages = []
            for msg in new_messages:
                msg_id = msg.get("id")
                if msg_id and msg_id not in existing_msg_ids:
                    cleaned_msg = self._clean_message(msg)
                    unique_messages.append(cleaned_msg)

            if not unique_messages:
                # print(f"No new messages to save for thread {thread_id}")
                return

            # Step 3: Update MongoDB
            result = self.collection.update_one(
                {"telegram_id": telegram_id, "thread_id": thread_id},
                {
                    "$push": {"messages": {"$each": unique_messages}},
                    "$set": {"last_saved": self._now()}
                },
                upsert=True
            )

            # print(f"[save_or_update_chat] Matched: {result.matched_count}, Modified: {result.modified_count}, Upserted: {result.upserted_id}")

        except Exception as e:
            print(f"[save_or_update_chat] Error saving messages: {e}")
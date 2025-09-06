from supabase import create_client, Client
from pathlib import Path
import mimetypes
from contextlib import suppress
from _configs.log_config import logger
from _configs.config import get_config
import time

cfg = get_config()
STORAGE_URL = cfg.supabase_config.storage_url
STORAGE_SERVICE_ROLE_KEY = cfg.supabase_config.storage_service_role_key

class SupabaseStorageClient:
    def __init__(self, client: Client):
        self.client = client

    @classmethod
    def create(cls) -> "SupabaseStorageClient":
        client = create_client(STORAGE_URL, STORAGE_SERVICE_ROLE_KEY)
        return cls(client)


    async def upload_avatar(self, user_id: int, file_path: Path) -> str:
        file_bytes = file_path.read_bytes()
        content_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"

        storage_path = f"avatars/{user_id}.jpg"
        bucket_name = "shinigami-users-avatars"

        with suppress(Exception):
            self.client.storage.from_(bucket_name).remove([storage_path])

        # Загружаем новую аватарку
        res = self.client.storage.from_(bucket_name).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type}
        )

        logger.debug(f"Upload response: {res}")
        logger.debug(f"Upload response (dir): {dir(res)}")

        public_url = self.client.storage.from_(bucket_name).get_public_url(storage_path)
        anti_cache_url = f"{public_url}?v={int(time.time())}"

        return anti_cache_url

from typing import Optional
from services.supabase.supabase_client import SupabaseStorageClient

supabase_client: Optional[SupabaseStorageClient] = SupabaseStorageClient.create()
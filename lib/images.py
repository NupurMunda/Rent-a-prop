# lib/images.py
import io, uuid
from PIL import Image
from lib.sb import sb_client

def upload_images_to_storage(files, owner_id):
    """Uploads up to 5 images to Supabase Storage bucket 'listing-images' and returns public URLs."""
    sb = sb_client()
    urls = []
    for f in (files or [])[:5]:
        image = Image.open(f).convert("RGB")
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        path = f"{owner_id}/{uuid.uuid4().hex}.jpg"
        sb.storage.from_("listing-images").upload(
            path, buf.getvalue(), {"content-type": "image/jpeg"}
        )
        urls.append(sb.storage.from_("listing-images").get_public_url(path))
    return urls

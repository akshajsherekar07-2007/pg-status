"""
Upload Service — File validation, EXIF stripping, structured storage.
"""
import os
import logging
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from extensions import db
from models.media import PropertyMedia

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
LIMITS = {'property': 10, 'floor': 5, 'room': 5, 'bed': 3}


def allowed_file(filename):
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


def strip_exif(image_path):
    """Strip EXIF data from image using Pillow."""
    try:
        img = Image.open(image_path)
        data = list(img.getdata())
        clean = Image.new(img.mode, img.size)
        clean.putdata(data)
        clean.save(image_path, quality=85, optimize=True)
    except Exception as e:
        logger.error(f'EXIF strip failed: {e}')


def save_upload(file, property_id, entity_type, entity_id, upload_folder):
    """Save uploaded file to structured path and create media record."""
    if not file or not file.filename:
        return {'success': False, 'error': 'No file provided.', 'code': 400}

    if not allowed_file(file.filename):
        return {'success': False,
                'error': 'File type not allowed. Use JPG, PNG, or WebP.', 'code': 400}

    # Check limits
    existing_count = PropertyMedia.query.filter_by(
        property_id=property_id, media_type=entity_type
    ).count()
    max_allowed = LIMITS.get(entity_type, 5)
    if existing_count >= max_allowed:
        return {'success': False,
                'error': f'Maximum {max_allowed} photos for {entity_type}.', 'code': 400}

    # Sanitize filename
    original = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique = uuid.uuid4().hex[:8]
    filename = f'{timestamp}_{unique}_{original}'

    # Create directory
    dir_path = os.path.join(
        upload_folder,
        str(property_id),
        f'{entity_type}_{entity_id}')
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, filename)

    # Save file
    file.save(file_path)

    # Check file size after save
    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        os.remove(file_path)
        return {'success': False, 'error': 'File exceeds 5MB limit.', 'code': 400}

    # Strip EXIF
    strip_exif(file_path)

    # Relative path for DB
    rel_path = os.path.join(
        'uploads',
        str(property_id),
        f'{entity_type}_{entity_id}',
        filename)
    rel_path = rel_path.replace('\\', '/')

    # Determine if primary
    is_primary = existing_count == 0

    # Create media record
    media_kwargs = {
        'property_id': property_id,
        'media_type': entity_type,
        'file_path': rel_path,
        'is_primary': is_primary
    }
    if entity_type == 'floor':
        media_kwargs['floor_id'] = entity_id
    elif entity_type == 'room':
        media_kwargs['room_id'] = entity_id
    elif entity_type == 'bed':
        media_kwargs['bed_id'] = entity_id

    media = PropertyMedia(**media_kwargs)
    db.session.add(media)
    db.session.commit()

    logger.info(f'Upload saved: {rel_path}')
    return {'success': True, 'data': {
        'file_path': rel_path, 'media_id': media.id}}


def delete_media(media_id, upload_folder):
    """Delete a media record and its file."""
    media = PropertyMedia.query.get(media_id)
    if not media:
        return {'success': False, 'error': 'Media not found.', 'code': 404}

    # Delete file
    full_path = os.path.join(
        upload_folder,
        media.file_path.replace(
            'uploads/',
            ''))
    if os.path.exists(full_path):
        os.remove(full_path)

    db.session.delete(media)
    db.session.commit()
    logger.info(f'Media deleted: {media_id}')
    return {'success': True, 'data': {'media_id': media_id}}

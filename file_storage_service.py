"""
File Storage Service for EstateCore
Handles file uploads, storage, and management with security and optimization
"""

import os
import hashlib
import mimetypes
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import uuid
from pathlib import Path
import shutil
from PIL import Image
import zipfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available, falling back to mimetypes")

@dataclass
class FileStorageConfig:
    """File storage configuration"""
    storage_path: str
    max_file_size: int = 10 * 1024 * 1024  # 10MB default
    allowed_extensions: List[str] = None
    create_thumbnails: bool = True
    thumbnail_sizes: List[Tuple[int, int]] = None
    virus_scan_enabled: bool = False
    compress_images: bool = True
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = [
                # Documents
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf',
                # Images
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg',
                # Archives
                '.zip', '.rar', '.7z', '.tar', '.gz',
                # Other
                '.csv', '.json', '.xml'
            ]
        
        if self.thumbnail_sizes is None:
            self.thumbnail_sizes = [(150, 150), (300, 300), (800, 600)]

class FileStorageService:
    def __init__(self, config: FileStorageConfig = None):
        """Initialize file storage service"""
        self.config = config or self._get_default_config()
        self._ensure_storage_directories()
        
    def _get_default_config(self) -> FileStorageConfig:
        """Get default configuration"""
        storage_path = os.getenv('FILE_STORAGE_PATH', 'uploads')
        return FileStorageConfig(
            storage_path=storage_path,
            max_file_size=int(os.getenv('MAX_FILE_SIZE', 10 * 1024 * 1024)),
            create_thumbnails=os.getenv('CREATE_THUMBNAILS', 'true').lower() == 'true',
            compress_images=os.getenv('COMPRESS_IMAGES', 'true').lower() == 'true'
        )
    
    def _ensure_storage_directories(self):
        """Create storage directories if they don't exist"""
        directories = [
            self.config.storage_path,
            os.path.join(self.config.storage_path, 'documents'),
            os.path.join(self.config.storage_path, 'images'),
            os.path.join(self.config.storage_path, 'thumbnails'),
            os.path.join(self.config.storage_path, 'temp'),
            os.path.join(self.config.storage_path, 'archives')
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _generate_secure_filename(self, original_filename: str, file_hash: str = None) -> str:
        """Generate secure filename with UUID and hash"""
        file_ext = Path(original_filename).suffix.lower()
        
        if file_hash:
            # Use first 8 characters of hash for uniqueness
            unique_id = file_hash[:8]
        else:
            unique_id = str(uuid.uuid4())[:8]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = "".join(c for c in Path(original_filename).stem if c.isalnum() or c in ('-', '_'))[:20]
        
        return f"{timestamp}_{unique_id}_{safe_name}{file_ext}"
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _get_file_type_category(self, filename: str, mime_type: str = None) -> str:
        """Determine file category based on extension and MIME type"""
        ext = Path(filename).suffix.lower()
        
        if mime_type:
            if mime_type.startswith('image/'):
                return 'images'
            elif mime_type.startswith('video/'):
                return 'media'
            elif mime_type.startswith('audio/'):
                return 'media'
        
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
        document_exts = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.csv'}
        archive_exts = {'.zip', '.rar', '.7z', '.tar', '.gz'}
        
        if ext in image_exts:
            return 'images'
        elif ext in document_exts:
            return 'documents'
        elif ext in archive_exts:
            return 'archives'
        else:
            return 'documents'  # Default category
    
    def _validate_file(self, file_path: str, original_filename: str) -> Tuple[bool, str]:
        """Validate uploaded file"""
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.config.max_file_size:
                return False, f"File size ({file_size} bytes) exceeds maximum allowed ({self.config.max_file_size} bytes)"
            
            # Check file extension
            file_ext = Path(original_filename).suffix.lower()
            if file_ext not in self.config.allowed_extensions:
                return False, f"File type '{file_ext}' is not allowed"
            
            # Check MIME type using python-magic
            try:
                mime_type = magic.from_file(file_path, mime=True)
                
                # Additional MIME type validation for security
                dangerous_types = [
                    'application/x-executable',
                    'application/x-msdos-program',
                    'application/x-msdownload',
                    'application/x-dosexec'
                ]
                
                if mime_type in dangerous_types:
                    return False, f"MIME type '{mime_type}' is not allowed for security reasons"
                    
            except Exception as e:
                logger.warning(f"Could not determine MIME type: {e}")
            
            # Virus scan if enabled
            if self.config.virus_scan_enabled:
                if not self._scan_for_viruses(file_path):
                    return False, "File failed virus scan"
            
            return True, "File is valid"
            
        except Exception as e:
            return False, f"File validation error: {str(e)}"
    
    def _scan_for_viruses(self, file_path: str) -> bool:
        """Placeholder for virus scanning integration"""
        # In production, integrate with ClamAV or similar
        # For now, just check file size as a basic measure
        try:
            file_size = os.path.getsize(file_path)
            # Reject files that are suspiciously large for their type
            if file_size > 100 * 1024 * 1024:  # 100MB
                return False
            return True
        except Exception:
            return False
    
    def _create_thumbnails(self, image_path: str, filename: str) -> List[Dict]:
        """Create thumbnails for image files"""
        thumbnails = []
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                for width, height in self.config.thumbnail_sizes:
                    # Create thumbnail
                    img_copy = img.copy()
                    img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)
                    
                    # Generate thumbnail filename
                    name_without_ext = Path(filename).stem
                    ext = Path(filename).suffix
                    thumb_filename = f"{name_without_ext}_thumb_{width}x{height}{ext}"
                    thumb_path = os.path.join(self.config.storage_path, 'thumbnails', thumb_filename)
                    
                    # Save thumbnail
                    img_copy.save(thumb_path, optimize=True, quality=85)
                    
                    thumbnails.append({
                        'size': f"{width}x{height}",
                        'filename': thumb_filename,
                        'path': thumb_path,
                        'url': f"/uploads/thumbnails/{thumb_filename}"
                    })
                    
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
        
        return thumbnails
    
    def _compress_image(self, image_path: str, quality: int = 85) -> bool:
        """Compress image file to reduce size"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Save with compression
                img.save(image_path, optimize=True, quality=quality)
                return True
                
        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            return False
    
    def upload_file(self, file_path: str, original_filename: str, metadata: Dict = None) -> Dict:
        """Upload and process file"""
        try:
            # Validate file
            is_valid, validation_message = self._validate_file(file_path, original_filename)
            if not is_valid:
                return {
                    'success': False,
                    'error': validation_message
                }
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Generate secure filename
            secure_filename = self._generate_secure_filename(original_filename, file_hash)
            
            # Determine storage category
            mime_type = magic.from_file(file_path, mime=True) if os.path.exists(file_path) else None
            category = self._get_file_type_category(original_filename, mime_type)
            
            # Create destination path
            dest_dir = os.path.join(self.config.storage_path, category)
            dest_path = os.path.join(dest_dir, secure_filename)
            
            # Copy file to destination
            shutil.copy2(file_path, dest_path)
            
            # Get file info
            file_size = os.path.getsize(dest_path)
            
            # Process image files
            thumbnails = []
            if category == 'images' and self.config.create_thumbnails:
                if self.config.compress_images:
                    self._compress_image(dest_path)
                thumbnails = self._create_thumbnails(dest_path, secure_filename)
            
            # Prepare file metadata
            file_metadata = {
                'original_filename': original_filename,
                'secure_filename': secure_filename,
                'file_path': dest_path,
                'relative_path': os.path.join(category, secure_filename),
                'file_size': file_size,
                'file_hash': file_hash,
                'mime_type': mime_type,
                'category': category,
                'thumbnails': thumbnails,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            return {
                'success': True,
                'file': file_metadata
            }
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return {
                'success': False,
                'error': f"Upload failed: {str(e)}"
            }
    
    def upload_multiple_files(self, file_paths: List[str], original_filenames: List[str], metadata: List[Dict] = None) -> Dict:
        """Upload multiple files"""
        results = []
        successful_uploads = 0
        
        metadata = metadata or [{}] * len(file_paths)
        
        for i, (file_path, original_filename) in enumerate(zip(file_paths, original_filenames)):
            file_metadata = metadata[i] if i < len(metadata) else {}
            result = self.upload_file(file_path, original_filename, file_metadata)
            
            if result['success']:
                successful_uploads += 1
            
            results.append({
                'original_filename': original_filename,
                'result': result
            })
        
        return {
            'total_files': len(file_paths),
            'successful_uploads': successful_uploads,
            'failed_uploads': len(file_paths) - successful_uploads,
            'results': results
        }
    
    def delete_file(self, file_path: str, delete_thumbnails: bool = True) -> bool:
        """Delete file and associated thumbnails"""
        try:
            # Delete main file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete thumbnails if requested
            if delete_thumbnails:
                filename = Path(file_path).name
                name_without_ext = Path(filename).stem
                ext = Path(filename).suffix
                
                thumb_dir = os.path.join(self.config.storage_path, 'thumbnails')
                for size in self.config.thumbnail_sizes:
                    thumb_filename = f"{name_without_ext}_thumb_{size[0]}x{size[1]}{ext}"
                    thumb_path = os.path.join(thumb_dir, thumb_filename)
                    if os.path.exists(thumb_path):
                        os.remove(thumb_path)
            
            return True
            
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False
    
    def get_file_url(self, relative_path: str) -> str:
        """Generate public URL for file"""
        base_url = os.getenv('FILE_BASE_URL', '/uploads')
        return f"{base_url}/{relative_path}"
    
    def create_download_archive(self, file_paths: List[str], archive_name: str = None) -> Dict:
        """Create ZIP archive of multiple files"""
        try:
            if not archive_name:
                archive_name = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            archive_path = os.path.join(self.config.storage_path, 'archives', archive_name)
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in file_paths:
                    if os.path.exists(file_path):
                        # Add file to archive with just the filename (not full path)
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname)
            
            archive_size = os.path.getsize(archive_path)
            
            return {
                'success': True,
                'archive_path': archive_path,
                'archive_name': archive_name,
                'archive_size': archive_size,
                'download_url': self.get_file_url(f"archives/{archive_name}"),
                'files_count': len(file_paths)
            }
            
        except Exception as e:
            logger.error(f"Archive creation failed: {e}")
            return {
                'success': False,
                'error': f"Archive creation failed: {str(e)}"
            }
    
    def get_storage_stats(self) -> Dict:
        """Get storage usage statistics"""
        try:
            stats = {
                'total_files': 0,
                'total_size': 0,
                'categories': {}
            }
            
            for category in ['documents', 'images', 'archives']:
                category_path = os.path.join(self.config.storage_path, category)
                if os.path.exists(category_path):
                    category_files = 0
                    category_size = 0
                    
                    for file_path in Path(category_path).rglob('*'):
                        if file_path.is_file():
                            category_files += 1
                            category_size += file_path.stat().st_size
                    
                    stats['categories'][category] = {
                        'files': category_files,
                        'size': category_size,
                        'size_mb': round(category_size / (1024 * 1024), 2)
                    }
                    
                    stats['total_files'] += category_files
                    stats['total_size'] += category_size
            
            stats['total_size_mb'] = round(stats['total_size'] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Storage stats calculation failed: {e}")
            return {}
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """Clean up temporary files older than specified hours"""
        try:
            temp_dir = os.path.join(self.config.storage_path, 'temp')
            if not os.path.exists(temp_dir):
                return 0
            
            cleanup_count = 0
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            for file_path in Path(temp_dir).rglob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleanup_count += 1
                    except Exception as e:
                        logger.warning(f"Could not delete temp file {file_path}: {e}")
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")
            return 0

# Utility functions
def create_file_storage_service() -> FileStorageService:
    """Create file storage service with default configuration"""
    return FileStorageService()

def allowed_file(filename: str, allowed_extensions: List[str] = None) -> bool:
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        service = create_file_storage_service()
        allowed_extensions = service.config.allowed_extensions
    
    return Path(filename).suffix.lower() in allowed_extensions

def get_file_icon(filename: str) -> str:
    """Get appropriate icon for file type"""
    ext = Path(filename).suffix.lower()
    
    icon_map = {
        '.pdf': '📄',
        '.doc': '📝', '.docx': '📝',
        '.xls': '📊', '.xlsx': '📊',
        '.ppt': '📈', '.pptx': '📈',
        '.txt': '📋', '.rtf': '📋',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
        '.bmp': '🖼️', '.tiff': '🖼️', '.webp': '🖼️', '.svg': '🖼️',
        '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
        '.csv': '📊',
        '.json': '🔧', '.xml': '🔧'
    }
    
    return icon_map.get(ext, '📄')

if __name__ == "__main__":
    # Test file storage service
    service = create_file_storage_service()
    
    # Display storage stats
    stats = service.get_storage_stats()
    print(f"📊 Storage Statistics:")
    print(f"Total files: {stats.get('total_files', 0)}")
    print(f"Total size: {stats.get('total_size_mb', 0)} MB")
    
    # Cleanup temp files
    cleaned = service.cleanup_temp_files()
    print(f"🧹 Cleaned up {cleaned} temporary files")
    
    print("✅ File storage service is ready!")
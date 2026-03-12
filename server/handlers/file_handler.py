"""
File handling for the GraphQL server.

This module manages file uploads and downloads for TTS and Translation services.
It handles file validation, temporary storage, and file retrieval for downloads.
"""

import os
import uuid
import base64
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging


class FileHandler:
    """
    Manages file uploads and downloads for the GraphQL server.
    
    Responsibilities:
    - Validate uploaded files (type and size)
    - Save files to temporary directory
    - Generate unique file IDs for download tracking
    - Retrieve files for download
    - Clean up temporary files
    """
    
    def __init__(self, config, logger: logging.Logger):
        """
        Initialize FileHandler with configuration and logger.
        
        Args:
            config: ServerConfig instance with file handling settings
            logger: Logger instance for file operations
        """
        self.config = config
        self.logger = logger
        self.temp_dir = Path(config.temp_directory)
        
        # Create temp directory if it doesn't exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"FileHandler initialized with temp directory: {self.temp_dir}")
    
    async def handle_upload(self, upload) -> str:
        """
        Process file upload and save to temp directory.
        
        Validates:
        - File type (text/plain only)
        - File size (max from config)
        
        Args:
            upload: File upload object (Strawberry Upload type)
            
        Returns:
            file_path: Path to saved temporary file
            
        Raises:
            ValueError: If file validation fails
        """
        # Read file content
        content = await upload.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        # Validate file size
        if file_size_mb > self.config.max_upload_size_mb:
            error_msg = (
                f"File size ({file_size_mb:.2f}MB) exceeds maximum allowed size "
                f"({self.config.max_upload_size_mb}MB)"
            )
            self.logger.warning(f"File upload rejected: {error_msg}")
            raise ValueError(error_msg)
        
        # Validate file type (text files only)
        # Check content type if available
        if hasattr(upload, 'content_type') and upload.content_type:
            if not upload.content_type.startswith('text/'):
                error_msg = (
                    f"Invalid file type: {upload.content_type}. "
                    f"Only text files are allowed."
                )
                self.logger.warning(f"File upload rejected: {error_msg}")
                raise ValueError(error_msg)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.txt"
        file_path = self.temp_dir / filename
        
        # Save file to temp directory
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
            
            self.logger.info(
                f"File uploaded successfully: {filename} ({file_size_mb:.2f}MB)",
                extra={
                    'file_id': file_id,
                    'file_size_mb': file_size_mb,
                    'file_path': str(file_path)
                }
            )
            
            return str(file_path)
            
        except Exception as e:
            error_msg = f"Failed to save uploaded file: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
    
    async def get_file_for_download(self, file_id: str) -> dict:
        """
        Retrieve file for download.
        
        Args:
            file_id: Unique file identifier for download tracking
            
        Returns:
            Dictionary with file information:
            - content: File content as bytes
            - filename: Original filename
            - content_type: MIME type
            - size: File size in bytes
            
        Raises:
            FileNotFoundError: If file does not exist
        """
        try:
            # Decode file_id to get file path
            file_path = self._decode_file_id(file_id)
            
            # Check if file exists
            if not os.path.exists(file_path):
                error_msg = f"File not found: {file_id}"
                self.logger.warning(error_msg)
                raise FileNotFoundError(error_msg)
            
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determine content type based on file extension
            file_ext = Path(file_path).suffix.lower()
            content_type = self._get_content_type(file_ext)
            
            # Get filename
            filename = Path(file_path).name
            
            self.logger.info(
                f"File retrieved for download: {filename}",
                extra={
                    'file_id': file_id,
                    'file_path': file_path,
                    'file_size': len(content)
                }
            )
            
            return {
                'content': content,
                'filename': filename,
                'content_type': content_type,
                'size': len(content)
            }
            
        except FileNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to retrieve file for download: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """
        Remove temporary file.
        
        Args:
            file_path: Path to temporary file to remove
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(
                    f"Temporary file cleaned up: {file_path}",
                    extra={'file_path': file_path}
                )
            else:
                self.logger.debug(
                    f"Temporary file not found for cleanup: {file_path}",
                    extra={'file_path': file_path}
                )
        except Exception as e:
            # Log error but don't raise - cleanup failures shouldn't break the flow
            self.logger.warning(
                f"Failed to cleanup temporary file: {file_path} - {str(e)}",
                extra={'file_path': file_path, 'error': str(e)}
            )
    
    def generate_file_id(self, file_path: str) -> str:
        """
        Generate unique file ID for download tracking.
        
        Creates a base64-encoded identifier that includes the file path
        and timestamp for uniqueness and security.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Unique file identifier for download
        """
        # Create identifier with file path and timestamp
        timestamp = datetime.now().isoformat()
        identifier = f"{file_path}|{timestamp}"
        
        # Encode to base64 for URL-safe identifier
        file_id = base64.urlsafe_b64encode(identifier.encode()).decode()
        
        self.logger.debug(
            f"Generated file ID for: {file_path}",
            extra={'file_path': file_path, 'file_id': file_id}
        )
        
        return file_id
    
    def _decode_file_id(self, file_id: str) -> str:
        """
        Decode file ID to get original file path.
        
        Args:
            file_id: Base64-encoded file identifier
            
        Returns:
            Original file path
            
        Raises:
            ValueError: If file_id is invalid
        """
        try:
            # Decode from base64
            decoded = base64.urlsafe_b64decode(file_id.encode()).decode()
            
            # Extract file path (before the pipe separator)
            file_path = decoded.split('|')[0]
            
            return file_path
            
        except Exception as e:
            error_msg = f"Invalid file ID: {file_id}"
            self.logger.warning(error_msg)
            raise ValueError(error_msg)
    
    def _get_content_type(self, file_ext: str) -> str:
        """
        Get MIME content type based on file extension.
        
        Args:
            file_ext: File extension (e.g., '.mp3', '.txt')
            
        Returns:
            MIME content type
        """
        content_types = {
            '.mp3': 'audio/mpeg',
            '.txt': 'text/plain',
            '.wav': 'audio/wav',
            '.json': 'application/json'
        }
        
        return content_types.get(file_ext, 'application/octet-stream')

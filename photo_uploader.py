#!/usr/bin/env python3
"""
Photo Upload Manager for Pi Zero Camera with Network Share
Uploads photos to local network share organized by date
Author: JMTDI
Date: 2025-10-25
"""

import os
import json
import time
import threading
import shutil
from datetime import datetime
from pathlib import Path

class PhotoUploader:
    def __init__(self, wifi_manager):
        self.wifi_manager = wifi_manager
        
        # Configuration
        self.device_id = "picamera-001"
        self.retry_attempts = 3
        self.retry_delay = 5
        
        # Network share configuration
        self.share_base_dir = "/home/pi/camera_share"  # Local share directory
        self.photos_by_date = True  # Organize photos by date
        
        # Queue management
        self.upload_queue = []
        self.queue_file = os.path.expanduser("~/camera/data/upload_queue.json")
        self.processing = False
        
        # Background worker
        self.running = True
        self.upload_thread = threading.Thread(target=self._upload_worker, daemon=True)
        self.upload_thread.start()
        
        # Create share directory structure
        self.setup_share_directory()
        
        # Load existing queue
        self.load_queue()
        
        print("📤 Photo uploader initialized (Network Share)")
    
    def setup_share_directory(self):
        """Set up network share directory structure"""
        try:
            os.makedirs(self.share_base_dir, exist_ok=True)
            os.makedirs(f"{self.share_base_dir}/by_date", exist_ok=True)
            os.makedirs(f"{self.share_base_dir}/all_photos", exist_ok=True)
            
            # Set permissions for network access
            os.chmod(self.share_base_dir, 0o755)
            os.chmod(f"{self.share_base_dir}/by_date", 0o755)
            os.chmod(f"{self.share_base_dir}/all_photos", 0o755)
            
            # Create info file
            info_content = f"""PiCamera Photos - {self.device_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Folder Structure:
/by_date/ - Photos organized by date (YYYY-MM-DD folders)
/all_photos/ - All photos in one folder

This folder is shared on the network and accessible from Windows.
"""
            with open(f"{self.share_base_dir}/README.txt", 'w') as f:
                f.write(info_content)
            
            print(f"📁 Share directory created: {self.share_base_dir}")
            
        except Exception as e:
            print(f"❌ Error setting up share directory: {e}")
    
    def queue_photo(self, filepath):
        """Add photo to upload queue"""
        if not os.path.exists(filepath):
            print(f"❌ Photo not found: {filepath}")
            return False
        
        # Create upload entry
        photo_info = {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'timestamp': datetime.now().isoformat(),
            'filesize': os.path.getsize(filepath),
            'uploaded': False,
            'upload_attempts': 0,
            'last_attempt': None,
            'error': None
        }
        
        self.upload_queue.append(photo_info)
        self.save_queue()
        
        print(f"📤 Photo queued for upload: {photo_info['filename']}")
        return True
    
    def _upload_worker(self):
        """Background worker thread for uploading photos to network share"""
        while self.running:
            try:
                # Process pending uploads (no need to check WiFi for local share)
                pending_uploads = [p for p in self.upload_queue if not p['uploaded']]
                
                if pending_uploads and not self.processing:
                    self.processing = True
                    
                    for photo in pending_uploads:
                        if not self.running:
                            break
                        
                        success = self._upload_single_photo(photo)
                        
                        if success:
                            photo['uploaded'] = True
                            photo['upload_time'] = datetime.now().isoformat()
                            print(f"✅ Uploaded to share: {photo['filename']}")
                        else:
                            # Wait before next attempt
                            time.sleep(self.retry_delay)
                        
                        self.save_queue()
                    
                    self.processing = False
                
                time.sleep(5)  # Check every 5 seconds for local share
                
            except Exception as e:
                print(f"❌ Upload worker error: {e}")
                self.processing = False
                time.sleep(30)  # Wait longer on error
    
    def _upload_single_photo(self, photo_info):
        """Upload a single photo to network share"""
        filepath = photo_info['filepath']
        
        if not os.path.exists(filepath):
            photo_info['error'] = "File not found"
            return False
        
        # Check retry limit
        if photo_info['upload_attempts'] >= self.retry_attempts:
            photo_info['error'] = "Max retries exceeded"
            print(f"❌ Max retries exceeded for {photo_info['filename']}")
            return False
        
        try:
            photo_info['upload_attempts'] += 1
            photo_info['last_attempt'] = datetime.now().isoformat()
            
            print(f"📤 Copying to share: {photo_info['filename']} (attempt {photo_info['upload_attempts']})...")
            
            # Get photo timestamp for date-based organization
            photo_timestamp = datetime.fromisoformat(photo_info['timestamp'])
            date_str = photo_timestamp.strftime('%Y-%m-%d')
            
            # Create date folder if it doesn't exist
            date_folder = f"{self.share_base_dir}/by_date/{date_str}"
            os.makedirs(date_folder, exist_ok=True)
            os.chmod(date_folder, 0o755)
            
            # Copy to date-organized folder
            date_dest = f"{date_folder}/{photo_info['filename']}"
            shutil.copy2(filepath, date_dest)
            os.chmod(date_dest, 0o644)
            
            # Also copy to all_photos folder
            all_dest = f"{self.share_base_dir}/all_photos/{photo_info['filename']}"
            shutil.copy2(filepath, all_dest)
            os.chmod(all_dest, 0o644)
            
            # Update photo info
            photo_info['share_date_path'] = date_dest
            photo_info['share_all_path'] = all_dest
            photo_info['error'] = None
            
            # Update daily count
            self._update_daily_count(date_str)
            
            return True
            
        except Exception as e:
            photo_info['error'] = str(e)
            print(f"❌ Upload error for {photo_info['filename']}: {e}")
            return False
    
    def _update_daily_count(self, date_str):
        """Update daily photo count in date folder"""
        try:
            date_folder = f"{self.share_base_dir}/by_date/{date_str}"
            
            # Count photos in this date folder
            photo_count = len([f for f in os.listdir(date_folder) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            
            # Create/update count file
            count_file = f"{date_folder}/photos_info.txt"
            count_content = f"""Photos taken on {date_str}
Total photos: {photo_count}
Device: {self.device_id}
Last updated: {datetime.now().strftime('%H:%M:%S')}
"""
            with open(count_file, 'w') as f:
                f.write(count_content)
            os.chmod(count_file, 0o644)
            
        except Exception as e:
            print(f"⚠️ Error updating daily count: {e}")
    
    def load_queue(self):
        """Load upload queue from file"""
        try:
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r') as f:
                    self.upload_queue = json.load(f)
                print(f"📤 Loaded {len(self.upload_queue)} items from upload queue")
            else:
                self.upload_queue = []
        except Exception as e:
            print(f"❌ Error loading upload queue: {e}")
            self.upload_queue = []
    
    def save_queue(self):
        """Save upload queue to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
            
            with open(self.queue_file, 'w') as f:
                json.dump(self.upload_queue, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving upload queue: {e}")
    
    def get_upload_status(self):
        """Get upload queue status"""
        total = len(self.upload_queue)
        uploaded = len([p for p in self.upload_queue if p['uploaded']])
        pending = total - uploaded
        failed = len([p for p in self.upload_queue if not p['uploaded'] and p['upload_attempts'] >= self.retry_attempts])
        
        return {
            'total': total,
            'uploaded': uploaded,
            'pending': pending,
            'failed': failed,
            'processing': self.processing
        }
    
    def get_todays_photos(self):
        """Get count of today's photos"""
        today = datetime.now().strftime('%Y-%m-%d')
        date_folder = f"{self.share_base_dir}/by_date/{today}"
        
        try:
            if os.path.exists(date_folder):
                photos = [f for f in os.listdir(date_folder) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                return len(photos)
        except Exception as e:
            print(f"Error counting today's photos: {e}")
        
        return 0
    
    def get_total_photos_in_share(self):
        """Get total number of photos in share"""
        try:
            all_folder = f"{self.share_base_dir}/all_photos"
            if os.path.exists(all_folder):
                photos = [f for f in os.listdir(all_folder) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                return len(photos)
        except Exception as e:
            print(f"Error counting total photos: {e}")
        
        return 0
    
    def cleanup(self):
        """Clean up uploader"""
        print("🧹 Cleaning up photo uploader...")
        self.running = False
        
        if self.upload_thread.is_alive():
            self.upload_thread.join(timeout=5)
        
        self.save_queue()
        print("✅ Photo uploader cleanup complete")
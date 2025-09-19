"""
Standalone LPR Client System
Provides API-based license plate recognition for external clients
"""

import os
import requests
import json
import time
from datetime import datetime
import argparse

class LPRClient:
    """Client for interacting with EstateCore LPR API"""
    
    def __init__(self, api_base_url, api_key=None):
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def recognize_image(self, image_path):
        """
        Recognize license plate from image file
        
        Args:
            image_path (str): Path to image file
            
        Returns:
            dict: Recognition result with plate, confidence, blacklist status
        """
        try:
            with open(image_path, 'rb') as img_file:
                files = {'image': (os.path.basename(image_path), img_file, 'image/jpeg')}
                
                response = self.session.post(
                    f'{self.api_base_url}/api/lpr/recognize',
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        'success': False,
                        'error': f'API returned {response.status_code}: {response.text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Recognition failed: {str(e)}'
            }
    
    def recognize_image_batch(self, image_paths):
        """
        Recognize license plates from multiple images
        
        Args:
            image_paths (list): List of image file paths
            
        Returns:
            list: List of recognition results
        """
        results = []
        for i, image_path in enumerate(image_paths):
            print(f"Processing image {i+1}/{len(image_paths)}: {image_path}")
            result = self.recognize_image(image_path)
            result['image_path'] = image_path
            results.append(result)
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.1)
            
        return results
    
    def check_blacklist(self, plate):
        """
        Check if a plate is blacklisted
        
        Args:
            plate (str): License plate number
            
        Returns:
            dict: Blacklist status and reason
        """
        try:
            response = self.session.get(
                f'{self.api_base_url}/api/lpr/blacklist/check',
                params={'plate': plate},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'error': f'API returned {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            return {
                'error': f'Blacklist check failed: {str(e)}'
            }
    
    def get_blacklist(self):
        """
        Get the complete blacklist
        
        Returns:
            list: List of blacklisted plates
        """
        try:
            response = self.session.get(
                f'{self.api_base_url}/api/lpr/blacklist',
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            print(f"Error getting blacklist: {str(e)}")
            return []
    
    def add_to_blacklist(self, plate, reason=""):
        """
        Add a plate to the blacklist
        
        Args:
            plate (str): License plate number
            reason (str): Reason for blacklisting
            
        Returns:
            dict: Operation result
        """
        try:
            response = self.session.post(
                f'{self.api_base_url}/api/lpr/blacklist',
                json={'plate': plate, 'reason': reason},
                timeout=10
            )
            
            return response.json()
                
        except Exception as e:
            return {
                'error': f'Failed to add to blacklist: {str(e)}'
            }
    
    def remove_from_blacklist(self, plate):
        """
        Remove a plate from the blacklist
        
        Args:
            plate (str): License plate number
            
        Returns:
            dict: Operation result
        """
        try:
            response = self.session.delete(
                f'{self.api_base_url}/api/lpr/blacklist',
                params={'plate': plate},
                timeout=10
            )
            
            return response.json()
                
        except Exception as e:
            return {
                'error': f'Failed to remove from blacklist: {str(e)}'
            }
    
    def get_events(self, limit=50):
        """
        Get recent LPR events
        
        Args:
            limit (int): Maximum number of events to retrieve
            
        Returns:
            list: List of LPR events
        """
        try:
            response = self.session.get(
                f'{self.api_base_url}/api/lpr/events',
                params={'limit': limit},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            print(f"Error getting events: {str(e)}")
            return []


def main():
    """Command line interface for LPR client"""
    parser = argparse.ArgumentParser(description='EstateCore LPR Client')
    parser.add_argument('--url', default='http://localhost:5000', help='API base URL')
    parser.add_argument('--api-key', help='API key for authentication')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Recognize command
    recognize_parser = subparsers.add_parser('recognize', help='Recognize license plate from image')
    recognize_parser.add_argument('image', help='Path to image file')
    
    # Batch recognize command
    batch_parser = subparsers.add_parser('batch', help='Recognize license plates from multiple images')
    batch_parser.add_argument('images', nargs='+', help='Paths to image files')
    
    # Blacklist commands
    blacklist_parser = subparsers.add_parser('blacklist', help='Blacklist management')
    blacklist_subparsers = blacklist_parser.add_subparsers(dest='blacklist_action')
    
    check_parser = blacklist_subparsers.add_parser('check', help='Check if plate is blacklisted')
    check_parser.add_argument('plate', help='License plate number')
    
    add_parser = blacklist_subparsers.add_parser('add', help='Add plate to blacklist')
    add_parser.add_argument('plate', help='License plate number')
    add_parser.add_argument('--reason', default='', help='Reason for blacklisting')
    
    remove_parser = blacklist_subparsers.add_parser('remove', help='Remove plate from blacklist')
    remove_parser.add_argument('plate', help='License plate number')
    
    list_parser = blacklist_subparsers.add_parser('list', help='List all blacklisted plates')
    
    # Events command
    events_parser = subparsers.add_parser('events', help='Get recent LPR events')
    events_parser.add_argument('--limit', type=int, default=50, help='Number of events to retrieve')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize client
    client = LPRClient(args.url, args.api_key)
    
    # Execute command
    if args.command == 'recognize':
        if not os.path.exists(args.image):
            print(f"Error: Image file not found: {args.image}")
            return
            
        print(f"Recognizing license plate in: {args.image}")
        result = client.recognize_image(args.image)
        print(json.dumps(result, indent=2))
        
    elif args.command == 'batch':
        valid_images = [img for img in args.images if os.path.exists(img)]
        invalid_images = [img for img in args.images if not os.path.exists(img)]
        
        if invalid_images:
            print(f"Warning: Skipping non-existent files: {invalid_images}")
        
        if not valid_images:
            print("Error: No valid image files found")
            return
            
        print(f"Processing {len(valid_images)} images...")
        results = client.recognize_image_batch(valid_images)
        
        # Summary
        successful = sum(1 for r in results if r.get('success', False))
        print(f"\nSummary: {successful}/{len(results)} images processed successfully")
        
        for result in results:
            if result.get('success'):
                status = "BLACKLISTED" if result.get('is_blacklisted') else "OK"
                print(f"✓ {result['image_path']}: {result['plate']} ({result['confidence']:.1f}%) [{status}]")
            else:
                print(f"✗ {result['image_path']}: {result.get('error', 'Unknown error')}")
    
    elif args.command == 'blacklist':
        if args.blacklist_action == 'check':
            result = client.check_blacklist(args.plate)
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                status = "BLACKLISTED" if result['is_blacklisted'] else "NOT BLACKLISTED"
                print(f"Plate {args.plate}: {status}")
                if result.get('reason'):
                    print(f"Reason: {result['reason']}")
                    
        elif args.blacklist_action == 'add':
            result = client.add_to_blacklist(args.plate, args.reason)
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                print(f"✓ Plate {args.plate} added to blacklist")
                
        elif args.blacklist_action == 'remove':
            result = client.remove_from_blacklist(args.plate)
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                print(f"✓ Plate {args.plate} removed from blacklist")
                
        elif args.blacklist_action == 'list':
            blacklist = client.get_blacklist()
            if blacklist:
                print(f"Blacklisted plates ({len(blacklist)}):")
                for entry in blacklist:
                    reason = f" - {entry['reason']}" if entry.get('reason') else ""
                    print(f"  {entry['plate']}{reason}")
            else:
                print("No blacklisted plates found")
    
    elif args.command == 'events':
        events = client.get_events(args.limit)
        if events:
            print(f"Recent LPR events ({len(events)}):")
            for event in events:
                status = "🚨 BLACKLISTED" if event.get('is_blacklisted') else "✓ OK"
                confidence = f"({event['confidence']:.1f}%)" if event.get('confidence') else ""
                camera = f"[{event['camera_id']}]" if event.get('camera_id') else ""
                print(f"  {event['plate']} {confidence} {camera} {status}")
        else:
            print("No events found")


if __name__ == '__main__':
    main()
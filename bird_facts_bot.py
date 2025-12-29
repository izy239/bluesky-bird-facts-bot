import os
import json
import random
import re
import requests
from datetime import datetime
from atproto import Client, models

def load_bird_facts():
    """Load bird facts from JSON file"""
    with open('bird_facts.json', 'r') as f:
        data = json.load(f)
    return data['facts']

def load_posted_facts():
    """Load previously posted facts to avoid repetition"""
    try:
        with open('data/posted_facts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_posted_fact(fact_index):
    """Save the index of posted fact"""
    posted = load_posted_facts()
    posted.append(fact_index)
    with open('data/posted_facts.json', 'w') as f:
        json.dump(posted, f)

def get_next_fact(facts):
    """Get a bird fact that hasn't been posted yet"""
    posted = load_posted_facts()
    available_indices = [i for i in range(len(facts)) if i not in posted]
    
    # Reset if all facts have been posted
    if not available_indices:
        print("All facts posted! Resetting...")
        with open('data/posted_facts.json', 'w') as f:
            json.dump([], f)
        available_indices = list(range(len(facts)))
    
    fact_index = random.choice(available_indices)
    return fact_index, facts[fact_index]

def extract_bird_name(fact):
    """Extract the bird name from the fact text"""
    # Common patterns for bird names at the start of sentences
    patterns = [
        r'^The ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+)?)',  # "The Arctic Tern has..."
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+)?)\s+(?:are|can|have|weigh|get|stand|live|hold|perform)',  # "Hummingbirds are..."
        r"^A\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:'s)?)",  # "A peacock's tail..."
    ]
    
    for pattern in patterns:
        match = re.match(pattern, fact)
        if match:
            bird_name = match.group(1)
            # Remove possessive 's
            bird_name = bird_name.replace("'s", "")
            return bird_name
    
    return None

def singularize_bird_name(bird_name):
    """Convert plural bird names to singular for better search results"""
    if not bird_name:
        return bird_name
    
    # Common plural patterns for birds
    singular = bird_name
    
    # Simple rules for common bird name plurals
    if bird_name.endswith('ies'):
        # Canaries -> Canary
        singular = bird_name[:-3] + 'y'
    elif bird_name.endswith('oes'):
        # Flamingoes -> Flamingo (though both are correct)
        singular = bird_name[:-2]
    elif bird_name.endswith('ses'):
        # Thrushes -> Thrush
        singular = bird_name[:-2]
    elif bird_name.endswith('ches'):
        # Finches -> Finch
        singular = bird_name[:-2]
    elif bird_name.endswith('xes'):
        # Ibexes -> Ibex (not common for birds but safe)
        singular = bird_name[:-2]
    elif bird_name.endswith('s') and not bird_name.endswith('ss'):
        # Most plurals: Grebes -> Grebe, Terns -> Tern
        # But not: Albatross -> Albatros (wrong)
        # Check if it's likely a plural by looking at common bird endings
        if bird_name.endswith(('rds', 'ks', 'ls', 'ns', 'ts', 'es', 'ws', 'ys')):
            singular = bird_name[:-1]
    
    return singular

def search_flickr_image(bird_name):
    """Search Flickr for a Creative Commons licensed bird image"""
    api_key = os.getenv('FLICKR_API_KEY')
    
    if not api_key:
        print("No Flickr API key found, skipping image")
        return None
    
    # Convert to singular for better search results
    search_name = singularize_bird_name(bird_name)
    print(f"Searching for: {search_name} (original: {bird_name})")
    
    try:
        # Search for Creative Commons licensed images
        url = "https://api.flickr.com/services/rest/"
        params = {
            'method': 'flickr.photos.search',
            'api_key': api_key,
            'text': f'{search_name} bird',
            'license': '1,2,4,5,7,9,10',  # CC licenses (excluding NC and ND for safety)
            'content_type': '1',  # Photos only
            'media': 'photos',
            'sort': 'relevance',
            'per_page': '10',
            'format': 'json',
            'nojsoncallback': '1',
            'extras': 'owner_name,license,url_c,url_z'  # Get medium size images
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('stat') != 'ok' or not data.get('photos', {}).get('photo'):
            print(f"No Flickr images found for {search_name}")
            return None
        
        # Get the first photo with a URL
        for photo in data['photos']['photo']:
            image_url = photo.get('url_c') or photo.get('url_z')  # Try medium, then large
            if image_url:
                owner_name = photo.get('ownername', 'Unknown')
                photo_id = photo['id']
                photo_url = f"https://www.flickr.com/photos/{photo['owner']}/{photo_id}"
                
                return {
                    'url': image_url,
                    'photographer': owner_name,
                    'photo_url': photo_url,
                    'bird_name': bird_name
                }
        
        return None
        
    except Exception as e:
        print(f"Error searching Flickr: {e}")
        return None

def download_image(image_url):
    """Download image from URL"""
    try:
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def create_facets(text, photo_url=None):
    """Create facets for hashtags and photo credit link to make them clickable"""
    facets = []
    
    # Find all hashtags in the text dynamically
    import re
    hashtag_pattern = r'#\w+'
    for match in re.finditer(hashtag_pattern, text):
        hashtag = match.group()
        start = match.start()
        
        # Convert string position to byte position
        byte_start = len(text[:start].encode('utf-8'))
        byte_end = len(text[:start + len(hashtag)].encode('utf-8'))
        
        facets.append(
            models.AppBskyRichtextFacet.Main(
                index=models.AppBskyRichtextFacet.ByteSlice(
                    byte_start=byte_start,
                    byte_end=byte_end
                ),
                features=[models.AppBskyRichtextFacet.Tag(tag=hashtag[1:])]
            )
        )
    
    # Add photo credit link facet if provided
    if photo_url:
        # Find the photographer credit text (e.g., "Photo by John Doe")
        photo_credit_pattern = "📷 Photo by "
        start = text.find(photo_credit_pattern)
        if start != -1:
            # Find the end of the photographer's name (before the newline)
            name_start = start + len(photo_credit_pattern)
            name_end = text.find('\n', name_start)
            if name_end == -1:
                name_end = len(text)
            
            # Create link for the entire "Photo by [Name]" text
            byte_start = len(text[:start].encode('utf-8'))
            byte_end = len(text[:name_end].encode('utf-8'))
            
            facets.append(
                models.AppBskyRichtextFacet.Main(
                    index=models.AppBskyRichtextFacet.ByteSlice(
                        byte_start=byte_start,
                        byte_end=byte_end
                    ),
                    features=[models.AppBskyRichtextFacet.Link(uri=photo_url)]
                )
            )
    
    return facets

def post_to_bluesky(text, image_data=None, alt_text=None, photo_url=None):
    """Post the bird fact to Bluesky with optional image"""
    username = os.getenv('BLUESKY_USERNAME')
    password = os.getenv('BLUESKY_PASSWORD')
    
    if not username or not password:
        raise ValueError("BLUESKY_USERNAME and BLUESKY_PASSWORD must be set")
    
    client = Client()
    client.login(username, password)
    
    # Create facets for clickable hashtags and photo credit link
    facets = create_facets(text, photo_url)
    
    # Upload image if provided
    embed = None
    if image_data:
        try:
            print("Uploading image to Bluesky...")
            upload = client.upload_blob(image_data)
            
            # Create image embed with alt text
            embed = models.AppBskyEmbedImages.Main(
                images=[
                    models.AppBskyEmbedImages.Image(
                        image=upload.blob,
                        alt=alt_text or "Bird photograph"
                    )
                ]
            )
            print("Image uploaded successfully")
        except Exception as e:
            print(f"Error uploading image: {e}")
            embed = None
    
    # Send post with facets and optional image
    post = client.send_post(text=text, facets=facets, embed=embed)
    print(f"Posted successfully at {datetime.now()}")
    return post

def main():
    """Main function to post daily bird fact"""
    try:
        print("Loading bird facts...")
        facts = load_bird_facts()
        
        print("Selecting a bird fact...")
        fact_index, fact = get_next_fact(facts)
        
        # Try to extract bird name and find image
        bird_name = extract_bird_name(fact)
        print(f"Extracted bird name: {bird_name}")
        
        image_info = None
        image_data = None
        photo_url = None
        post_text = f"🐦 Bird Fact of the Day 🐦\n\n{fact}\n\n"
        
        if bird_name:
            print(f"Searching Flickr for {bird_name}...")
            image_info = search_flickr_image(bird_name)
            
            if image_info:
                print(f"Found image by {image_info['photographer']}")
                image_data = download_image(image_info['url'])
                photo_url = image_info['photo_url']
                
                if image_data:
                    # Add photo credit to the post
                    post_text += f"📷 Photo by {image_info['photographer']}\n\n"
        
        # Add hashtags - include bird name hashtag if available
        if bird_name:
            # Convert bird name to hashtag format (remove spaces, keep camelCase)
            bird_hashtag = bird_name.replace(' ', '').replace('-', '')
            post_text += f"#{bird_hashtag} #birdfacts #Birds #Nature"
        else:
            post_text += "#birdfacts #Birds #Nature"
        
        # Create alt text
        alt_text = f"Photograph of a {bird_name}" if bird_name else "Bird photograph"
        
        print(f"Posting: {post_text[:50]}...")
        post_to_bluesky(post_text, image_data, alt_text, photo_url)
        
        # Save that we posted this fact
        save_posted_fact(fact_index)
        
        print("Success!")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()

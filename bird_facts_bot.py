import os
import json
import random
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
        with open('posted_facts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_posted_fact(fact_index):
    """Save the index of posted fact"""
    posted = load_posted_facts()
    posted.append(fact_index)
    with open('posted_facts.json', 'w') as f:
        json.dump(posted, f)

def get_next_fact(facts):
    """Get a bird fact that hasn't been posted yet"""
    posted = load_posted_facts()
    available_indices = [i for i in range(len(facts)) if i not in posted]
    
    # Reset if all facts have been posted
    if not available_indices:
        print("All facts posted! Resetting...")
        with open('posted_facts.json', 'w') as f:
            json.dump([], f)
        available_indices = list(range(len(facts)))
    
    fact_index = random.choice(available_indices)
    return fact_index, facts[fact_index]

def create_facets(text):
    """Create facets for hashtags to make them clickable"""
    facets = []
    hashtags = ['#birdfacts', '#Birds', '#Nature']
    
    for hashtag in hashtags:
        start = text.find(hashtag)
        if start != -1:
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
    
    return facets

def post_to_bluesky(text):
    """Post the bird fact to Bluesky with clickable hashtags"""
    username = os.getenv('BLUESKY_USERNAME')
    password = os.getenv('BLUESKY_PASSWORD')
    
    if not username or not password:
        raise ValueError("BLUESKY_USERNAME and BLUESKY_PASSWORD must be set")
    
    client = Client()
    client.login(username, password)
    
    # Create facets for clickable hashtags
    facets = create_facets(text)
    
    # Send post with facets
    post = client.send_post(text=text, facets=facets)
    print(f"Posted successfully at {datetime.now()}")
    return post

def main():
    """Main function to post daily bird fact"""
    try:
        print("Loading bird facts...")
        facts = load_bird_facts()
        
        print("Selecting a bird fact...")
        fact_index, fact = get_next_fact(facts)
        
        # Format the post
        post_text = f"🐦 Bird Fact of the Day 🐦\n\n{fact}\n\n#birdfacts #Birds #Nature"
        
        print(f"Posting: {post_text[:50]}...")
        post_to_bluesky(post_text)
        
        # Save that we posted this fact
        save_posted_fact(fact_index)
        
        print("Success!")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()

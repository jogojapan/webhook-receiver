from flask import Flask, request
import datetime
import requests
import json
import os

app = Flask(__name__)

# Configuration from environment variables
GOTIFY_URL = os.getenv('GOTIFY_URL', 'http://localhost:80')
GOTIFY_TOKEN = os.getenv('GOTIFY_TOKEN')
WATCHED_IMAGES_STR = os.getenv('WATCHED_IMAGES', '')
WATCHED_IMAGES = [img.strip() for img in WATCHED_IMAGES_STR.split(',') if img.strip()]

# Validate required environment variables
if not GOTIFY_TOKEN:
    raise ValueError("GOTIFY_TOKEN environment variable is required")

if not WATCHED_IMAGES:
    raise ValueError("WATCHED_IMAGES environment variable is required")

print(f"Gotify URL: {GOTIFY_URL}")
print(f"Watching images: {WATCHED_IMAGES}")

@app.route('/docker-webhook', methods=['POST'])
def docker_webhook():
    try:
        data = request.json

        # Check if this is a push event
        if "push_data" not in data:
            return "Not a push event", 200

        # Extract repository and tag information
        repo_name = data.get('repository', {}).get('name', 'Unknown')
        repo_full_name = data.get('repository', {}).get('repo_name', 'Unknown')
        tag = data.get('push_data', {}).get('tag', 'Unknown')
        pushed_at = data.get('push_data', {}).get('pushed_at', 'Unknown')
        pushed_at_utc = datetime.datetime.utcfromtimestamp(pushed_at)
        pushed_at_readable = pushed_at_utc.strftime('%Y-%m-%d %H:%M:%S UTC')

        # Check if this is one of our watched images
        if repo_name not in WATCHED_IMAGES and repo_full_name not in WATCHED_IMAGES:
            print(f"Image {repo_full_name} not in watch list", flush=True)
            return f"Image {repo_full_name} not in watch list", 200

        # Prepare notification message
        title = f"🐳 New Docker Tag Released"
        message = f"**Image:** {repo_full_name}\n**Tag:** {tag}\n**Pushed:** {pushed_at_readable}"

        # Send notification to Gotify
        gotify_payload = {
            "title": title,
            "message": message,
            "priority": 5
        }

        response = requests.post(
            f"{GOTIFY_URL}/message",
            params={"token": GOTIFY_TOKEN},
            json=gotify_payload
        )

        if response.status_code == 200:
            print(f"Notification sent for {repo_full_name}:{tag}", flush=True)
            return "Notification sent", 200
        else:
            print(f"Failed to send notification: {response.status_code} - {response.text}", flush=True)
            return "Failed to send notification", 500

    except Exception as e:
        print(f"Error processing webhook: {e}", flush=True)
        return "Error processing webhook", 500

@app.route('/health', methods=['GET'])
def health_check():
    return {
        "status": "running",
        "gotify_url": GOTIFY_URL,
        "watched_images": WATCHED_IMAGES
    }, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

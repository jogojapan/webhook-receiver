# Docker Hub Webhook to Gotify Notifier

A lightweight webhook receiver that forwards Docker Hub push notifications to your self-hosted Gotify instance. Get instant notifications when new tags are released for your watched Docker images.

## 🚀 Features

- **Real-time notifications**: Receive instant alerts when new Docker tags are pushed
- **Selective monitoring**: Watch only the Docker images you care about
- **Self-hosted**: No dependency on third-party services like Zapier
- **Lightweight**: Minimal resource footprint with Python Flask
- **Docker-ready**: Runs as a container with docker-compose support
- **Configurable**: Environment variable configuration for easy deployment

## 📋 Prerequisites

- Docker and Docker Compose
- A running [Gotify](https://gotify.net/) instance
- Access to configure webhooks on Docker Hub repositories

## 🏗️ Project Structure

```
.
├── Dockerfile
├── README.md
├── requirements.txt
└── scripts
    └── receiver.py
```

## 📁 File Contents

### ```Dockerfile```
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY scripts/receiver.py .
EXPOSE 5000
CMD ["python", "receiver.py"]
```

### ```requirements.txt```
```
Flask==2.3.3
requests==2.31.0
```

### ```receiver.py```

``` python
from flask import Flask, request
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
        if data.get('action') != 'push':
            return "Not a push event", 200

        # Extract repository and tag information
        repo_name = data.get('repository', {}).get('name', 'Unknown')
        repo_full_name = data.get('repository', {}).get('repo_name', 'Unknown')
        tag = data.get('target', {}).get('tag', 'Unknown')
        pushed_at = data.get('target', {}).get('date', 'Unknown')

        # Check if this is one of our watched images
        if repo_name not in WATCHED_IMAGES and repo_full_name not in WATCHED_IMAGES:
            print(f"Image {repo_full_name} not in watch list")
            return f"Image {repo_full_name} not in watch list", 200

        # Prepare notification message
        title = f"🐳 New Docker Tag Released"
        message = f"**Image:** {repo_full_name}\n**Tag:** {tag}\n**Pushed:** {pushed_at}"

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
            print(f"Notification sent for {repo_full_name}:{tag}")
            return "Notification sent", 200
        else:
            print(f"Failed to send notification: {response.status_code} - {response.text}")
            return "Failed to send notification", 500

    except Exception as e:
        print(f"Error processing webhook: {e}")
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
```

## 🐳 Running with Docker

### Build the Image
```bash
docker build -t jogojapan/webhook-receiver .
```

### Run with Command Line
```bash
docker run -d \
  --name webhook-receiver \
  -p 5000:5000 \
  -e GOTIFY_URL="http://your-gotify-server:80" \
  -e GOTIFY_TOKEN="your-application-token" \
  -e WATCHED_IMAGES="nginx,postgres,redis" \
  jogojapan/webhook-receiver
```

## 🔧 Docker Compose Usage

### Complete Setup with Gotify

```yaml
version: '3.8'

services:
  webhook-receiver:
    image: jogojapan/webhook-receiver
    ports:
      - "5000:5000"
    environment:
      - GOTIFY_URL=http://gotify:80
      - GOTIFY_TOKEN=AaaBbbCccDddEee123456
      - WATCHED_IMAGES=nginx,postgres,redis,mysql/mysql-server
    restart: unless-stopped
    depends_on:
      - gotify

  gotify:
    image: gotify/server
    ports:
      - "8080:80"
    environment:
      - GOTIFY_DEFAULTUSER_PASS=your-secure-password
    volumes:
      - gotify-data:/app/data
    restart: unless-stopped

volumes:
  gotify-data:
```

### Using with Existing Gotify Instance

```yaml
version: '3.8'

services:
  webhook-receiver:
    image: jogojapan/webhook-receiver
    ports:
      - "5000:5000"
    environment:
      - GOTIFY_URL=https://gotify.yourdomain.com
      - GOTIFY_TOKEN=AaaBbbCccDddEee123456
      - WATCHED_IMAGES=nginx,postgres,redis
    restart: unless-stopped
```

### Start the Services
```bash
docker-compose up -d
```

### View Logs
```bash
docker-compose logs -f webhook-receiver
```

## ⚙️ Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| ```GOTIFY_URL``` | Full URL to your Gotify server | Yes | ```http://gotify:80```<br>```https://gotify.example.com``` |
| ```GOTIFY_TOKEN``` | Application token from Gotify | Yes | ```AaaBbbCccDddEee123456``` |
| ```WATCHED_IMAGES``` | Comma-separated list of Docker images to monitor | Yes | ```nginx,postgres,redis```<br>```myuser/myapp,nginx``` |

### Environment Variable Details

#### ```GOTIFY_URL```
- **Format**: Complete URL including protocol and port
- **Examples**:
  - ```http://localhost:8080``` - Local Gotify instance
  - ```http://gotify:80``` - Docker Compose service name
  - ```https://gotify.yourdomain.com``` - External Gotify with reverse proxy

#### ```GOTIFY_TOKEN```
- **How to obtain**:
  1. Open your Gotify web interface
  2. Navigate to **Apps**
  3. Click **Create Application**
  4. Name it (e.g., "Docker Hub Notifications")
  5. Copy the generated token

#### ```WATCHED_IMAGES```
- **Format**: Comma-separated list (no spaces around commas)
- **Image name formats**:
  - ```nginx``` - Official image (short form)
  - ```library/nginx``` - Official image (full form)
  - ```username/imagename``` - User repository
  - ```organization/imagename``` - Organization repository

## 🔗 Docker Hub Webhook Configuration

### For Each Repository You Want to Monitor:

1. **Navigate to your Docker Hub repository**
   - Go to ```https://hub.docker.com/r/your-username/your-image```
   - Or ```https://hub.docker.com/_/nginx``` for official images (requires permissions)

2. **Access Webhook Settings**
   - Click **Settings** → **Webhooks**

3. **Create New Webhook**
   - **Name**: ```Gotify Notifications```
   - **Webhook URL**: ```http://your-server-ip:5000/docker-webhook```
   - Click **Create**

### Example Webhook URLs
- Local development: ```http://localhost:5000/docker-webhook```
- VPS deployment: ```http://your-vps-ip:5000/docker-webhook```
- Domain with reverse proxy: ```https://webhooks.yourdomain.com/docker-webhook```

## 🧪 Testing the Setup

### 1. Health Check
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "running",
  "gotify_url": "http://gotify:80",
  "watched_images": ["nginx", "postgres", "redis"]
}
```

### 2. Test Webhook Manually
```bash
curl -X POST http://localhost:5000/docker-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "action": "push",
    "repository": {
      "name": "nginx",
      "repo_name": "library/nginx"
    },
    "target": {
      "tag": "latest",
      "date": "2023-01-01T12:00:00Z"
    }
  }'
```

### 3. Verify Gotify Notification
Check your Gotify web interface or mobile app for the test notification.

## 📱 Example Notification

When a new tag is pushed, you'll receive a Gotify notification like:

```
🐳 New Docker Tag Released

Image: library/nginx
Tag: 1.25.3-alpine
Pushed: 2023-12-01T14:30:00Z
```

## 🔒 Security Considerations

### Production Deployment
- Use HTTPS for webhook endpoints
- Consider adding webhook signature verification
- Restrict network access to the webhook receiver
- Use strong passwords for Gotify

### Webhook Signature Verification (Optional)
Add this to your Docker Hub webhook configuration and update the Python script:
```python
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
# Add signature verification logic
```

## 🐛 Troubleshooting

### Common Issues

#### **Webhook receiver not receiving notifications**
1. **Check webhook URL**: Ensure Docker Hub can reach your server
2. **Verify port accessibility**: Test with ```curl``` from external source
3. **Check logs**: ```docker-compose logs webhook-receiver```

#### **Notifications not appearing in Gotify**
1. **Verify token**: Check Gotify app token is correct
2. **Test Gotify API directly**:
   ```bash
   curl -X POST "http://your-gotify:80/message?token=YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test","message":"Test message"}'
   ```

#### **Image not being monitored**
1. **Check image name format**: Use exact name from Docker Hub
2. **Verify WATCHED_IMAGES**: Check environment variable syntax
3. **Test with health endpoint**: Confirm watched images list

### Debug Mode
Enable debug logging by modifying the Python script:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ✨ Acknowledgments

- [Gotify](https://gotify.net/) - Self-hosted notification server
- [Docker Hub](https://hub.docker.com/) - Container registry and webhook provider
- [Flask](https://flask.palletsprojects.com/) - Lightweight web framework


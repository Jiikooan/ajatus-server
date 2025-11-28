# Deployment Guide

This guide covers deploying the Ajatus Server to various platforms.

## Prerequisites

Before deploying, ensure you have:

1. **Fireworks AI API Key**
   - Sign up at [Fireworks AI](https://fireworks.ai)
   - Create an API key from the dashboard
   - Model: `accounts/fireworks/models/llama-v4-maverick`

2. **Stripe Account**
   - Create account at [Stripe](https://stripe.com)
   - Get API keys from Dashboard → Developers → API keys
   - Set up webhook endpoint for payment events

## Environment Variables

Required environment variables for production:

```bash
FIREWORKS_API_KEY=fw_xxx...
STRIPE_SECRET_KEY=sk_live_xxx...
STRIPE_WEBHOOK_SECRET=whsec_xxx...
PORT=8000
ENVIRONMENT=production
```

## Deployment Options

### 1. Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

1. Click "Deploy on Railway"
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard
4. Deploy!

Railway will automatically:
- Build the Docker image
- Expose the service on a public URL
- Handle SSL/TLS certificates

### 2. Render

1. Create new Web Service on [Render](https://render.com)
2. Connect GitHub repository: `Jiikooan/ajatus-server`
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables
5. Deploy

### 3. Fly.io

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Create app: `fly launch`
4. Set secrets:
   ```bash
   fly secrets set FIREWORKS_API_KEY=fw_xxx...
   fly secrets set STRIPE_SECRET_KEY=sk_live_xxx...
   fly secrets set STRIPE_WEBHOOK_SECRET=whsec_xxx...
   ```
5. Deploy: `fly deploy`

### 4. Docker (Self-hosted)

```bash
# Build image
docker build -t ajatus-server .

# Run container
docker run -d \
  -p 8000:8000 \
  -e FIREWORKS_API_KEY=fw_xxx... \
  -e STRIPE_SECRET_KEY=sk_live_xxx... \
  -e STRIPE_WEBHOOK_SECRET=whsec_xxx... \
  --name ajatus-server \
  ajatus-server
```

Or use docker-compose:

```bash
# Create .env file with your keys
cp .env.example .env
# Edit .env with your actual keys

# Start services
docker-compose up -d
```

### 5. Heroku

1. Create Heroku app: `heroku create ajatus-server`
2. Set buildpack: `heroku buildpacks:set heroku/python`
3. Add Procfile:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
4. Set environment variables:
   ```bash
   heroku config:set FIREWORKS_API_KEY=fw_xxx...
   heroku config:set STRIPE_SECRET_KEY=sk_live_xxx...
   heroku config:set STRIPE_WEBHOOK_SECRET=whsec_xxx...
   ```
5. Deploy: `git push heroku master`

## Stripe Webhook Configuration

After deploying, configure Stripe webhook:

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. Enter your webhook URL: `https://your-domain.com/api/stripe-webhook`
4. Select events to listen for:
   - `checkout.session.completed`
5. Copy the webhook signing secret
6. Update `STRIPE_WEBHOOK_SECRET` environment variable

## Health Check

Test your deployment:

```bash
curl https://your-domain.com/
```

Expected response:
```json
{
  "status": "online",
  "service": "Ajatuskumppani API",
  "version": "1.0.0",
  "fireworks_available": true,
  "stripe_configured": true,
  "timestamp": "2025-11-28T14:00:00"
}
```

## API Documentation

Once deployed, access API documentation at:

- **Swagger UI**: `https://your-domain.com/docs`
- **ReDoc**: `https://your-domain.com/redoc`

## Monitoring

### Logs

View application logs:

```bash
# Railway
railway logs

# Render
render logs

# Fly.io
fly logs

# Docker
docker logs ajatus-server
```

### Health Checks

Set up health check monitoring:

- **Endpoint**: `GET /`
- **Expected Status**: 200
- **Interval**: 30 seconds

## Scaling

### Horizontal Scaling

Most platforms support auto-scaling:

- **Railway**: Configure in dashboard
- **Render**: Upgrade to paid plan
- **Fly.io**: `fly scale count 3`

### Database Migration

For production, replace in-memory storage with PostgreSQL:

1. Add PostgreSQL to your deployment
2. Install `psycopg2` or `asyncpg`
3. Update `main.py` to use database instead of `user_balances` dict

## Security Checklist

- [ ] Use HTTPS only (handled by platform)
- [ ] Set `ENVIRONMENT=production`
- [ ] Use production Stripe keys (`sk_live_...`)
- [ ] Configure CORS for specific origins only
- [ ] Enable rate limiting (TODO: implement)
- [ ] Set up monitoring and alerts
- [ ] Regular security updates

## Troubleshooting

### Server won't start

Check logs for:
- Missing environment variables
- Port conflicts
- Module import errors

### Stripe webhook fails

Verify:
- Webhook URL is correct
- `STRIPE_WEBHOOK_SECRET` matches Stripe dashboard
- Endpoint is publicly accessible

### Fireworks AI errors

Check:
- API key is valid
- Model name is correct
- Account has sufficient credits

## Support

For deployment issues:

- **GitHub Issues**: https://github.com/Jiikooan/ajatus-server/issues
- **Email**: ajatuskumppani@pinnacore.ai
- **Discord**: https://discord.gg/ajatuskumppani


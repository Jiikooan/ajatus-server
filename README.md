# Ajatus Server

Backend API server for Ajatuskumppani - Finnish-first open-source decentralized AI platform.

## Features

- 🤖 **Fireworks AI Integration** - Chat completions with streaming support
- 💳 **Stripe Payments** - AJT token purchases via credit card
- 🔐 **Wallet-based Auth** - Solana wallet address authentication
- 📊 **Balance Management** - Track AJT token consumption
- 🚀 **FastAPI** - Modern, fast, async Python web framework

## Tech Stack

- **Framework**: FastAPI 0.115+
- **AI Provider**: Fireworks AI (Llama 4 Maverick)
- **Payments**: Stripe
- **Server**: Uvicorn (ASGI)

## Installation

### Prerequisites

- Python 3.11+
- Fireworks AI API key
- Stripe account (for payments)

### Setup

1. **Clone the repository**

```bash
git clone https://github.com/Jiikooan/ajatus-server.git
cd ajatus-server
```

2. **Create virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:

- `FIREWORKS_API_KEY` - Get from [Fireworks AI](https://fireworks.ai)
- `STRIPE_SECRET_KEY` - Get from [Stripe Dashboard](https://dashboard.stripe.com)
- `STRIPE_WEBHOOK_SECRET` - Create webhook endpoint in Stripe
- `PORT` - Server port (default: 8000)

5. **Run the server**

```bash
# Development mode with auto-reload
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check

```http
GET /
```

Returns server status and configuration.

**Response:**
```json
{
  "status": "online",
  "service": "Ajatuskumppani API",
  "version": "1.0.0",
  "fireworks_available": true,
  "stripe_configured": true,
  "timestamp": "2025-11-27T19:00:00"
}
```

### Chat Completion

```http
POST /api/chat
```

Send messages to Fireworks AI and receive responses. Supports streaming.

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "Hei! Mikä on Suomen pääkaupunki?"}
  ],
  "model": "accounts/fireworks/models/llama-v4-maverick",
  "stream": true,
  "max_tokens": 2048,
  "temperature": 0.7,
  "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
}
```

**Response (Streaming):**
```
data: {"content": "Suomen"}
data: {"content": " pääkaupunki"}
data: {"content": " on"}
data: {"content": " Helsinki"}
data: [DONE]
```

**Response (Non-streaming):**
```json
{
  "content": "Suomen pääkaupunki on Helsinki.",
  "model": "accounts/fireworks/models/llama-v4-maverick",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 8,
    "total_tokens": 23
  }
}
```

### Get Balance

```http
GET /api/balance?wallet_address=7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
```

Get AJT token balance for a wallet address.

**Response:**
```json
{
  "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
  "balance": 1000,
  "consumed": 0,
  "last_updated": "2025-11-27T19:00:00"
}
```

### Create Checkout Session

```http
POST /api/create-checkout-session
```

Create a Stripe checkout session for purchasing AJT tokens.

**Request Body:**
```json
{
  "amount": 10000,
  "currency": "usd",
  "success_url": "https://ajatuskumppani.manus.space/payment/success",
  "cancel_url": "https://ajatuskumppani.manus.space/chat",
  "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
}
```

**Response:**
```json
{
  "sessionId": "cs_test_a1b2c3d4e5f6g7h8i9j0",
  "url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

### Stripe Webhook

```http
POST /api/stripe-webhook
```

Webhook endpoint for Stripe payment events. Automatically credits AJT tokens after successful payment.

**Headers:**
- `stripe-signature`: Webhook signature for verification

## Token Economics

- **Initial Credits**: 1000 AJT (free)
- **Chat Cost**: 1 AJT per message
- **Purchase Rate**: 1000 AJT = $1 USD

## Development

### Project Structure

```
ajatus-server/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Your environment variables (git-ignored)
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

### Testing

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest
```

### API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables (Production)

Set these in your deployment platform:

- `FIREWORKS_API_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `PORT`
- `ENVIRONMENT=production`

## Security

- ✅ CORS configured for specific origins
- ✅ Stripe webhook signature verification
- ✅ Input validation with Pydantic
- ⚠️ TODO: Add rate limiting
- ⚠️ TODO: Add JWT authentication
- ⚠️ TODO: Replace in-memory storage with PostgreSQL

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

- **Email**: ajatuskumppani@pinnacore.ai
- **GitHub**: https://github.com/Jiikooan/ajatus-server
- **Discord**: https://discord.gg/ajatuskumppani

## Roadmap

- [ ] PostgreSQL database integration
- [ ] Redis caching layer
- [ ] Rate limiting per wallet
- [ ] JWT authentication
- [ ] Docker sandbox for code execution
- [ ] WebSocket support for real-time updates
- [ ] Monitoring and analytics
- [ ] Multi-model support (GPT-4, Claude, etc.)


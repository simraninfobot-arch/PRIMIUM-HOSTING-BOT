# Docker pe Deploy

## Step 1 — .env file banao
```bash
cp .env.example .env
nano .env
```

## Step 2 — Docker Compose se start karo
```bash
docker-compose up -d
```

## Useful commands
```bash
# Logs dekho
docker-compose logs -f

# Restart karo
docker-compose restart

# Band karo
docker-compose down
```

## Sirf Docker (Compose ke bina)
```bash
docker build -t telegram-hosting-bot .
docker run -d --env-file .env --name tgbot telegram-hosting-bot
```

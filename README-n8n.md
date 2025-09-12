# n8n Docker Compose Setup

This setup provides a complete n8n automation platform with PostgreSQL database and Redis caching, optimized for local network access.

## Services Included

- **n8n**: Main automation platform
- **PostgreSQL**: Robust database for production use
- **Redis**: Caching and queue management (optional)

## Quick Start

1. **Prepare environment file**:
   ```bash
   cp .env.example .env
   # Edit .env file with your desired credentials and network settings
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **Access n8n**:
   - Local access: http://localhost:5678
   - Network access: http://YOUR_SERVER_IP:5678
   - Login with credentials from .env file (default: admin/changeme123)

## Network Configuration

### For Local Network Access

1. Find your server's IP address:
   ```bash
   ip addr show | grep inet
   ```

2. Update the WEBHOOK_URL in .env file:
   ```
   WEBHOOK_URL=http://192.168.1.100:5678/
   ```

3. Access n8n from other devices: `http://192.168.1.100:5678`

## Directory Structure

```
├── docker-compose.yml     # Main compose file
├── .env                   # Environment configuration
├── n8n-data/             # n8n persistent data (auto-created)
├── local-files/          # File sharing directory
└── README-n8n.md         # This file
```

## Security Notes

⚠️ **Important**: Change default passwords in .env file before production use!

- Update N8N_BASIC_AUTH_PASSWORD
- Update DB_POSTGRES_PASSWORD
- Update REDIS_PASSWORD

## Useful Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f n8n

# Stop services
docker-compose down

# Update to latest versions
docker-compose pull && docker-compose up -d

# Backup n8n data
docker run --rm -v n8n_n8n_data:/data -v $(pwd):/backup alpine tar czf /backup/n8n-backup.tar.gz -C /data .

# Restore n8n data
docker run --rm -v n8n_n8n_data:/data -v $(pwd):/backup alpine tar xzf /backup/n8n-backup.tar.gz -C /data
```

## Troubleshooting

### Can't access from network
1. Check firewall settings: `sudo ufw status`
2. Verify n8n is binding to 0.0.0.0: check container logs
3. Ensure WEBHOOK_URL matches your server IP

### Database connection issues
1. Check PostgreSQL container status: `docker-compose logs postgres`
2. Verify database credentials in .env file

### Performance optimization
- Increase Docker resources if needed
- Consider using external PostgreSQL for production
- Monitor container resource usage: `docker stats`

## File Operations

The `local-files/` directory is mounted to `/files` in the n8n container. Use this path in n8n's "Read/Write Files from Disk" nodes.

## External Libraries

The setup allows common libraries (axios, lodash, moment). Add more in docker-compose.yml under `NODE_FUNCTION_ALLOW_EXTERNAL`.

## Production Considerations

- Use strong passwords
- Set up SSL/TLS with reverse proxy (Traefik/Nginx)
- Regular backups
- Monitor resource usage
- Consider using managed database services
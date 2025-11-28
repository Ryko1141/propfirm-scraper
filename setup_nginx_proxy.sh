#!/bin/bash
# Nginx Reverse Proxy Setup Script for MT5 REST API
# Run with: bash setup_nginx_proxy.sh

set -e

echo "============================================================"
echo "MT5 REST API - Nginx Reverse Proxy Setup"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Please run as root: sudo bash setup_nginx_proxy.sh"
    exit 1
fi

# Install Nginx
echo "1. Installing Nginx..."
apt-get update -qq
apt-get install -y nginx

echo "✓ Nginx installed"
echo ""

# Copy configuration
echo "2. Configuring Nginx..."
cp nginx_mt5_api.conf /etc/nginx/sites-available/mt5_api
ln -sf /etc/nginx/sites-available/mt5_api /etc/nginx/sites-enabled/mt5_api

# Remove default site
rm -f /etc/nginx/sites-enabled/default

echo "✓ Configuration copied"
echo ""

# Generate self-signed certificate (for testing)
echo "3. Generating SSL certificate..."
mkdir -p /etc/ssl/private
chmod 700 /etc/ssl/private

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/mt5_api.key \
    -out /etc/ssl/certs/mt5_api.crt \
    -subj "/C=US/ST=State/L=City/O=YourCompany/CN=api.yourdomain.com" \
    2>/dev/null

chmod 600 /etc/ssl/private/mt5_api.key

echo "✓ Self-signed certificate generated"
echo "⚠️  For production, replace with a valid certificate from Let's Encrypt"
echo ""

# Test configuration
echo "4. Testing Nginx configuration..."
nginx -t

if [ $? -ne 0 ]; then
    echo "✗ Configuration test failed"
    exit 1
fi

echo "✓ Configuration is valid"
echo ""

# Create log directory
mkdir -p /var/log/nginx
chmod 755 /var/log/nginx

# Restart Nginx
echo "5. Restarting Nginx..."
systemctl enable nginx
systemctl restart nginx

echo "✓ Nginx restarted"
echo ""

# Show status
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "Nginx Status:"
systemctl status nginx --no-pager | head -5
echo ""
echo "Access your API at:"
echo "  • HTTP:  http://localhost (redirects to HTTPS)"
echo "  • HTTPS: https://localhost"
echo "  • Docs:  https://localhost/docs"
echo ""
echo "Rate Limits Configured:"
echo "  • Login:  5 requests/minute (burst 3)"
echo "  • API:    60 requests/minute (burst 20)"
echo "  • Global: 100 requests/minute (burst 50)"
echo ""
echo "Connection Limits:"
echo "  • Max 10 concurrent connections per IP"
echo ""
echo "Logs:"
echo "  • Access: /var/log/nginx/mt5_api_access.log"
echo "  • Error:  /var/log/nginx/mt5_api_error.log"
echo ""
echo "⚠️  Remember to:"
echo "  1. Update server_name in /etc/nginx/sites-available/mt5_api"
echo "  2. Replace self-signed certificate with valid SSL certificate"
echo "  3. Configure firewall rules (allow 80, 443)"
echo ""
echo "Next steps:"
echo "  • Test: curl -k https://localhost/health"
echo "  • Monitor: tail -f /var/log/nginx/mt5_api_access.log"
echo "  • Reload config: sudo systemctl reload nginx"
echo "============================================================"

# Use the official NGINX base image
FROM nginx:alpine

# Copy custom NGINX configuration file
COPY nginx.conf /etc/nginx/nginx.conf

# Copy test HTML files to nginx default directory
COPY html/* /usr/share/nginx/html/

# Expose port 80
EXPOSE 80

# nginx runs in foreground by default
CMD ["nginx", "-g", "daemon off;"]
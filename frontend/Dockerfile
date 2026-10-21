# Use official, ultra-lightweight Alpine Nginx web server
FROM nginx:alpine

# Copy only the CONTENTS of your locally compiled static Vue 3 /dist assets straight into Nginx's public HTML directory
# Adding trailing slashes ./dist/ and /html/ explicitly forces Docker to copy the files inside the folder, 
# preventing any accidental directory nesting or blank page errors!
COPY ./dist/ /usr/share/nginx/html/

# Expose the default container port
EXPOSE 8080

# Google Cloud Run requires Nginx to listen dynamically on the $PORT environment variable.
# We run an un-crashable startup script that replaces any '80' listening ports (both IPv4 and IPv6) 
# inside Nginx's default config with the dynamic '$PORT' provided by Cloud Run, and boot Nginx!
CMD ["sh", "-c", "sed -i 's/80/'\"$PORT\"'/g' /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
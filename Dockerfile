FROM php:8.2-apache

# Enable Apache mod_rewrite and required PHP extensions
RUN a2enmod rewrite && \
    docker-php-ext-install pdo pdo_mysql && \
    apt-get update && apt-get install -y --no-install-recommends \
        libcurl4-openssl-dev \
    && docker-php-ext-install curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /var/www/html

# Copy entire project into Apache's web root
COPY . .

# Apache config: allow .htaccess overrides and set document root
RUN echo '<Directory /var/www/html>\n\
    Options Indexes FollowSymLinks\n\
    AllowOverride All\n\
    Require all granted\n\
</Directory>' > /etc/apache2/conf-available/project.conf \
    && a2enconf project

# Fix permissions
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html

# Railway sets PORT env var — Apache listens on it
RUN sed -i 's/Listen 80/Listen ${PORT:-80}/' /etc/apache2/ports.conf \
    && sed -i 's/<VirtualHost \*:80>/<VirtualHost *:${PORT:-80}>/' \
       /etc/apache2/sites-enabled/000-default.conf

EXPOSE 80

CMD ["apache2-foreground"]
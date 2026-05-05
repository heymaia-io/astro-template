# Local-only PHP image used by docker-compose.yml to test the contact form.
# msmtp is a tiny sendmail-compatible binary that forwards every mail() call
# to the mailpit service instead of trying to deliver real mail.
FROM php:8.2-apache

RUN apt-get update \
    && apt-get install -y --no-install-recommends msmtp ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN printf 'account default\nhost mailpit\nport 1025\nfrom contact@localhost\nauto_from on\ntls off\n' > /etc/msmtprc \
    && chmod 644 /etc/msmtprc

RUN printf 'sendmail_path = /usr/bin/msmtp -t -i\n' > /usr/local/etc/php/conf.d/sendmail.ini

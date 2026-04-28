FROM alpine:3.20

RUN apk add --no-cache unbound bind-tools ca-certificates \
    && mkdir -p /var/lib/unbound \
    && chown -R unbound:unbound /var/lib/unbound

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 5335/tcp 5335/udp
HEALTHCHECK --interval=60s --timeout=5s --retries=3 CMD dig @127.0.0.1 -p 5335 example.com A +time=3 +tries=1 >/dev/null || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

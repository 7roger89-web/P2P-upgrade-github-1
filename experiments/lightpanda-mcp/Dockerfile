# Lightpanda 1.0.2 official browser image (no Chromium).
FROM lightpanda/browser:1.0.2

ENV LIGHTPANDA_DISABLE_TELEMETRY=true \
    LIGHTPANDA_DISABLE_CORE_DUMP=1 \
    PORT=10000

EXPOSE 10000

# Render terminates HTTPS and proxies /mcp to this container.
CMD ["/bin/lightpanda", "mcp", "--host", "0.0.0.0", "--port", "10000", "--block-private-networks", "--obey-robots"]

FROM nousresearch/hermes-agent:latest

USER root

ARG HERMES_PATCHES_VERSION=1.6.1

# Apply the selected hermes-patches set at image-build time because the
# upstream image intentionally seals /opt/hermes read-only at runtime.
# Security-sensitive Tirith auto-approval and Chinese menu localization
# are intentionally NOT enabled.
RUN set -eux; \
    uvx --from "hermes-patches==${HERMES_PATCHES_VERSION}" hermes-patches \
      --target /opt/hermes \
      --only footer table db nostream clean-think smart-split terminal-cwd state-guard; \
    uvx --from "hermes-patches==${HERMES_PATCHES_VERSION}" hermes-patches \
      --target /opt/hermes --status --json > /tmp/hermes-patches-status.json; \
    python3 -c 'import json; d=json.load(open("/tmp/hermes-patches-status.json")); req={"footer","table","db","nostream","clean-think","smart-split","terminal-cwd","state-guard"}; missing=[x for x in sorted(req) if not d["patches"].get(x,{}).get("applied")]; assert not missing, f"hermes-patches missing after build: {missing}"'; \
    rm -f /tmp/hermes-patches-status.json

# --- Read-only Logistics connector dependency -------------------------------
# The base image does not bundle pymongo. Install it into the Hermes runtime
# venv (/opt/hermes/.venv) so the hermes-logistics plugin can execute real
# read-only MongoDB queries. /opt/hermes is sealed read-only at runtime, so
# this must happen at build time.
RUN set -eux; \
    uv pip install --python /opt/hermes/.venv/bin/python --no-cache-dir "pymongo>=4.6,<5" || \
    /opt/hermes/.venv/bin/python -m pip install --no-cache-dir "pymongo>=4.6,<5"

# --- Copy the read-only Logistics Hermes plugin into the image --------------
# Placed outside /opt/data (the persistent volume) so the plugin code survives
# container recreation; the entrypoint copies it into HERMES_HOME/plugins at
# startup and enables it.
COPY --chmod=0755 deployments/hermes-dockhosting/plugins /opt/hermes-logistics

COPY --chmod=0755 deployments/hermes-dockhosting/dockhosting-entrypoint.sh /usr/local/bin/dockhosting-entrypoint.sh

ENV API_SERVER_ENABLED=true \
    API_SERVER_HOST=0.0.0.0

EXPOSE 8642

# Keep the upstream image's root entry semantics so s6-overlay can initialize
# the persistent volume and then drop Hermes services to the unprivileged user.
ENTRYPOINT ["/usr/local/bin/dockhosting-entrypoint.sh"]
CMD ["gateway", "run"]

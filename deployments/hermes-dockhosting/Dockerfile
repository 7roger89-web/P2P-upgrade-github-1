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

# Hermes Logistics read-only integration (HERMES_LOGISTICS_READONLY_001).
# Installed as a bundled plugin directory (the same surface as other bundled
# backend plugins), so it loads deterministically from the image and does not
# depend on /opt/data config state (local persistence across DockHosting
# redeploy is currently unreliable). The tools stay hidden from the model until
# LOGISTICS_MONGO_URI_READONLY and LOGISTICS_MONGO_DB_NAME are provided
# (check_fn gates schema exposure), and the connector exposes find/find_one
# only, over a collection allowlist. See README-logistics.md.
COPY --chmod=a+rX,go-w deployments/hermes-dockhosting/plugins/logistics/ /opt/hermes/plugins/logistics/

# pymongo is the MongoDB client for the Logistics plugin and is not part of the
# upstream hermes-agent dependency set. Exact pin, installed into the sealed
# image venv at build time so the Free-tier runtime never needs PyPI access.
ARG PYMONGO_VERSION=4.18.0
RUN uv pip install --python /opt/hermes/.venv/bin/python "pymongo==${PYMONGO_VERSION}"

COPY --chmod=0755 deployments/hermes-dockhosting/dockhosting-entrypoint.sh /usr/local/bin/dockhosting-entrypoint.sh

ENV API_SERVER_ENABLED=true \
    API_SERVER_HOST=0.0.0.0

EXPOSE 8642

# Keep the upstream image's root entry semantics so s6-overlay can initialize
# the persistent volume and then drop Hermes services to the unprivileged user.
ENTRYPOINT ["/usr/local/bin/dockhosting-entrypoint.sh"]
CMD ["gateway", "run"]

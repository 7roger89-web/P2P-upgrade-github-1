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

COPY --chmod=0755 deployments/hermes-dockhosting/dockhosting-entrypoint.sh /usr/local/bin/dockhosting-entrypoint.sh

ENV API_SERVER_ENABLED=true \
    API_SERVER_HOST=0.0.0.0

EXPOSE 8642

# Keep the upstream image's root entry semantics so s6-overlay can initialize
# the persistent volume and then drop Hermes services to the unprivileged user.
ENTRYPOINT ["/usr/local/bin/dockhosting-entrypoint.sh"]
CMD ["gateway", "run"]

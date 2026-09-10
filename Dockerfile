FROM nousresearch/hermes-agent:latest

USER root

ARG HERMES_PATCHES_VERSION=1.6.1

RUN set -eux; \
    uvx --from "hermes-patches==${HERMES_PATCHES_VERSION}" hermes-patches \
      --target /opt/hermes \
      --only footer table db nostream clean-think smart-split terminal-cwd state-guard; \
    uvx --from "hermes-patches==${HERMES_PATCHES_VERSION}" hermes-patches \
      --target /opt/hermes --status --json > /tmp/hermes-patches-status.json; \
    python3 -c 'import json; d=json.load(open("/tmp/hermes-patches-status.json")); req={"footer","table","db","nostream","clean-think","smart-split","terminal-cwd","state-guard"}; missing=[x for x in sorted(req) if not d["patches"].get(x,{}).get("applied")]; assert not missing, f"hermes-patches missing after build: {missing}"'; \
    # hermes-patches replaces Python files via NamedTemporaryFile + os.replace.
    # Those temp files default to mode 0600, which makes patched modules unreadable
    # by the runtime hermes user. Restore the upstream image invariant: source files
    # must be readable/traversable by the non-root hermes service account.
    find /opt/hermes -type f ! -perm -004 -exec chmod a+r,go-w {} +; \
    rm -f /tmp/hermes-patches-status.json

# Hermes Logistics read-only integration. DockHosting currently builds this
# repository-root Dockerfile, so the runtime image must include the plugin here
# as well as in deployments/hermes-dockhosting/Dockerfile.
COPY --chmod=a+rX,go-w deployments/hermes-dockhosting/plugins/logistics/ /opt/hermes/plugins/logistics/

# Runtime dependency used by the Logistics read-only MongoDB connector.
# DockHosting's build resolver did not expose the just-released 4.18.0; pin the
# older stable 4.17.0 release so the build can resolve reproducibly.
ARG PYMONGO_VERSION=4.17.0
RUN uv pip install --python /opt/hermes/.venv/bin/python "pymongo==${PYMONGO_VERSION}"

COPY --chmod=0755 deployments/hermes-dockhosting/dockhosting-entrypoint.sh /usr/local/bin/dockhosting-entrypoint.sh

ENV API_SERVER_ENABLED=true \
    API_SERVER_HOST=0.0.0.0

EXPOSE 8642

ENTRYPOINT ["/usr/local/bin/dockhosting-entrypoint.sh"]
CMD ["gateway", "run"]

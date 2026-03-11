# Source home-manager session variables if available
if [[ -f "/etc/profiles/per-user/simon/etc/profile.d/hm-session-vars.sh" ]]; then
  . "/etc/profiles/per-user/simon/etc/profile.d/hm-session-vars.sh"
fi

typeset -U path
path+=$HOME/.local/bin
path+=$HOME/.krew/bin

export WORDCHARS="*?[]~=&;!#$%^(){}"
export MINIKUBE_WANTUPDATENOTIFICATION=false
# see https://github.com/romkatv/powerlevel10k/issues/57
export GITSTATUS_NUM_THREADS=4
export GREP_OPTIONS="--color=always"

export PYTHONBREAKPOINT=pdbp.set_trace
export PYTHONDONTWRITEBYTECODE=1

export FZF_DEFAULT_COMMAND="rg --files --hidden --follow -g '!.config' -g '!.local' -g '!.mypy_cache' -g '!.git' -g '!node_modules' -g '!.venv' -g '!.cache' --sort path"
export FZF_DEFAULT_OPTS="--height 100% +i --bind ctrl-d:page-down,ctrl-u:page-up --exact"
export FZF_CTRL_R_OPTS="--with-nth 2.."

export _ZO_EXCLUDE_DIRS=".cache/*:.git/*:.venv/*:node_modules/*:.mypy_cache/*"
export _ZO_FZF_OPTS="--exact --no-sort --bind=ctrl-z:ignore,btab:up,tab:down --cycle --keep-right --border=sharp --height=100% --info=inline --layout=reverse --tabstop=1 --select-1 --preview='command -p ls -Cp --color=always --group-directories-first {2..}' --preview-window=down,30%,sharp"
export _ZO_ECHO=0  # Suppress zoxide output: detected a possible configuration issue

export SCHEMA_REGISTRY_URL=http://schema-registry-cp-schema-registry.kafka.svc.cluster.local:8081
export KAFKA_BROKERS=kafka-cp-kafka-headless.kafka.svc.cluster.local:9092
export KAFKA_BOOTSTRAP_SERVERS=kafka-cp-kafka-headless.kafka.svc.cluster.local:9092

# only works if a profile is explicitly added when running skaffold run
# e.g. skaffold run -p dev
export SKAFFOLD_KUBE_CONTEXT=minikube

# set age encryption environment variable used by sops for encrypting secrets
if [ -f "$HOME/.config/sops/age/keys.txt" ] && command -v age-keygen >/dev/null; then
  export SOPS_AGE_RECIPIENTS="$(age-keygen -y $HOME/.config/sops/age/keys.txt)"
fi

# secrets - only load if files exist
SECRETS_DIR="${SECRETS_DIR:-$HOME/.config/sops-nix/secrets}"
if [[ -f "$SECRETS_DIR/codestral_api_key" ]]; then
  export CODESTRAL_API_KEY=$(cat "$SECRETS_DIR/codestral_api_key")
fi
if [[ -f "$SECRETS_DIR/mistral_api_key" ]]; then
  export MISTRAL_API_KEY=$(cat "$SECRETS_DIR/mistral_api_key")
fi
if [[ -f "$SECRETS_DIR/gemini_api_key" ]]; then
  export GEMINI_API_KEY=$(cat "$SECRETS_DIR/gemini_api_key")
fi
if [[ -f "$SECRETS_DIR/anthropic_api_key" ]]; then
  export ANTHROPIC_API_KEY=$(cat "$SECRETS_DIR/anthropic_api_key")
fi
if [[ -f "$SECRETS_DIR/google_search_api_key" ]]; then
  export GOOGLE_SEARCH_API_KEY=$(cat "$SECRETS_DIR/google_search_api_key")
fi
export GOOGLE_SEARCH_ENGINE_ID=d7c60b4fb9dc846b5
if [[ -f "$SECRETS_DIR/openrouter_api_key" ]]; then
  export OPENROUTER_API_KEY=$(cat "$SECRETS_DIR/openrouter_api_key")
fi

if [[ "$CURSOR_AGENT" == "1" ]]; then
  return
fi

if [[ -r "$HOME/.cache/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "$HOME/.cache/p10k-instant-prompt-${(%):-%n}.zsh"
fi

typeset -U path cdpath fpath manpath

# Add common zsh completion directories to fpath
fpath+=($HOME/.local/share/zsh/site-functions)
fpath+=(/usr/local/share/zsh/site-functions)
fpath+=(/usr/share/zsh/site-functions)

# Set HELPDIR dynamically if zsh help is available
if [[ -d "/usr/share/zsh/$ZSH_VERSION/help" ]]; then
  HELPDIR="/usr/share/zsh/$ZSH_VERSION/help"
fi

# Load antidote plugin manager
# Find antidote.zsh in common locations
if [[ -n "${ANTIDOTE_HOME:-}" ]] && [[ -f "$ANTIDOTE_HOME/antidote.zsh" ]]; then
  # Use ANTIDOTE_HOME if set
  source "$ANTIDOTE_HOME/antidote.zsh"
elif command -v antidote >/dev/null; then
  # Try to find antidote via command (installed via home-manager)
  ANTIDOTE_SCRIPT="$(command -v antidote)"
  if [[ -f "$ANTIDOTE_SCRIPT" ]]; then
    source "$ANTIDOTE_SCRIPT"
  fi
fi

# Configure antidote if it's loaded
if (( $+functions[antidote] )); then
  # Set up antidote bundle and static files
  zstyle ':antidote:bundle' file "${ZDOTDIR:-$HOME}/.zsh_plugins"
  zstyle ':antidote:static' file "${ZDOTDIR:-$HOME}/.zsh_plugins.zsh"
  
  # Load plugins
  antidote load
fi

autoload -Uz compinit
for dump in $HOME/.zcompdump(N.mh+24); do
  compinit
done
compinit -C

# Allow kubecolor to reuse kubectl's completions
compdef kubecolor=kubectl

# Load zsh-autosuggestions if available
# Try multiple common locations
if [[ -n "${ZSH_AUTOSUGGESTIONS_PATH:-}" ]] && [[ -f "$ZSH_AUTOSUGGESTIONS_PATH/zsh-autosuggestions.zsh" ]]; then
  # Use ZSH_AUTOSUGGESTIONS_PATH if set
  source "$ZSH_AUTOSUGGESTIONS_PATH/zsh-autosuggestions.zsh"
else
  # Search in fpath for zsh-autosuggestions
  for dir in $fpath; do
    if [[ -f "$dir/zsh-autosuggestions.zsh" ]]; then
      source "$dir/zsh-autosuggestions.zsh"
      break
    fi
  done
fi

# Configure zsh-autosuggestions if loaded
if (( $+functions[_zsh_autosuggest_start] )); then
  ZSH_AUTOSUGGEST_STRATEGY=(history)
fi


# History options should be set in .zshrc and after oh-my-zsh sourcing.
# See https://github.com/nix-community/home-manager/issues/177.
HISTSIZE="1000000"
SAVEHIST="1000000"
HISTORY_IGNORE='(rm *|pkill *|cp *|ls *|cd *|kill *|echo *|less *|make *|just *|which *)'
HISTFILE="$HOME/.zsh_history"
mkdir -p "$(dirname "$HISTFILE")"

setopt HIST_FCNTL_LOCK
unsetopt APPEND_HISTORY
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
unsetopt HIST_SAVE_NO_DUPS
unsetopt HIST_FIND_NO_DUPS
setopt HIST_IGNORE_SPACE
unsetopt HIST_EXPIRE_DUPS_FIRST
setopt SHARE_HISTORY
setopt EXTENDED_HISTORY
setopt autocd

# avoid the need to manually reset the terminal
ttyctl -f

# Remove superfluous blanks from each command line being added to the history list.
setopt HIST_REDUCE_BLANKS
HIST_STAMPS="yyyy-mm-dd"

zstyle ":completion:*" rehash true
zstyle ":completion:*" completer _complete
zstyle ":completion:*" matcher-list "" "m:{[:lower:][:upper:]}={[:upper:][:lower:]}" "+l:|=* r:|=*"
zstyle ":completion:*" special-dirs true

# enable builtin calculator
autoload -U zcalc

# enable smart file renamer
autoload -Uz zmv

alias -g G=" | grep"
alias -g R=" | rg"

# zsh-autosuggestions
# use CTRL+arrow keys to jump words
bindkey "^[[1;5C" forward-word
bindkey "^[[1;5D" backward-word
bindkey "^ " autosuggest-accept
bindkey "^[^M" autosuggest-execute

# zoxide
zle -N cdi
bindkey '^G' cdi

# fuzzy find git branches
fbr() {
  local branches branch
  branches=$(git branch)
  branch=$(echo "$branches" | fzf-tmux -d '15%')
  git checkout $(echo "$branch" | sed "s/.* //")
}
zle     -N   fbr
bindkey '^B' fbr

# change k8s context
bindkey -s '^o' 'kubectx\n'

# k8s
function kexec() {
    pod=$1; shift; kubectl exec -it $pod -- $@;
}

# kafka
function kafka-purge-topic() {
    set -x
    topic=$1
    kafka-topics.sh --bootstrap-server $KAFKA_BROKERS --delete --topic $topic 2>/dev/null
    kafka-topics.sh --bootstrap-server $KAFKA_BROKERS --create --topic $topic 2>/dev/null
}
function kafka-delete-topic() {
    set -x
    topic=$1
    kafka-topics.sh --bootstrap-server $KAFKA_BROKERS --delete --topic $topic 2>/dev/null
}
function kafka-describe-topic() {
    set -x
    topic=$1
    kafka-topics.sh --bootstrap-server $KAFKA_BROKERS --describe --topic $topic 2>/dev/null
}

# python
pyclean () {
    find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
}

# git
# Search all local Git branches for a keyword
ggk() {
  if [[ -z "$1" ]]; then
    echo "Usage: ggk <keyword>"
    return 1
  fi

  local keyword=$1
  echo "🔍 Searching for '$keyword' in all local branches..."

  # Collect all local branch names
  local branches
  branches=($(git for-each-ref --format='%(refname:short)' refs/heads/ 2>/dev/null))

  if [[ ${#branches[@]} -eq 0 ]]; then
    echo "No local branches found."
    return 1
  fi

  # Run git grep across all branches
  git grep --color=always "$keyword" "${branches[@]}" || {
    echo "No matches found."
    return 1
  }
}

vpa-set-max-cpu() {
  if [[ $# -lt 2 ]]; then
    echo "Usage: vpa-set-max-cpu <vpa-name> <cpu-limit>"
    echo "Example: vpa-set-max-cpu apptus-projection-service 100m"
    return 1
  fi

  local vpa_name=$1
  local cpu_limit=$2

  kubectl patch vpa "$vpa_name" --type='json' -p="[{\"op\": \"replace\", \"path\":
\"/spec/resourcePolicy/containerPolicies/0/maxAllowed/cpu\", \"value\": \"$cpu_limit\"}]"
}

nixify() {
  # Default Python package
  nix_python="pkgs.python312"

  # Check for .python-version and convert version string
  if [[ -f .python-version ]]; then
    pyver=$(<.python-version)
    # Remove dots to get e.g. 3.12 -> 312
    pyver_attr="${pyver//./}"
    if [[ "$pyver_attr" =~ ^[0-9]{3}$ ]]; then
      nix_python="pkgs.python$pyver_attr"
    else
      echo "Warning: could not parse Python version '$pyver'. Falling back to $nix_python"
    fi
  fi

  # 1. Create shell.nix
  cat > shell.nix <<EOF
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    $nix_python
  ];

  env = {
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc
    ];
  };
}
EOF

  # 2. Append to .envrc if not already present
  grep -qxF 'source_env_if_exists ".envrc.local"' .envrc 2>/dev/null || echo 'source_env_if_exists ".envrc.local"' >> .envrc

  # 3. Create .envrc.local
  cat > .envrc.local <<EOF
use nix
if [ -d .venv ]; then
  source .venv/bin/activate
fi
EOF

  # 4. Append to .gitignore if not already present
  grep -qxF '.direnv' .gitignore 2>/dev/null || echo '.direnv' >> .gitignore
  grep -qxF '.envrc.local' .gitignore 2>/dev/null || echo '.envrc.local' >> .gitignore
  grep -qxF 'shell.nix' .gitignore 2>/dev/null || echo 'shell.nix' >> .gitignore

  echo "Nix environment setup complete using $nix_python!"
}

if command -v fzf-share >/dev/null; then
  source "$(fzf-share)/key-bindings.zsh"
  source "$(fzf-share)/completion.zsh"
fi
if command -v kubectl >/dev/null; then
  source <(kubectl completion zsh)
fi
if command -v gh >/dev/null; then
  eval "$(gh completion -s zsh)"
fi
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

function in_nix_shell() {
  if [ ! -z ${IN_NIX_SHELL+x} ];
    then echo "%F{blue} %f";
  fi
}

POWERLEVEL9K_CUSTOM_NIX_SHELL="in_nix_shell"
POWERLEVEL9K_VIRTUALENV_LEFT_DELIMITER="("
POWERLEVEL9K_VIRTUALENV_RIGHT_DELIMITER=")"
POWERLEVEL9K_VIRTUALENV_SHOW_PYTHON_VERSION=true
POWERLEVEL9K_VIRTUALENV_FOREGROUND=7
POWERLEVEL9K_LEFT_PROMPT_ELEMENTS=(dir vcs newline virtualenv custom_nix_shell prompt_char)
POWERLEVEL9K_INSTANT_PROMPT=quiet

alias -- bc=zcalc
alias -- cal='cal -w -3'
alias -- edit_config='sudo -E nvim /etc/nixos/configuration.nix'
alias -- edit_flake='sudo -E nvim /etc/nixos/flake.nix'
alias -- edit_home='nvim /etc/nixos/home.nix'
alias -- ga='git add'
alias -- gb='git brv'
alias -- gba='git branch -vva'
alias -- gc='git commit'
alias -- 'gc!'='git commit -v --amend'
alias -- gcd='cd $(git root)'
alias -- gcm='git checkout master'
alias -- gco='git checkout'
alias -- gd='git diff'
alias -- gdc='git diff --cached'
alias -- gdn='git diff --no-ext-diff'
alias -- gf='git fetch'
alias -- ghb='gh repo view -w'
alias -- ghpr='gh pr create -f -d'
alias -- gl='git pull'
alias -- glog='git log --abbrev-commit --oneline --color=always '\''--pretty=format:%Cred%h%Creset - %s %Cred%d%Creset %Cgreen(%cd) %C(bold blue)<%an>%Creset '\'' --date=short'
alias -- glogg='git log --graph --pretty=format:'\''%C(124)%ad %C(24)%h %C(34)%an %C(252)%s%C(178)%d'\'' --date=short'
alias -- gp='git push'
alias -- grhh='git reset --hard'
alias -- gs='git status -s'
alias -- gss='git status'
alias -- gst='git stash'
alias -- gstp='git stash pop'
alias -- k=kubecolor
alias -- kl='kubecolor logs --tail=100 -f'
alias -- ls='ls -lsh --color=auto'
alias -- open=xdg-open
alias -- rebuild='sudo nixos-rebuild switch'
alias -- vim=nvim
alias -- zcalc='zcalc -f'

# Initialize zoxide if available
if command -v zoxide >/dev/null; then
  eval "$(zoxide init zsh --cmd cd)"
fi

# Initialize direnv if available
if command -v direnv >/dev/null; then
  eval "$(direnv hook zsh)"
fi

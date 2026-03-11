# Add this to your home-manager configuration
# This replaces the old programs.zsh configuration

{
  # Install required packages
  home.packages = with pkgs; [
    antidote
    zsh-autosuggestions
    zoxide
    direnv
    fzf
    age  # if using sops
    kubectl
    kubecolor
    kubectx
    gh  # GitHub CLI
  ];

  # Symlink zsh configuration files from dotfiles
  home.file.".zshrc" = {
    source = config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/.zshrc";
  };
  
  home.file.".zshenv" = {
    source = config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/.zshenv";
  };
  
  home.file.".zsh_plugins" = {
    source = config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/.zsh_plugins";
  };

  # You can now remove or disable the old programs.zsh configuration:
  # programs.zsh.enable = false;
}

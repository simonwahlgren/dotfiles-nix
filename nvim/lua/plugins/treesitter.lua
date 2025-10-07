return {
  "nvim-treesitter/nvim-treesitter",
  run = ":TSUpdate",
  config = function()
    require("nvim-treesitter.configs").setup({
      ensure_installed = {
        "bash",
        "dockerfile",
        "json",
        "lua",
        "markdown",
        "markdown_inline",
        "nix",
        "python",
        "sway",
        "terraform",
        "toml",
        "typescript",
        "yaml",
      },
      highlight = {
        enable = true,
        additional_vim_regex_highlighting = false,
      },
      -- experiment!
      -- disabled since it messes up markdown bullet indentation
      indent = {
        enable = true,
        disable= { "markdown" },
      },
      incremental_selection = {
        enable = true,
        keymaps = {
          init_selection = false,
          scope_incremental = "<tab>",
          node_incremental = "v",
          node_decremental = "V",
        },
      },
    })
  end,
}

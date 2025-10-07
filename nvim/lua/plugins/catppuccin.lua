return {
  {
    "catppuccin/nvim",
    enable=true,
    name = "catppuccin",
    priority = 1000, -- Ensure the colorscheme loads before other plugins
    config = function()
      require("catppuccin").setup({
        flavour = "mocha", -- You can change this to "latte", "frappe", or "macchiato"
        transparent_background = false,
        term_colors = true,
        no_italic = false,
        no_bold = false,
        no_underline = false,
        integrations = {
          cmp = true,
          gitsigns = true;
          treesitter = true,
          telescope = true,
          lsp_trouble = true,
          native_lsp = {
            enabled = true,
          },
        },
        color_overrides = {
          mocha = {
            base = "#111111",
            mantle = "#111111",
            crust = "#111111",
          },
        },
      })
      vim.cmd.colorscheme("catppuccin")
    end,
  },
}

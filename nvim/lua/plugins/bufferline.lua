return {
  {
    "akinsho/bufferline.nvim",
    dependencies = {
      "tiagovla/scope.nvim",
      "folke/snacks.nvim"
    },
    opts = {
      options = {
        separator_style = "slant",
        show_buffer_icons = false,
        show_buffer_close_icons = false,
        truncate_names = false,
        always_show_bufferline = true,
        diagnostics = "nvim_lsp",
        close_command = function(n) Snacks.bufdelete(n) end,
        right_mouse_command = function(n) Snacks.bufdelete(n) end,
      },
    },
    config = function(_, opts)
      local bufferline = require("bufferline")
      opts.options.style_preset = bufferline.style_preset.no_italic
      require("bufferline").setup(opts)
      vim.keymap.set("n", "<C-n>", ":BufferLineCycleNext<CR>", { noremap = true, silent = true })
      vim.keymap.set("n", "<C-p>", ":BufferLineCyclePrev<CR>", { noremap = true, silent = true })
    end,
  }
}

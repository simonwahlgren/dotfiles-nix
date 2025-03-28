return {
  "akinsho/bufferline.nvim",
  dependencies = { "tiagovla/scope.nvim" },
  opts = {
    options = {
      separator_style = "slant",
      show_buffer_icons = false,
      show_buffer_close_icons = false,
      truncate_names = false,
    },
  },
  config = function(_, opts)
    require("bufferline").setup(opts)
    vim.keymap.set("n", "<C-n>", ":BufferLineCycleNext<CR>", { noremap = true, silent = true })
    vim.keymap.set("n", "<C-p>", ":BufferLineCyclePrev<CR>", { noremap = true, silent = true })
  end,
}

return {
  "stevearc/oil.nvim",
  dependencies = { { "echasnovski/mini.icons", opts = {} } },
  lazy=false,
  keys = {
    { "<leader>e", "<cmd>Oil<CR>", desc = "Open Oil file explorer" },
  },
  opts = {
    default_file_explorer = true,
    view_options = {
      show_hidden = true,
    },
  },
}

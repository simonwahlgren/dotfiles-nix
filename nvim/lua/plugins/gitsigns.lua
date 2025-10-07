return {
  "lewis6991/gitsigns.nvim",
  dependencies = {
    "nvim-lua/plenary.nvim",
  },
  -- lazy loading not working correctly, need to press keys twice first time
  -- keys = {
  --   {
  --     "<leader>gb",
  --     "<cmd>Gitsigns blame<CR>",
  --     desc = "Git blame current buffer",
  --   },
  --   {
  --     "<leader>gB",
  --     "<cmd>Gitsigns blame_line<CR>",
  --     desc = "Git blame current line",
  --   },
  -- },
  opts = {
    signs = {
      add = { text = "+" },
      change = { text = "~" },
      delete = { text = "-" },
      topdelete = { text = "-" },
      changedelete = { text = "~" },
      untracked = { text = "*" },
    },
  },
  config = function(_, opts)
    require("gitsigns").setup(opts)
    vim.keymap.set("n", "<leader>gb", ":Gitsigns blame<CR>", { noremap = true, silent = true })
    vim.keymap.set("n", "<leader>gB", ":Gitsigns blame_line<CR>", { noremap = true, silent = true })
  end,
}

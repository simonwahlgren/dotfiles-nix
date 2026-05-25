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
    word_diff = true,
    on_attach = function(bufnr)
      local gs = require("gitsigns")
      local map = function(mode, lhs, rhs, desc)
        vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, desc = desc })
      end
      map("n", "]c", function()
        if vim.wo.diff then
          vim.cmd.normal({ "]c", bang = true })
        else
          gs.nav_hunk("next")
        end
      end, "Next git hunk")
      map("n", "[c", function()
        if vim.wo.diff then
          vim.cmd.normal({ "[c", bang = true })
        else
          gs.nav_hunk("prev")
        end
      end, "Previous git hunk")
    end,
  },
  config = function(_, opts)
    require("gitsigns").setup(opts)
    vim.keymap.set("n", "<leader>gb", ":Gitsigns blame<CR>", { noremap = true, silent = true })
    vim.keymap.set("n", "<leader>gB", ":Gitsigns blame_line<CR>", { noremap = true, silent = true })
    vim.keymap.set("n", "<leader>gw", ":Gitsigns toggle_word_diff<CR>", { noremap = true, silent = true, desc = "Toggle gitsigns word diff" })
  end,
}

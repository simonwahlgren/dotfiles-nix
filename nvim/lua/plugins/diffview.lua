return {
  "sindrets/diffview.nvim",
  lazy = true,
  cmd = {
    "DiffviewOpen",
    "DiffviewClose",
    "DiffviewToggleFiles",
    "DiffviewFocusFiles",
    "DiffviewFileHistory",
  },
  keys = {
    {
      "<leader>gd",
      "<cmd>DiffviewOpen HEAD~1<CR>",
      desc = "Git diff HEAD~1",
    },
  },
  dependencies = { "nvim-lua/plenary.nvim" },
  config = function()
    require("diffview").setup({})
    vim.api.nvim_create_autocmd("FileType", {
      pattern = "DiffviewFiles",
      callback = function()
        vim.keymap.set("n", "<C-q>", ":tabclose<CR>", { buffer = true, silent = true })
      end,
    })
  end,
}

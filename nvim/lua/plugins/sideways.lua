return {
  "AndrewRadev/sideways.vim",
  config = function()
    vim.keymap.set("n", "<C-M-h>", "<Plug>SidewaysLeft", { remap = true, silent = true })
    vim.keymap.set("n", "<C-M-l>", "<Plug>SidewaysRight", { remap = true, silent = true })
  end,
}

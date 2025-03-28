return {
  "kana/vim-smartword",
  config = function()
    vim.keymap.set({ "n", "x" }, "w", "<Plug>(smartword-w)", { remap = true, silent = true })
    vim.keymap.set({ "n", "x" }, "b", "<Plug>(smartword-b)", { remap = true, silent = true })
    vim.keymap.set({ "n", "x" }, "e", "<Plug>(smartword-e)", { remap = true, silent = true })
    vim.keymap.set({ "n", "x" }, "ge", "<Plug>(smartword-ge)", { remap = true, silent = true })
  end,
}

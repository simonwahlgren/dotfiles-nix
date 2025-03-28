return {
  "svermeulen/vim-subversive",
  config = function()
    vim.keymap.set("n", "s", "<Plug>(SubversiveSubstitute)", { remap = true, silent = true })
    vim.keymap.set("n", "ss", "<Plug>(SubversiveSubstituteLine)", { remap = true, silent = true })
    vim.keymap.set("n", "S", "<Plug>(SubversiveSubstituteToEndOfLine)", { remap = true, silent = true })
  end,
}

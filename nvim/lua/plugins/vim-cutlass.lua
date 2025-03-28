return {
  "svermeulen/vim-cutlass",
   config = function()
    -- Normal mode: remap "m" to "d"
    vim.keymap.set("n", "m", "d", { noremap = true, silent = true })
    -- Visual mode: remap "m" to "d"
    vim.keymap.set("x", "m", "d", { noremap = true, silent = true })
    -- Normal mode: remap "mm" to "dd"
    vim.keymap.set("n", "mm", "dd", { noremap = true, silent = true })
    -- Normal mode: remap "M" to "D"
    vim.keymap.set("n", "M", "D", { noremap = true, silent = true })
  end,
}

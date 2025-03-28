vim.keymap.set('n', '<leader>BB', 'Obreakpoint()<esc>', { buffer = true, silent = true })
vim.keymap.set('n', '<leader>bb', 'obreakpoint()<esc>', { buffer = true, silent = true })
vim.keymap.set('n', '<leader>bf', ':/breakpoint()<cr>', { buffer = true, silent = true })
vim.keymap.set('n', '<leader>bd', ':g/breakpoint\\(\\)/d<cr>', { buffer = true, silent = true })

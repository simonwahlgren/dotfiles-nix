return {
  "dyng/ctrlsf.vim",
  config = function()
    vim.g.ctrlsf_ackprg       = "/run/current-system/sw/bin/rg"
    vim.g.ctrlsf_mapping      = { next = "n", prev = "N" }
    vim.g.ctrlsf_winsize      = "100%"
    vim.g.ctrlsf_search_mode  = "sync"

    vim.keymap.set("n", "<C-S>f", "<Plug>CtrlSFPrompt", { remap = true, silent = false })
    vim.keymap.set("n", "<C-S>w", "<Plug>CtrlSFCwordExec", { remap = true, silent = false })
    vim.keymap.set("v", "<C-S>v", "<Plug>CtrlSFVwordExec", { remap = true, silent = false })
  end,
}

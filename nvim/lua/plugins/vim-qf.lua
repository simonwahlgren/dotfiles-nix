return {
  "romainl/vim-qf",
  config = function()
    vim.keymap.set("n", "[q", "<Plug>(qf_qf_previous)", { noremap = true, silent = true })
    vim.keymap.set("n", "]q", "<Plug>(qf_qf_next)", { noremap = true, silent = true })
    vim.keymap.set("n", "[l", "<Plug>(qf_loc_previous)", { noremap = true, silent = true })
    vim.keymap.set("n", "]l", "<Plug>(qf_loc_next)", { noremap = true, silent = true })
    vim.keymap.set("n", "<F5>", "<Plug>(qf_qf_toggle)", { noremap = true, silent = true })
    vim.keymap.set("n", "<F6>", "<Plug>(qf_loc_toggle)", { noremap = true, silent = true })

    -- Ack.vim-inspired mappings available only in location/quickfix windows:
    --  s - open entry in a new horizontal window
    --  v - open entry in a new vertical window
    --  t - open entry in a new tab
    --  o - open entry and come back
    --  O - open entry and close the location/quickfix window
    --  p - open entry in a preview window
    vim.g.qf_mapping_ack_style = 1
  end,
}

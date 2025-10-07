return {
  "bcicen/vim-jfmt",
  lazy = true,
  ft = { "json" },
  init = function()
    vim.g.jfmt_on_save = 0
    vim.g.jfmt_jq_options = "--sort-keys"
  end,
}

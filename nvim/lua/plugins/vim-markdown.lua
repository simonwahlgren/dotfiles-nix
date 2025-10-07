return {
  "preservim/vim-markdown",
  config = function()
    vim.g.vim_markdown_new_list_item_indent = 2
    -- the extended gx mapping is no longer working on non-markdown links
    vim.g.vim_markdown_no_default_key_mappings = 1
  end,
}

return {
  "iamcco/markdown-preview.nvim",
  ft = { "markdown" },
  build = "cd app && npm install",
  config = function()
    -- Set this if you want to automatically start the preview
    vim.g.mkdp_auto_start = 0
    -- Optional settings
    vim.g.mkdp_auto_close = 1
    vim.g.mkdp_refresh_slow = 0
    vim.g.mkdp_command_for_global = 0
    vim.g.mkdp_open_to_the_world = 0
    vim.g.mkdp_browser = ""
    vim.g.mkdp_theme = "dark"
  end
}

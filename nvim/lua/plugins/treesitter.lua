return {
  "nvim-treesitter/nvim-treesitter",
  branch = "main",
  lazy = false,
  build = ":TSUpdate",
  init = function()
    vim.api.nvim_create_autocmd("FileType", {
      callback = function()
        pcall(vim.treesitter.start)
        if vim.bo.filetype ~= "markdown" then
          vim.bo.indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
        end
      end,
    })

    local ensure_installed = {
      "bash",
      "dockerfile",
      "json",
      "lua",
      "markdown",
      "markdown_inline",
      "nix",
      "python",
      "sway",
      "terraform",
      "toml",
      "typescript",
      "yaml",
    }
    local already_installed = require("nvim-treesitter.config").get_installed()
    local to_install = vim.iter(ensure_installed)
      :filter(function(parser)
        return not vim.tbl_contains(already_installed, parser)
      end)
      :totable()
    if #to_install > 0 then
      require("nvim-treesitter").install(to_install)
    end
  end,
}

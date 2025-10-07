return {
  "stevearc/resession.nvim",
  config = function()
    require("resession").setup({})

    local function find_git_root()
      local git_root = vim.fn.system("git rev-parse --show-toplevel 2>/dev/null")
      git_root = vim.fn.trim(git_root)
      if git_root == "" then
        return nil
      else
        return git_root
      end
    end

    vim.api.nvim_create_autocmd("VimEnter", {
      callback = function()
        if vim.fn.argc(-1) == 0 and not vim.g.using_stdin then
          local root = find_git_root()
          if root then
            require("resession").load(root, { silence_errors = true })
            -- Force reload the buffer to fix highlight/colorscheme issues in the first buffer
            vim.schedule(function()
              vim.cmd("silent! edit")
            end)
          end
        end
      end,
      nested = true,
      desc = "Restore session for Git root if available and no arguments provided",
    })

    vim.api.nvim_create_autocmd("VimLeavePre", {
      callback = function()
        local root = find_git_root()
        if root then
          require("resession").save(root, { notify = false })
        end
      end,
      desc = "Save session for Git root on exit, if available",
    })

    vim.api.nvim_create_autocmd("StdinReadPre", {
      callback = function()
        vim.g.using_stdin = true
      end,
      desc = "Mark that Neovim is reading from stdin",
    })
  end,
}

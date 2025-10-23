return {
  "neovim/nvim-lspconfig",
  event = { "BufReadPre", "BufNewFile" },
  dependencies = {
    "hrsh7th/cmp-nvim-lsp",
  },
  config = function()
    -- Add cmp_nvim_lsp capabilities settings to lspconfig
    -- This should be executed before you configure any language server
    local lspconfig_defaults = require('lspconfig').util.default_config
    local capabilities = require('cmp_nvim_lsp').default_capabilities()

    lspconfig_defaults.capabilities = vim.tbl_deep_extend(
      'force',
      lspconfig_defaults.capabilities,
      capabilities
    )

    local keymap = vim.keymap
    vim.api.nvim_create_autocmd("LspAttach", {
      group = vim.api.nvim_create_augroup("UserLspConfig", {}),
      callback = function(ev)
        local opts = { buffer = ev.buf, silent = true }

        -- Builtin keymaps:
        -- [d: Previous diagnostic
        -- ]d: Next diagnostic
        -- <C-w>d or <C-w><C-d>: Open diagnostic float
        -- gri: Go to implementation
        -- grr: Show references
        -- grn: Rename symbol
        -- CTRL+S: Signature help
        -- gra: Code actions
        -- K: Show hover documentation
        keymap.set('n', 'gd', vim.lsp.buf.definition, opts)
        keymap.set('n', '<leader>n', function()
          vim.lsp.buf.format({ async = false })
          vim.lsp.buf.code_action({
            context = { only = { 'source.organizeImports' }, diagnostics = {} },
            apply = true,
          })
          -- will also remove unreferenced imports
          -- vim.lsp.buf.code_action({
          --   context = {
          --     only = {
          --       "source.fixAll.ruff"
          --     },
          --   },
          --   apply = true,
          -- })
        end)
        keymap.set("n", "grR", ":LspRestart<CR>", opts)
      end,
    })

    -- defer hover in favor of Pyright
    -- https://docs.astral.sh/ruff/editors/setup/#neovim
    vim.api.nvim_create_autocmd("LspAttach", {
      group = vim.api.nvim_create_augroup('lsp_attach_disable_ruff_hover', { clear = true }),
      callback = function(args)
        local client = vim.lsp.get_client_by_id(args.data.client_id)
        if client == nil then
          return
        end
        if client.name == 'ruff' then
          -- Disable hover in favor of Pyright
          client.server_capabilities.hoverProvider = false
        end
      end,
      desc = 'LSP: Disable hover capability from Ruff',
    })

    vim.lsp.config('pyright', {
      capabilities = capabilities,
      settings = {
        pyright = {
          -- Using Ruff's import organizer
          disableOrganizeImports = true,
        },
        python = {
          analysis = {
            -- Ignore all files for analysis to exclusively use Ruff for linting
            ignore = { '*' },
            diagnosticMode = "workspace",
            autoImportCompletions = true,
            typeCheckingMode = "standard",
            exclude = {
              "**/.venv",
              "**/.mypy_cache",
              "**/__pycache__",
              "**/build",
              "**/dist",
            },
          },
        },
      },
    })
    vim.lsp.enable('pyright')

    -- Ruff: keep it for diagnostics/code actions, not completion/hover
    vim.lsp.config('ruff', {
      capabilities = capabilities,
      on_attach = function(client, _)
        client.server_capabilities.hoverProvider = false
        client.server_capabilities.completionProvider = nil
      end,
    })
    vim.lsp.enable('ruff')

    vim.lsp.enable('lua_ls')
    vim.lsp.enable('terraformls')
    vim.lsp.enable('typos_lsp')
    vim.lsp.enable('marksman')
  end,
}

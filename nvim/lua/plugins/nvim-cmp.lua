return {
  "hrsh7th/nvim-cmp",
  version = false,
  enabled = true,
  dependencies = {
    "hrsh7th/cmp-nvim-lsp",
    "hrsh7th/cmp-buffer",
    "hrsh7th/cmp-path",
    "hrsh7th/cmp-cmdline",
    -- "milanglacier/minuet-ai.nvim"
  },
  opts = function()
    local cmp = require("cmp")
    local defaults = require("cmp.config.default")()
    -- local minuet = require("minuet")
    local auto_select = false

    return {
      auto_brackets = {}, -- configure any filetype to auto add brackets
      completion = {
        completeopt = "menu,menuone,noinsert" .. (auto_select and "" or ",noselect"),
        keyword_length = 1,
      },
      preselect = auto_select and cmp.PreselectMode.Item or cmp.PreselectMode.None,
      mapping = cmp.mapping.preset.insert({
        ["<Tab>"] = function(fallback)
          if cmp.visible() then
            cmp.select_next_item({ behavior = cmp.SelectBehavior.Insert })
          else
            fallback()
          end
        end,
        ["<S-Tab>"] = function(fallback)
          if cmp.visible() then
            cmp.select_prev_item({ behavior = cmp.SelectBehavior.Insert })
          else
            fallback()
          end
        end,
        ["<C-Space>"] = cmp.mapping.complete(),
        ["<CR>"] = cmp.mapping.confirm({ select = auto_select }),
        -- ["<C-y>"] = minuet.make_cmp_map(),
      }),
      sources = cmp.config.sources({
        { name = "nvim_lsp" },
        { name = "path" },
        -- { name = "minuet" },
      }, {
        { name = "buffer" },
      }),
      formatting = {
        format = function(entry, item)
          local widths = {
            abbr = vim.g.cmp_widths and vim.g.cmp_widths.abbr or 40,
            menu = vim.g.cmp_widths and vim.g.cmp_widths.menu or 30,
          }
          for key, width in pairs(widths) do
            if item[key] and vim.fn.strdisplaywidth(item[key]) > width then
              item[key] = vim.fn.strcharpart(item[key], 0, width - 1) .. "…"
            end
          end
          return item
        end,
      },
      experimental = {
        ghost_text = vim.g.ai_cmp and {
          hl_group = "CmpGhostText",
        } or false,
      },
      sorting = defaults.sorting,
      performance = {
        -- LLMs are slower than LSP; increase fetch timeout so items don’t get dropped
        fetching_timeout = 2000,
      },
    }
  end,
  config = function(_, opts)
    local cmp = require("cmp")
    cmp.setup(opts)

    -- Setup cmdline completion for search mode ("/")
    cmp.setup.cmdline({"/", "?"}, {
      completion = { completeopt = 'menu,menuone,noselect' },
      mapping = cmp.mapping.preset.cmdline(),
      sources = {
        { name = "buffer" },
      },
    })

    -- Setup cmdline completion for command mode (":")
    cmp.setup.cmdline(":", {
      completion = { completeopt = 'menu,menuone,noselect' },
      mapping = cmp.mapping.preset.cmdline(),
      sources = cmp.config.sources({
        { name = "path" },
      }, {
        { name = "cmdline" },
      }),
    })
  end,
}

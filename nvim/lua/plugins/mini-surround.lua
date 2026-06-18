-- mini.surround
-- Add, delete, replace surroundings (vim-surround style)
--
-- Cheatsheet:
--   ys<motion><char>   → Add surrounding
--   ds<char>           → Delete surrounding
--   cs<old><new>       → Replace surrounding
--   gs                 → Highlight surrounding
--   suffixes:
--     l → target last   (default: "l")
--     n → target next   (default: "n")
--
-- Docs: https://github.com/echasnovski/mini.surround
return {
  "echasnovski/mini.surround",
  version = false,
  event = "VeryLazy",
  opts = {
    mappings = {
      add = "ys",          -- Add surrounding
      delete = "ds",       -- Delete surrounding
      replace = "cs",      -- Replace surrounding
      find = "",           -- (disabled, default: "sf")
      find_left = "",      -- (disabled, default: "sF")
      highlight = "gs",    -- Highlight surrounding
      update_n_lines = "", -- (disabled, default: "sn")
      suffix_last = "l",   -- Suffix to target last
      suffix_next = "n",   -- Suffix to target next
    },
  },
  config = function(_, opts)
    require("mini.surround").setup(opts)
    -- Move visual-mode "add surrounding" off `ys` so it doesn't make visual `y` wait on timeoutlen.
    vim.keymap.del("x", "ys")
    vim.keymap.set("x", "S", [[:<C-u>lua MiniSurround.add('visual')<CR>]], { silent = true })
  end,
}

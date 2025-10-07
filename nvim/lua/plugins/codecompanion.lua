--[[
CodeCompanion.nvim — Cheatsheet (defaults)

Core Commands
  :CodeCompanion            → Inline assistant on current buffer/selection
  :CodeCompanionChat        → Open a chat buffer (toggle with :CodeCompanionChat Toggle)
  :CodeCompanionCmd         → Generate an Ex command (command-line mode)
  :CodeCompanionActions     → Action Palette (also :Telescope codecompanion if enabled)
  :checkhealth codecompanion → Diagnostics/log path

Chat Buffer (normal-mode) keymaps
  ?        Show all available CodeCompanion keymaps (in-buffer help)
  <C-s>    to send a message to the LLM
  <C-c>    to close the chat buffer
  q        Cancel/stop the current request
  ga       Select adapter (and model/command if applicable)
  gd       Open Debug window (inspect/adjust messages/settings)
  gD       Super Diff (review & accept/reject file edits)
  gc       Insert a fenced code block
  gf       Fold/unfold code blocks in chat
  gp       Pin a context item (on a line inside the “> Context” block)
  gw       Watch current buffer as context
  gta      Toggle Auto Tool mode
  gs       Toggle system prompt visibility
  gS       Show Copilot usage stats (Copilot adapter only)
  gx       Clear chat buffer
  gy       Yank last code block in chat
  gR       Go to file under cursor (reuse window/tab if open)
  <C-n>    to move to the previous header
  <C-p>    to move to the next header
  n        to move to the previous chat
  N        to move to the next chat

Useful tips
  • Variables: use #{buffer}, #{files}, … in prompts
  • Tools: use @{grep_search}, @{insert_edit_into_file}, … in prompts
  • Slash commands: /buffer, /files, /image, /now, …
  • Press ? in the chat buffer anytime to see context-aware keymaps
  • Action Palette provider can be vim.ui.select, telescope, mini.pick or snacks

Default config: https://github.com/olimorris/codecompanion.nvim/blob/main/lua/codecompanion/config.lua
--]]

return {
  "olimorris/codecompanion.nvim",
  cmd = {
    "CodeCompanion",
    "CodeCompanionChat",
    "CodeCompanionActions",
    "CodeCompanionHistory",
    "CodeCompanionSummaries",
  },
  dependencies = {
    "j-hui/fidget.nvim",
    "ravitemer/mcphub.nvim",
    "ravitemer/codecompanion-history.nvim",
    "echasnovski/mini.diff"
  },
  keys = {
    { "<leader>cA", "<cmd>CodeCompanionActions<cr>",     mode = { "n", "v" }, desc = "CodeCompanion: Actions" },
    { "<leader>cc", "<cmd>CodeCompanionChat Toggle<cr>", mode = { "n", "v" }, desc = "CodeCompanion: Toggle Chat" },
    { "<leader>ci", ":CodeCompanion ",                   mode = { "v" },      desc = "CodeCompanion: Inline Chat" },
    { "<leader>ca", "<cmd>CodeCompanionChat Add<cr>",    mode = "v",          desc = "CodeCompanion: Add selection to Chat" },
  },
  opts = {
    adapters = {
      http = {
        opts = {
          show_defaults = false,
        },
        anthropic = function()
          return require("codecompanion.adapters").extend("anthropic", {
            schema = {
              model = {
                -- default = "claude-opus-4-1-20250805",
                default = "claude-opus-4-20250514",
              },
              extended_thinking = {
                default = true,
              },
            },
          })
        end,
      },
    },
    strategies = {
      chat = {
        adapter = "anthropic",
        tools = {
          opts = {
            default_tools = {
              "insert_edit_into_file",
            },
          },
        },
        variables = {
          ["buffer"] = {
            opts = {
              default_params = 'watch', -- or 'pin', send full buffer on changes, 'watch' sends only changes
            },
          },
        },
        -- keymaps = {
        --   next_chat = {
        --     modes = { n = "<C-n>" },
        --   },
        --   previous_chat = {
        --     modes = { n = "<C-p>" },
        --   },
        --   next_header = {
        --     modes = { n = "n" },
        --   },
        --   previous_header = {
        --     modes = { n = "N" },
        --   },
        --   accept_change = {
        --     modes = { n = "ga" },
        --   },
        --   reject_change = {
        --     modes = { n = "gr" },
        --   },
        --   always_accept = {
        --     modes = { n = "gy" },
        --   },
        -- },
      },
      inline = {
        adapter = {
          name = "anthropic",
          model = "claude-3-5-haiku-latest",
        },
        keymaps = {
          accept_change = {
            modes = { n = "ga" },
          },
          reject_change = {
            modes = { n = "gr" },
          },
          always_accept = {
            modes = { n = "gy" },
          },
        },
      },
      cmd = {
        adapter = {
          name = "anthropic",
          model = "claude-3-5-haiku-latest",
        },
      },
    },
    display = {
      action_palette = {
        provider = "snacks",
      },
      chat = {
        window = {
          position = "right",
        }
      },
      show_settings = true,
      diff = {
        provider = "mini_diff"
      }
    },
    extensions = {
      -- mcphub = {
      --   callback = "mcphub.extensions.codecompanion",
      --   opts = {
      --     make_vars = true,
      --     make_slash_commands = true,
      --     show_result_in_chat = true
      --   }
      -- },
      history = {
        enabled = true,
        opts = {
          keymap = "gh",
          save_chat_keymap = "gs",
          picker = "snacks",
          continue_last_chat = false,
          dir_to_save = vim.fn.expand("$HOME") .. "/notes/ai/codecompanion_prompts",
          title_generation_opts = {
            adapter = "anthropic",
            model = "claude-3-7-sonnet-latest",
          },
          summary = {
            create_summary_keymap = "gcs",
            browse_summaries_keymap = "gbs",
            generation_opts = {
              adapter = "anthropic",
              model = "claude-3-7-sonnet-latest",
            },
          },
        },
      },
    },
  },
  init = function()
    vim.cmd([[
      cnoreabbrev CC CodeCompanion
    ]])
    require("plugins.custom.spinner"):init()
  end,
}

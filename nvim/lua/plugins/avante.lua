--[[
=== AVANTE.NVIM HOTKEYS REFERENCE ===

SIDEBAR CONTROLS:
]p                    - Next prompt
[p                    - Previous prompt
A                     - Apply all changes
a                     - Apply cursor changes
r                     - Retry user request
e                     - Edit user request
<Tab>                 - Switch windows
<S-Tab>               - Reverse switch windows
d                     - Remove file from context
@                     - Add file to context
q                     - Close sidebar
<leader>aa            - Show sidebar
<leader>at            - Toggle sidebar visibility
<leader>ar            - Refresh sidebar
<leader>af            - Switch sidebar focus

SUGGESTIONS:
<leader>a?            - Select model
<leader>an            - New ask
<leader>ae            - Edit selected blocks
<leader>aS            - Stop current AI request
<leader>ah            - Select between chat histories
<M-l>                 - Accept suggestion
<M-]>                 - Next suggestion
<M-[>                 - Previous suggestion
<C-]>                 - Dismiss suggestion
<leader>ad            - Toggle debug mode
<leader>as            - Toggle suggestion display
<leader>aR            - Toggle repomap

FILES:
<leader>ac            - Add current buffer to selected files
<leader>aB            - Add all buffer files to selected files

DIFF CONTROLS:
co                    - Choose ours
ct                    - Choose theirs
ca                    - Choose all theirs
cb                    - Choose both
cc                    - Choose cursor
]x                    - Move to next conflict
[x                    - Move to previous conflict

CONFIRM WINDOW:
<C-w>f                - Focus confirm window
c                     - Confirm code
r                     - Confirm response
i                     - Confirm input

COMMANDS:
:AvanteAsk [question] [position] - Ask AI about your code
:AvanteBuild          - Build dependencies
:AvanteChat           - Start chat session
:AvanteChatNew        - Start new chat session
:AvanteHistory        - Open chat history picker
:AvanteClear          - Clear chat history
:AvanteEdit           - Edit selected code blocks
:AvanteFocus          - Switch focus to/from sidebar
:AvanteRefresh        - Refresh all windows
:AvanteStop           - Stop current AI request
:AvanteSwitchProvider - Switch AI provider
:AvanteShowRepoMap    - Show repository map
:AvanteToggle         - Toggle sidebar
:AvanteModels         - Show model list
:AvanteSwitchSelectorProvider - Switch selector provider

COMPLETION SOURCES (with nvim-cmp/blink.cmp):
@codebase             - Enable project context
@diagnostics          - Enable diagnostics info
@file                 - Open file selector
@quickfix             - Add quickfix files
@buffers              - Add open buffers
/help                 - Show help message
/init                 - Initialize AGENTS.md
/clear                - Clear chat history
/new                  - Start new chat
/compact              - Compact history
/lines <n>-<m>        - Ask about specific lines
/commit               - Generate commit message
#refactor             - Refactor code shortcut
#test                 - Generate tests shortcut
--]]

return {
  "yetone/avante.nvim",
  enabled = false,
  build = vim.fn.has("win32") ~= 0
      and "powershell -ExecutionPolicy Bypass -File Build.ps1 -BuildFromSource false"
      or "make",
  event = "VeryLazy",
  version = false,
  dependencies = {
    "nvim-lua/plenary.nvim",
    "MunifTanjim/nui.nvim",
  },
  opts = {
    provider = "claude",
    providers = {
      claude = {
        model = "claude-sonnet-4-20250514",
      },
      gemini = {
        -- @see https://ai.google.dev/gemini-api/docs/models/gemini
        model = "gemini-2.5-pro",
        extra_request_body = {
          temperature = 0,
          max_tokens = 8192,
        },
      },
    },
    web_search_engine = {
      provider = "google",
    },
    prompt_logger = {
      log_dir = vim.fn.expand("$HOME") .. "/notes/ai/avante_prompts",
    },
    behaviour = {
      enable_token_counting = false,
    },
  }
}

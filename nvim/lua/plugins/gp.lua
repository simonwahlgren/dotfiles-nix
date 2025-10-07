--[[
gp.nvim — Built-ins quick reference

CHAT BUFFER HOTKEYS (built-in, buffer-local defaults)
  <C-g><C-g>  — Respond in current chat            (chat_shortcut_respond)
  <C-g>d      — Delete current chat (asks confirm) (chat_shortcut_delete)
  <C-g>s      — Stop all running jobs              (chat_shortcut_stop)
  <C-g>c      — New chat from here/selection      (chat_shortcut_new)
  In Chat Finder: <C-d> deletes a selected chat   (chat_finder_mappings.delete)

CHAT COMMANDS
  :GpChatNew [vsplit|split|tabnew|popup]
      Open a fresh chat (uses selection/range if provided).
  :GpChatPaste [vsplit|split|tabnew|popup]
      Paste selection/range into the latest chat.
  :GpChatToggle [vsplit|split|tabnew|popup]
      Toggle last chat (or start new from selection/range).
  :GpChatFinder
      Search/preview/open/delete chats.
  :GpChatRespond [N]
      Ask for a new response; with N, use only the last N “..” sections.
  :GpChatDelete
      Delete current chat (confirm unless disabled in config).

OTHER HANDY COMMANDS (non-chat but you’ll likely use them)
  Text/code targets:
    :GpRewrite [prompt] | :GpAppend | :GpPrepend | :GpEnew
    :GpNew | :GpVnew | :GpTabnew | :GpPopup | :GpImplement
  Repo context file:
    :GpContext [vsplit|split|tabnew|popup]
  Agents & misc:
    :GpNextAgent | :GpAgent [NAME] | :GpSelectAgent
    :GpStop
  Speech (optional, needs sox):
    :GpWhisper[Rewrite|Append|Prepend|Enew|New|Vnew|Tabnew|Popup] {lang?}
]]

return {
  "robitx/gp.nvim",
  enabled = false,
  cmd = {
    "GpChatNew", "GpChatPaste", "GpChatToggle", "GpChatFinder", "GpChatRespond",
    "GpChatDelete", "GpRewrite", "GpAppend", "GpPrepend", "GpEnew",
    "GpNew", "GpVnew", "GpTabnew", "GpPopup", "GpImplement", "GpContext",
    "GpNextAgent", "GpAgent", "GpSelectAgent", "GpStop",
    "GpWhisper", "GpWhisperRewrite", "GpWhisperAppend", "GpWhisperPrepend",
    "GpWhisperEnew", "GpWhisperNew", "GpWhisperVnew", "GpWhisperTabnew", "GpWhisperPopup",
  },
  config = function()
    local gp = require("gp")

    -- Minimal, Anthropic-first setup
    local conf = {
      -- You can keep OPENAI here if you also use it elsewhere; not required.
      providers = {
        anthropic = {
          endpoint = "https://api.anthropic.com/v1/messages",
          secret = os.getenv("ANTHROPIC_API_KEY"),
        },
      },

      -- Define at least one chat agent and one command agent
      agents = {
        {
          name = "ClaudeChat",
          provider = "anthropic",
          chat = true,
          command = false,
          -- Claude model; adjust to what you have access to
          -- (e.g. "claude-3-5-sonnet-20240620")
          model = { model = "claude-sonnet-4-20250514", max_tokens = 4096 },
          system_prompt = "You are an expert, concise, pragmatic pair programmer and technical writer.",
        },
        {
          name = "ClaudeCmd",
          provider = "anthropic",
          chat = false,
          command = true,
          model = { model = "claude-3-5-sonnet-20240620", max_tokens = 4096 },
          system_prompt =
            "When editing code, be precise and deterministic. Prefer minimal diffs and explain only when requested.",
        },
      },

      -- Make the Anthropic agents the defaults
      -- (gp.nvim persists chosen agents; this is just the initial default)
      default_agent = "ClaudeChat",
      default_command_agent = "ClaudeCmd",

      -- Keep the handy built-in chat buffer shortcuts (documented above)
      chat_shortcut_respond = { modes = { "n", "i", "v", "x" }, shortcut = "<C-g><C-g>" },
      chat_shortcut_delete  = { modes = { "n", "i", "v", "x" }, shortcut = "<C-g>d" },
      chat_shortcut_stop    = { modes = { "n", "i", "v", "x" }, shortcut = "<C-g>s" },
      chat_shortcut_new     = { modes = { "n", "i", "v", "x" }, shortcut = "<C-g>c" },
      chat_finder_mappings  = {
        delete = { modes = { "n", "i", "v", "x" }, shortcut = "<C-d>" },
      },

      -- Optional: where :GpChatToggle / :GpContext appear by default
      toggle_target = "vsplit",
    }

    gp.setup(conf)

    -- Optional global keymaps (comment out if you prefer none).
    -- These mirror the README examples and won’t interfere with your leader maps.
    local function KM(desc) return { noremap = true, silent = true, nowait = true, desc = "gp: " .. desc } end
    vim.keymap.set({ "n", "i" }, "<C-g>c", "<cmd>GpChatNew<CR>",            KM("New Chat"))
    vim.keymap.set({ "n", "i" }, "<C-g>t", "<cmd>GpChatToggle<CR>",         KM("Toggle Chat"))
    vim.keymap.set({ "n", "i" }, "<C-g>f", "<cmd>GpChatFinder<CR>",         KM("Chat Finder"))
    vim.keymap.set({ "n", "i" }, "<C-g>r", "<cmd>GpRewrite<CR>",            KM("Rewrite Inline"))
    vim.keymap.set({ "n", "i" }, "<C-g>a", "<cmd>GpAppend<CR>",             KM("Append"))
    vim.keymap.set({ "n", "i" }, "<C-g>b", "<cmd>GpPrepend<CR>",            KM("Prepend"))
    vim.keymap.set({ "n", "i", "v", "x" }, "<C-g>n", "<cmd>GpNextAgent<CR>",KM("Next Agent"))
    vim.keymap.set({ "n", "i", "v", "x" }, "<C-g>l", "<cmd>GpSelectAgent<CR>", KM("Select Agent"))
  end,
}

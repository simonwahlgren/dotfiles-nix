return {
  "milanglacier/minuet-ai.nvim",
  enabled = false,
  dependencies = { "nvim-lua/plenary.nvim" },
  opts = {
    -- notify = "debug",
    provider = "codestral",
    provider_options = {
      codestral = {
        model = "codestral-latest",
        end_point = "https://codestral.mistral.ai/v1/fim/completions",
        api_key = "CODESTRAL_API_KEY",
        stream = true,
        optional = {
          max_tokens = 256,
          stop = { '\n\n' },
        },
      },
    },

    -- Inline ghost text (Copilot-like)
    virtualtext = {
      auto_trigger_ft = { "lua", "python" },
      show_on_completion_menu = true, -- show both ghost text and completion menu
      keymap = {
        accept = "<C-Up>",
        accept_line = "<C-Down>",
        next = "<C-Right>",
        prev = "<C-Left>",
      },
    },

    -- Sensible timeouts for LLMs
    request_timeout = 5,
    throttle = 1500,
    debounce = 250,
  },
}

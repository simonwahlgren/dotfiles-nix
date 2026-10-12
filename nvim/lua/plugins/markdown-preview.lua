return {
  "brianhuster/live-preview.nvim",
  ft = { "markdown", "html", "asciidoc" },
  keys = {
    {
      "<leader>mp",
      function()
        local cfg = require("livepreview.config").config
        local listening = require("livepreview.utils").processes_listening_on_port

        require("livepreview").close() -- stop this instance's server (async)

        vim.defer_fn(function()
          -- Pick the first port nobody is listening on, so a stale preview
          -- in another nvim squatting the default port can't block us.
          local port = 5500
          for _ = 0, 20 do
            if #listening(port) == 0 then
              break
            end
            port = port + 1
          end
          cfg.port = port
          vim.cmd("LivePreview start")
        end, 100)
      end,
      desc = "Live preview: restart for current file",
    },
  },
  opts = {},
}

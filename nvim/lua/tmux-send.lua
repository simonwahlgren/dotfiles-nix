local M = {}

local function notify(message)
  vim.notify("tmux-send: " .. message, vim.log.levels.ERROR)
end

local function tmux(args, stdin)
  local command = { "tmux" }
  vim.list_extend(command, args)
  local ok, result = pcall(function()
    return vim.system(command, { text = true, stdin = stdin }):wait(3000)
  end)
  if not ok then
    return nil, tostring(result)
  end
  if result.code ~= 0 then
    return nil, vim.trim(result.stderr or "") ~= "" and vim.trim(result.stderr)
      or "tmux command failed (exit " .. result.code .. ")"
  end
  return result.stdout or ""
end

local function pane_state(pane)
  local output, err = tmux({ "display-message", "-p", "-t", pane,
    "#{pane_id}\t#{session_id}\t#{window_id}\t#{pane_dead}" })
  if not output then
    return nil, err
  end
  local fields = vim.split(output:gsub("\n$", ""), "\t", { plain = true })
  if fields[1] ~= pane or #fields ~= 4 then
    return nil, "Cannot resolve tmux pane " .. pane
  end
  return { id = fields[1], session = fields[2], window = fields[3], dead = fields[4] }
end

local function send(pane, source, payload)
  local current_source, err = pane_state(source.id)
  if not current_source then
    notify("Source pane is no longer available: " .. err)
    return
  end
  local target
  target, err = pane_state(pane.id)
  if not target or target.dead ~= "0" then
    notify("Destination pane is no longer available" .. (err and ": " .. err or "."))
    return
  end
  if current_source.session ~= source.session or target.session ~= source.session then
    notify("The source or destination pane has moved to another session. Select again.")
    return
  end
  local buffer = "nvim-selection-" .. vim.fn.getpid() .. "-" .. tostring(vim.uv.hrtime())
  local loaded
  loaded, err = tmux({ "load-buffer", "-b", buffer, "-" }, payload)
  if not loaded then
    tmux({ "delete-buffer", "-b", buffer })
    notify("Could not load selection: " .. err)
    return
  end
  local pasted
  pasted, err = tmux({ "paste-buffer", "-p", "-r", "-d", "-b", buffer, "-t", target.id })
  if not pasted then
    tmux({ "delete-buffer", "-b", buffer })
    notify("Could not paste selection: " .. err)
    return
  end

  local focused
  focused, err = tmux({ "select-window", "-t", source.session .. ":" .. target.window })
  if focused then
    focused, err = tmux({ "select-pane", "-t", target.id })
  end
  if not focused then
    notify("Selection was pasted, but could not focus the destination: " .. err)
  end
end

function M.send_selection()
  local mode = vim.fn.mode()
  if mode ~= "v" and mode ~= "V" and mode ~= "\22" then
    notify("Select text in visual mode first.")
    return
  end
  if vim.fn.executable("tmux") ~= 1 or not vim.env.TMUX or not vim.env.TMUX_PANE then
    notify("Run Neovim inside tmux to send a selection.")
    return
  end

  local first, last = vim.fn.getpos("v"), vim.fn.getpos(".")
  local region_opts = { type = mode, exclusive = vim.o.selection == "exclusive" }
  local text = vim.fn.getregion(first, last, region_opts)
  local positions = vim.fn.getregionpos(first, last, region_opts)
  local path = vim.api.nvim_buf_get_name(0)
  if path == "" then
    path = "[No Name]"
  else
    path = vim.fn.fnamemodify(path, ":p")
  end
  local payload = string.format("Reference: %s:L%d-%d\n\n%s", path,
    positions[1][1][2], positions[#positions][2][2], table.concat(text, "\n"))
  vim.cmd("normal! \27")

  local source, err = pane_state(vim.env.TMUX_PANE)
  if not source then
    notify("Cannot resolve source pane: " .. err)
    return
  end
  local output
  output, err = tmux({ "list-panes", "-s", "-t", source.session, "-F",
    "#{pane_id}\t#{pane_dead}\t#{window_index}\t#{pane_index}\t#{window_name}\t#{pane_current_command}\t#{pane_title}" })
  if not output then
    notify("Could not list destination panes: " .. err)
    return
  end
  local panes = {}
  for line in output:gmatch("[^\n]+") do
    local fields = vim.split(line, "\t", { plain = true })
    if #fields >= 7 and fields[1]:match("^%%%d+$") and fields[1] ~= source.id and fields[2] == "0" then
      table.insert(panes, {
        id = fields[1],
        label = string.format("%s.%s %s | %s | %s", fields[3], fields[4], fields[5], fields[6],
          table.concat(fields, " ", 7)),
      })
    end
  end
  if #panes == 0 then
    notify("No other live panes in this tmux session.")
    return
  end
  vim.ui.select(panes, {
    prompt = "Send selection to tmux pane:",
    format_item = function(pane) return pane.label end,
  }, function(pane)
    if pane then
      send(pane, source, payload)
    end
  end)
end

return M

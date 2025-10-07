-- Floating terminal for cursor-agent integration
-- Usage: Add to your init.lua and map a key to toggle

local M = {}

-- State to track the floating terminal per project
-- We store sessions by project root to support multiple projects
local sessions = {}

local state = {
  buf = nil,
  win = nil,
  job_id = nil,
}

-- Get session file path for storing chat IDs per project
local function get_session_file()
  local data_dir = vim.fn.stdpath('data') .. '/cursor-agent-sessions'
  vim.fn.mkdir(data_dir, 'p')
  return data_dir .. '/sessions.json'
end

-- Load all saved sessions from disk
local function load_sessions()
  local session_file = get_session_file()
  local file = io.open(session_file, 'r')
  if file then
    local content = file:read('*all')
    file:close()
    local ok, decoded = pcall(vim.json.decode, content)
    if ok and decoded then
      sessions = decoded
    end
  end
end

-- Save sessions to disk
local function save_sessions()
  local session_file = get_session_file()
  local file = io.open(session_file, 'w')
  if file then
    file:write(vim.json.encode(sessions))
    file:close()
  end
end

-- Get or create chat ID for current project root
local function get_or_create_chat_id()
  local project_root = vim.fn.getcwd()

  -- Load existing sessions
  load_sessions()

  -- Return existing chat ID if we have one for this project
  if sessions[project_root] then
    return sessions[project_root]
  end

  -- Create new chat and get its ID
  local handle = io.popen('cursor-agent create-chat 2>&1')
  if handle then
    local chat_id = handle:read('*all'):gsub('%s+$', '') -- trim whitespace
    handle:close()

    if chat_id and chat_id ~= '' then
      -- Save the chat ID for this project
      sessions[project_root] = chat_id
      save_sessions()
      return chat_id
    end
  end

  return nil
end

-- Create a centered floating window
local function create_floating_window()
  -- Get editor dimensions
  local width = vim.o.columns
  local height = vim.o.lines

  -- Calculate floating window size (80% of screen)
  local win_height = math.ceil(height * 0.8)
  local win_width = math.ceil(width * 0.8)

  -- Calculate starting position (centered)
  local row = math.ceil((height - win_height) / 2)
  local col = math.ceil((width - win_width) / 2)

  -- Create buffer if it doesn't exist
  if not state.buf or not vim.api.nvim_buf_is_valid(state.buf) then
    state.buf = vim.api.nvim_create_buf(false, true) -- No file, scratch buffer
    vim.api.nvim_buf_set_option(state.buf, 'bufhidden', 'hide')
    vim.api.nvim_buf_set_option(state.buf, 'filetype', 'terminal')
  end

  -- Window configuration
  local opts = {
    style = "minimal",
    relative = "editor",
    width = win_width,
    height = win_height,
    row = row,
    col = col,
    border = "rounded", -- Options: 'single', 'double', 'rounded', 'solid', 'shadow'
  }

  -- Create the floating window
  state.win = vim.api.nvim_open_win(state.buf, true, opts)

  -- Set window-local options
  vim.api.nvim_win_set_option(state.win, 'winblend', 0) -- 0 = opaque, 30 = semi-transparent

  -- Set buffer-local keymaps for easy closing
  local keymaps = {
    { 'n', '<Esc>',       ':lua require("cursor-agent-float").toggle()<CR>' },
    { 'n', 'q',           ':lua require("cursor-agent-float").toggle()<CR>' },
    { 't', '<Esc>',       '<C-\\><C-n>:lua require("cursor-agent-float").toggle()<CR>' }, -- Exit insert mode and close
    { 't', '<C-\\><C-n>', '<C-\\><C-n>' },                                          -- Easy terminal mode exit
  }

  for _, map in ipairs(keymaps) do
    vim.api.nvim_buf_set_keymap(
      state.buf,
      map[1],
      map[2],
      map[3],
      { noremap = true, silent = true }
    )
  end

  return state.win
end

-- Start cursor-agent in the terminal
local function start_cursor_agent()
  -- Get project root (vim's current working directory)
  local project_root = vim.fn.getcwd()

  -- Get or create chat ID for this project
  local chat_id = get_or_create_chat_id()

  -- Build command with resume if we have a chat ID
  -- cd into project root first so cursor-agent uses it as context by default
  local cmd
  if chat_id then
    cmd = 'cd ' .. vim.fn.shellescape(project_root) .. ' && cursor-agent --resume ' .. chat_id
  else
    -- Fallback: start without resume if chat creation failed
    cmd = 'cd ' .. vim.fn.shellescape(project_root) .. ' && cursor-agent chat'
  end

  -- Only start a new job if one doesn't exist
  if not state.job_id then
    state.job_id = vim.fn.termopen(cmd, {
      on_exit = function()
        state.job_id = nil
      end
    })
  end

  -- Enter insert mode in terminal
  vim.cmd('startinsert')
end

-- Toggle the floating terminal
function M.toggle()
  -- If window exists and is valid, hide it
  if state.win and vim.api.nvim_win_is_valid(state.win) then
    vim.api.nvim_win_hide(state.win)
    state.win = nil
    return
  end

  -- Otherwise, show/create the window
  create_floating_window()

  -- If this is the first time, start cursor-agent
  if not state.job_id then
    start_cursor_agent()
  else
    -- Just enter insert mode if terminal already running
    vim.cmd('startinsert')
  end
end

-- Restart cursor-agent (useful if you want to change context)
function M.restart()
  if state.job_id then
    vim.fn.jobstop(state.job_id)
    state.job_id = nil
  end

  if state.buf and vim.api.nvim_buf_is_valid(state.buf) then
    vim.api.nvim_buf_delete(state.buf, { force = true })
    state.buf = nil
  end

  M.toggle()
end

-- Start a new chat session for current project (clears old session)
function M.new_session()
  -- Get project root
  local project_root = vim.fn.getcwd()

  -- Stop existing job
  if state.job_id then
    vim.fn.jobstop(state.job_id)
    state.job_id = nil
  end

  -- Delete buffer
  if state.buf and vim.api.nvim_buf_is_valid(state.buf) then
    vim.api.nvim_buf_delete(state.buf, { force = true })
    state.buf = nil
  end

  -- Clear the saved session for this project
  load_sessions()
  sessions[project_root] = nil
  save_sessions()

  -- Start fresh
  M.toggle()
end

-- Clear all saved sessions
function M.clear_all_sessions()
  sessions = {}
  save_sessions()
  print('Cleared all cursor-agent sessions')
end

-- Ask a specific question with project context
function M.ask(question)
  local project_root = vim.fn.getcwd()

  -- Create window if needed
  if not state.win or not vim.api.nvim_win_is_valid(state.win) then
    create_floating_window()
  end

  -- Send the question to cursor-agent
  local cmd = 'cursor-agent chat @' .. project_root .. ' "' .. question .. '"\n'

  if state.job_id then
    vim.fn.chansend(state.job_id, cmd)
  else
    state.job_id = vim.fn.termopen('cursor-agent chat @' .. project_root, {
      on_exit = function()
        state.job_id = nil
      end
    })
    vim.fn.chansend(state.job_id, question .. '\n')
  end

  vim.cmd('startinsert')
end

return M

-- Floating terminal for cursor-agent integration
-- Usage: Add to your init.lua and map a key to toggle

local M = {}

-- State to track the floating terminal per project
-- We store sessions by project root to support multiple projects
local sessions = {}

-- State for persistent terminal (with resume)
local state = {
  buf = nil,
  win = nil,
  job_id = nil,
}

-- State for ephemeral terminal (no resume, fresh each time)
local ephemeral_state = {
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
local function create_floating_window(term_state, toggle_cmd)
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
  if not term_state.buf or not vim.api.nvim_buf_is_valid(term_state.buf) then
    term_state.buf = vim.api.nvim_create_buf(false, true) -- No file, scratch buffer
    vim.api.nvim_buf_set_option(term_state.buf, 'bufhidden', 'hide')
    vim.api.nvim_buf_set_option(term_state.buf, 'filetype', 'terminal')
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
  term_state.win = vim.api.nvim_open_win(term_state.buf, true, opts)

  -- Set window-local options
  vim.api.nvim_win_set_option(term_state.win, 'winblend', 0) -- 0 = opaque, 30 = semi-transparent

  -- Set buffer-local keymaps for easy closing
  -- In terminal normal mode: 'q' closes the terminal
  vim.api.nvim_buf_set_keymap(
    term_state.buf,
    'n',
    'q',
    ':lua require("cursor-agent-float").' .. toggle_cmd .. '()<CR>',
    { noremap = true, silent = true }
  )
  
  -- In terminal insert mode: Ctrl+q closes the terminal (works from anywhere)
  vim.api.nvim_buf_set_keymap(
    term_state.buf,
    't',
    '<C-q>',
    '<C-\\><C-n>:lua require("cursor-agent-float").' .. toggle_cmd .. '()<CR>',
    { noremap = true, silent = true }
  )
  
  -- Esc is left unbound in terminal mode, so it passes through to cursor-agent
  -- This allows cursor-agent to handle Esc for closing menus, exiting review mode, etc.

  return term_state.win
end

-- Start cursor-agent in the terminal
local function start_cursor_agent(term_state, ephemeral)
  -- Get project root (vim's current working directory)
  local project_root = vim.fn.getcwd()

  -- Build command
  local cmd
  if ephemeral then
    -- Ephemeral mode: always start fresh without resume
    -- This ensures ephemeral sessions don't interfere with persistent ones
    cmd = 'cursor-agent'
  else
    -- Persistent mode: use a dedicated chat ID per project
    local chat_id = get_or_create_chat_id()
    if chat_id then
      -- Resume the specific chat for this project
      cmd = 'cursor-agent --resume=' .. chat_id
    else
      -- Fallback if we couldn't get/create a chat ID
      cmd = 'bash -c "cursor-agent resume 2>/dev/null || cursor-agent"'
    end
  end

  -- Only start a new job if one doesn't exist
  if not term_state.job_id then
    -- Start terminal in the project directory
    term_state.job_id = vim.fn.termopen(cmd, {
      cwd = project_root,
      on_exit = function(job_id, exit_code, event_type)
        term_state.job_id = nil
        -- Delete the buffer when the job exits to ensure clean restart
        if term_state.buf and vim.api.nvim_buf_is_valid(term_state.buf) then
          vim.api.nvim_buf_delete(term_state.buf, { force = true })
          term_state.buf = nil
        end
      end
    })
  end

  -- Enter insert mode in terminal
  vim.cmd('startinsert')
end

-- Toggle the floating terminal (persistent with resume)
function M.toggle()
  -- Exit terminal mode if we're in it (use feedkeys to avoid re-enter error)
  if vim.fn.mode() == 't' then
    vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes('<C-\\><C-n>', true, false, true), 'n', false)
    -- Wait a bit for mode change to complete
    vim.wait(10)
  end

  -- Hide ephemeral window if it's open
  if ephemeral_state.win and vim.api.nvim_win_is_valid(ephemeral_state.win) then
    vim.api.nvim_win_hide(ephemeral_state.win)
    ephemeral_state.win = nil
  end

  -- If persistent window exists and is valid, hide it
  if state.win and vim.api.nvim_win_is_valid(state.win) then
    vim.api.nvim_win_hide(state.win)
    state.win = nil
    return
  end

  -- Otherwise, show/create the window
  create_floating_window(state, 'toggle')

  -- If this is the first time, start cursor-agent
  if not state.job_id then
    start_cursor_agent(state, false)
  else
    -- Just enter insert mode if terminal already running
    vim.cmd('startinsert')
  end
end

-- Toggle the ephemeral floating terminal (no resume, fresh each time)
function M.toggle_ephemeral()
  -- Exit terminal mode if we're in it (use feedkeys to avoid re-enter error)
  if vim.fn.mode() == 't' then
    vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes('<C-\\><C-n>', true, false, true), 'n', false)
    -- Wait a bit for mode change to complete
    vim.wait(10)
  end

  -- Hide persistent window if it's open
  if state.win and vim.api.nvim_win_is_valid(state.win) then
    vim.api.nvim_win_hide(state.win)
    state.win = nil
  end

  -- If ephemeral window exists and is valid, hide it
  if ephemeral_state.win and vim.api.nvim_win_is_valid(ephemeral_state.win) then
    vim.api.nvim_win_hide(ephemeral_state.win)
    ephemeral_state.win = nil
    return
  end

  -- Otherwise, show/create the window
  create_floating_window(ephemeral_state, 'toggle_ephemeral')

  -- If this is the first time, start cursor-agent in ephemeral mode
  if not ephemeral_state.job_id then
    start_cursor_agent(ephemeral_state, true)
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

-- Send visually selected code as reference to cursor-agent (persistent terminal)
function M.send_selection()
  -- Get current file path relative to project root
  local filepath = vim.fn.expand("%:.")
  
  -- Check if we're in visual mode
  local mode = vim.fn.mode()
  local reference
  
  if mode == 'v' or mode == 'V' or mode == '\22' then
    -- Visual mode: get selection range
    local start_pos = vim.fn.getpos("v")
    local end_pos = vim.fn.getpos(".")
    
    local start_line = start_pos[2]
    local end_line = end_pos[2]
    
    -- Ensure start_line is before end_line
    if start_line > end_line then
      start_line, end_line = end_line, start_line
    end
    
    -- Format the reference with line numbers
    reference = string.format("Reference: %s:L%d-%d. ", filepath, start_line, end_line)
  else
    -- No visual selection: send entire file path
    reference = string.format("Reference: %s. ", filepath)
  end

  -- Show/create the window if needed
  if not state.win or not vim.api.nvim_win_is_valid(state.win) then
    create_floating_window(state, 'toggle')
  end

  -- Start cursor-agent if not running
  if not state.job_id then
    start_cursor_agent(state, false)
    -- Wait a bit for the terminal to be ready
    vim.defer_fn(function()
      vim.fn.chansend(state.job_id, reference)
    end, 500)
  else
    -- Send the reference to the terminal
    vim.fn.chansend(state.job_id, reference)
  end

  -- Enter insert mode so user can type their question
  vim.cmd('startinsert')
end

-- Send visually selected code as reference to cursor-agent (ephemeral terminal)
function M.send_selection_ephemeral()
  -- Get current file path relative to project root
  local filepath = vim.fn.expand("%:.")
  
  -- Check if we're in visual mode
  local mode = vim.fn.mode()
  local reference
  
  if mode == 'v' or mode == 'V' or mode == '\22' then
    -- Visual mode: get selection range
    local start_pos = vim.fn.getpos("v")
    local end_pos = vim.fn.getpos(".")
    
    local start_line = start_pos[2]
    local end_line = end_pos[2]
    
    -- Ensure start_line is before end_line
    if start_line > end_line then
      start_line, end_line = end_line, start_line
    end
    
    -- Format the reference with line numbers
    reference = string.format("Reference: %s:L%d-%d. ", filepath, start_line, end_line)
  else
    -- No visual selection: send entire file path
    reference = string.format("Reference: %s. ", filepath)
  end

  -- Show/create the window if needed
  if not ephemeral_state.win or not vim.api.nvim_win_is_valid(ephemeral_state.win) then
    create_floating_window(ephemeral_state, 'toggle_ephemeral')
  end

  -- Start cursor-agent if not running
  if not ephemeral_state.job_id then
    start_cursor_agent(ephemeral_state, true)
    -- Wait a bit for the terminal to be ready
    vim.defer_fn(function()
      vim.fn.chansend(ephemeral_state.job_id, reference)
    end, 500)
  else
    -- Send the reference to the terminal
    vim.fn.chansend(ephemeral_state.job_id, reference)
  end

  -- Enter insert mode so user can type their question
  vim.cmd('startinsert')
end

return M

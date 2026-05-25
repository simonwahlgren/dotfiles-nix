-- Floating terminal for Claude CLI integration
-- Usage: Add to your init.lua and map a key to toggle

local M = {}

local state = {
  buf = nil,
  win = nil,
  job_id = nil,
}

-- Track last Esc press time for double-Esc detection
local last_esc_time = 0
local esc_timeout_ms = 300

-- Handle Esc key in terminal mode: first Esc goes to claude, second Esc exits terminal mode
local function handle_terminal_esc()
  local current_time = vim.loop.now()

  if current_time - last_esc_time < esc_timeout_ms then
    last_esc_time = 0
    return '<C-\\><C-n>'
  else
    last_esc_time = current_time
    return '<Esc>'
  end
end

-- Create a centered floating window
local function create_floating_window()
  local width = vim.o.columns
  local height = vim.o.lines

  local win_height = math.ceil(height * 0.8)
  local win_width = math.ceil(width * 0.8)

  local row = math.ceil((height - win_height) / 2)
  local col = math.ceil((width - win_width) / 2)

  if not state.buf or not vim.api.nvim_buf_is_valid(state.buf) then
    state.buf = vim.api.nvim_create_buf(false, true)
    vim.api.nvim_buf_set_option(state.buf, 'bufhidden', 'hide')
    vim.api.nvim_buf_set_option(state.buf, 'filetype', 'terminal')
  end

  local opts = {
    style = "minimal",
    relative = "editor",
    width = win_width,
    height = win_height,
    row = row,
    col = col,
    border = "rounded",
  }

  state.win = vim.api.nvim_open_win(state.buf, true, opts)
  vim.api.nvim_win_set_option(state.win, 'winblend', 0)

  vim.api.nvim_buf_set_keymap(
    state.buf, 'n', 'q',
    ':lua require("claude-float").toggle()<CR>',
    { noremap = true, silent = true }
  )

  vim.api.nvim_buf_set_keymap(
    state.buf, 't', '<C-q>',
    '<C-\\><C-n>:lua require("claude-float").toggle()<CR>',
    { noremap = true, silent = true }
  )

  vim.keymap.set('t', '<Esc>', handle_terminal_esc, {
    buffer = state.buf,
    expr = true,
    noremap = true,
    silent = true,
  })

  return state.win
end

-- Start claude in the terminal
local function start_claude()
  local project_root = vim.fn.getcwd()

  if not state.job_id then
    state.job_id = vim.fn.termopen('claude -c || claude', {
      cwd = project_root,
      on_exit = function()
        state.job_id = nil
        if state.buf and vim.api.nvim_buf_is_valid(state.buf) then
          vim.api.nvim_buf_delete(state.buf, { force = true })
          state.buf = nil
        end
      end,
    })
  end

  vim.cmd('startinsert')
end

-- Toggle the floating terminal
function M.toggle()
  if vim.fn.mode() == 't' then
    vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes('<C-\\><C-n>', true, false, true), 'n', false)
    vim.wait(10)
  end

  if state.win and vim.api.nvim_win_is_valid(state.win) then
    vim.api.nvim_win_hide(state.win)
    state.win = nil
    -- Reload any buffers modified externally by claude
    vim.cmd('checktime')
    return
  end

  create_floating_window()

  if not state.job_id then
    start_claude()
  else
    vim.cmd('startinsert')
  end
end

-- Restart claude
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

-- Send visually selected code as reference to claude
function M.send_selection()
  local filepath = vim.fn.expand("%:.")

  local mode = vim.fn.mode()
  local reference

  if mode == 'v' or mode == 'V' or mode == '\22' then
    local start_pos = vim.fn.getpos("v")
    local end_pos = vim.fn.getpos(".")

    local start_line = start_pos[2]
    local end_line = end_pos[2]

    if start_line > end_line then
      start_line, end_line = end_line, start_line
    end

    reference = string.format("Reference: %s:L%d-%d. ", filepath, start_line, end_line)
  else
    reference = string.format("Reference: %s. ", filepath)
  end

  if not state.win or not vim.api.nvim_win_is_valid(state.win) then
    create_floating_window()
  end

  if not state.job_id then
    start_claude()
    vim.defer_fn(function()
      vim.fn.chansend(state.job_id, reference)
    end, 500)
  else
    vim.fn.chansend(state.job_id, reference)
  end

  vim.cmd('startinsert')
end

return M

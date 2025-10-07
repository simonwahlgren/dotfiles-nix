--------------------------------------------------------------------------------
-- General Options
--------------------------------------------------------------------------------
vim.opt.clipboard   = "unnamedplus"
vim.opt.wrap        = false
vim.opt.backup      = true
vim.opt.backupdir   = vim.fn.stdpath("data") .. "/backup//"
vim.opt.writebackup = true
vim.opt.backupcopy  = "yes"
vim.opt.swapfile    = false
vim.opt.undofile    = true
vim.opt.undodir     = vim.fn.stdpath("data") .. "/undo_file"
vim.opt.hidden      = true
vim.opt.joinspaces  = false
vim.opt.gdefault    = true
vim.opt.foldenable  = false
vim.opt.mouse       = "a"
vim.opt.spell       = true
vim.opt.spelllang   = "en_us"
-- vim.opt.thesaurus:append("~/.local/share/nvim/thesaurii.txt")
vim.opt.inccommand  = "nosplit"
vim.opt.splitright  = true
vim.opt.virtualedit = "block"
vim.opt.grepprg     = [[rg --glob "!.git" --no-heading --vimgrep --follow $*]]
vim.opt.grepformat  = vim.opt.grepformat ^ { "%f:%l:%c:%m" }
vim.opt.diffopt     = {"filler", "internal", "algorithm:histogram", "indent-heuristic"}
vim.opt.signcolumn  = "number"
vim.opt.showcmd     = false

--------------------------------------------------------------------------------
-- Search Options
--------------------------------------------------------------------------------
vim.opt.scrolloff  = 10
vim.opt.incsearch  = true
vim.opt.hlsearch   = false
vim.opt.ignorecase = false
vim.opt.smartcase  = true

--------------------------------------------------------------------------------
-- Interface and Visual Settings
--------------------------------------------------------------------------------
vim.opt.cursorline     = true
vim.opt.ruler          = true
vim.opt.relativenumber = true
vim.opt.number         = true
vim.opt.synmaxcol      = 256
vim.cmd("syntax sync minlines=256")
vim.opt.list           = true
vim.opt.listchars      = { tab = "→ ", nbsp = "␣", trail = "•", extends = "⟩", precedes = "⟨" }
vim.opt.termguicolors  = true
vim.opt.cmdheight      = 0
vim.opt.laststatus     = 0

-- if vim.g.started_by_firenvim then
--   vim.cmd("colorscheme github_light")
--   vim.opt.laststatus = 0
-- else
--   vim.opt.background = "dark"
--   vim.cmd("colorscheme darch")
--   vim.opt.laststatus = 3
-- end

-- Simple statusline (customize as needed)
-- vim.opt.statusline = "%1* %{%toupper(mode())} %* %2*%f %="

--------------------------------------------------------------------------------
-- LSP
--------------------------------------------------------------------------------
vim.diagnostic.config({
  -- virtual_lines = {
  --   current_line = true
  -- },
  virtual_text = {
    current_line = true
  },
  signs = {
    text = {
      [vim.diagnostic.severity.ERROR] = "•",
      [vim.diagnostic.severity.WARN] = "•",
      [vim.diagnostic.severity.INFO] = "•",
      [vim.diagnostic.severity.HINT] = "•"
    },
    numhl = {
      [vim.diagnostic.severity.ERROR] = "DiagnosticSignError",
      [vim.diagnostic.severity.WARN] = "DiagnosticSignWarn",
      [vim.diagnostic.severity.INFO] = "DiagnosticSignInfo",
      [vim.diagnostic.severity.HINT] = "DiagnosticSignHint"
    },
    linehl = {
      [vim.diagnostic.severity.ERROR] = "DiagnosticSignErrorLine",
      [vim.diagnostic.severity.WARN] = "DiagnosticSignWarnLine",
      [vim.diagnostic.severity.INFO] = "DiagnosticSignInfoLine",
      [vim.diagnostic.severity.HINT] = "DiagnosticSignHintLine"
    }
  },
  underline = false,
  severity_sort = true,
})

--------------------------------------------------------------------------------
-- Mappings
--------------------------------------------------------------------------------
vim.g.mapleader = " "

-- Map Swedish characters
vim.keymap.set("n", "å", "[", { remap = true })
vim.keymap.set("n", "¨", "]", { remap = true })
vim.keymap.set("n", "ä", "{", { remap = true })
vim.keymap.set("n", "'", "}", { remap = true })

-- Buffers
vim.keymap.set("", "<C-q>", ":bd<cr>", { noremap = false, silent = true })
vim.keymap.set("", "<C-m-q>", ":bufdo bd!<cr>", { noremap = false, silent = true })

-- Reflow current line
vim.keymap.set("n", "Q", "gww", { noremap = true, silent = true })
vim.keymap.set("v", "Q", "gww", { noremap = true, silent = true })

-- Open URLs asynchronously
function _G.open_url()
  local file = vim.fn.expand("<cfile>")
  local cwd = vim.fn.getcwd()
  vim.fn.jobstart({ "xdg-open", cwd .. "/" .. file }, { detach = true })
end
vim.keymap.set("n", "go", ":lua open_url()<CR>", { noremap = true, silent = true })

-- Fast newline insertion
vim.keymap.set("n", "<leader><BS>", "O<Esc>j", { noremap = true, silent = true })
vim.keymap.set("n", "<leader><CR>", "o<Esc>k", { noremap = true, silent = true })

-- Jump to specific tab (1-9)
for i = 1, 9 do
  vim.keymap.set("n", "<leader>" .. i, i .. "gt", { noremap = true, silent = true })
end

-- Center screen after scrolling
vim.keymap.set("n", "<C-d>", "<C-d>zz", { noremap = true, silent = true })
vim.keymap.set("n", "<C-u>", "<C-u>zz", { noremap = true, silent = true })

-- Quick fix misspelled word and other mappings
vim.keymap.set("n", ",z", "1z=", { noremap = true, silent = true })

vim.keymap.set("n", "Y", "y$", { noremap = true, silent = true })
vim.keymap.set("n", "gp", "`[v`]", { noremap = true, silent = true })

-- Quick save
vim.keymap.set("n", "<leader><leader>", ":w!<CR>", { noremap = true, silent = true })

-- Jump to last active buffer
-- vim.keymap.set("n", "<leader>e", ":b#<CR>", { noremap = true, silent = true })

-- Navigate between split windows
vim.keymap.set("n", "<C-j>", "<C-W><C-j>", { noremap = true, silent = true })
vim.keymap.set("n", "<C-k>", "<C-W><C-k>", { noremap = true, silent = true })
vim.keymap.set("n", "<C-l>", "<C-W><C-l>", { noremap = true, silent = true })
vim.keymap.set("n", "<C-h>", "<C-W><C-h>", { noremap = true, silent = true })

-- Create new splits
vim.keymap.set("n", "<leader>sh", ":leftabove vnew<CR>", { noremap = true, silent = true })
vim.keymap.set("n", "<leader>sl", ":rightbelow vnew<CR>", { noremap = true, silent = true })
vim.keymap.set("n", "<leader>sk", ":leftabove new<CR>", { noremap = true, silent = true })
vim.keymap.set("n", "<leader>sj", ":rightbelow new<CR>", { noremap = true, silent = true })

vim.keymap.set("n", "<BS>", "daw", { noremap = true, silent = true })
vim.keymap.set("n", "H", "0", { noremap = true, silent = true })
vim.keymap.set("n", "L", "$", { noremap = true, silent = true })

vim.keymap.set("n", ",C", "c0", { noremap = true, silent = true })
vim.keymap.set("n", ",D", "d0", { noremap = true, silent = true })
vim.keymap.set("n", ",c", "c^", { noremap = true, silent = true })
vim.keymap.set("n", ",d", "d^", { noremap = true, silent = true })

vim.keymap.set("n", "c*", "*Ncgn", { noremap = true, silent = true })
vim.keymap.set("n", "c#", "#NcgN", { noremap = true, silent = true })
-- vim.keymap.set("v", "c*", "*Ncgn", { noremap = true, silent = true })
-- vim.keymap.set("v", "c#", "#NcgN", { noremap = true, silent = true })
vim.keymap.set("v", "c*", [["vy/<C-r>"<CR>Ncgn]], { noremap = true, silent = true })
vim.keymap.set("v", "c#", [["vy?<C-r>"<CR>NcgN]], { noremap = true, silent = true })

vim.keymap.set("n", "c,", "ct,", { noremap = true, silent = true })
vim.keymap.set("n", "d,", "dt,", { noremap = true, silent = true })
vim.keymap.set("n", "m,", "mt,", { noremap = true, silent = true })
vim.keymap.set("n", "c<space>", "cf<space>", { noremap = true, silent = true })
vim.keymap.set("n", "d<space>", "df<space>", { noremap = true, silent = true })
vim.keymap.set("n", "m<space>", "mf<space>", { noremap = true, silent = true })

-- vim.keymap.set("n", ",gl", ":diffget 1<CR>", { noremap = true, silent = true })
-- vim.keymap.set("n", ",gr", ":diffget 2<CR>", { noremap = true, silent = true })

vim.keymap.set("n", "<C-]>", "g<C-]>", { noremap = true, silent = true })
vim.keymap.set("n", "<M-s>", "<NOP>", { noremap = true, silent = true })

-- Search and replace current word
vim.keymap.set("n", ",s", [[:%s/\(<C-r>=expand("<cword>")<CR>\)/]], { noremap = true, silent = false })
vim.keymap.set("v", ",s", [[ "hy:%s/<C-r>h]], { noremap = true, silent = false })

-- Yank and reselect yanked block, then place cursor at the last character (in visual mode)
vim.keymap.set("v", "y", "ygv<Esc>", { noremap = true, silent = true })

-- Keep selection after indenting (visual mode)
vim.keymap.set("v", ">", ">gv", { noremap = true, silent = true })
vim.keymap.set("v", "<", "<gv", { noremap = true, silent = true })

-- Repeat macro over selected lines (visual mode)
vim.keymap.set("v", "@", ":norm @q<CR>", { noremap = true, silent = true })

-- Open file under cursor in new tab (normal and visual modes)
vim.keymap.set("n", "gf", "<C-W>gf", { noremap = true, silent = true })
vim.keymap.set("v", "gf", "<C-W>gf", { noremap = true, silent = true })

-- Open currently open file in a new tab and change CWD for the tab (normal mode)
vim.keymap.set("n", "gF", ":tabnew %<CR>:tcd %:h<CR>", { noremap = true, silent = true })

-- Paste with Ctrl-V in insert mode
vim.keymap.set("i", "<C-v>", "<C-r>+", { noremap = true, silent = true })

-- Make dot repeat work over visual line selection
vim.keymap.set("x", ".", ":norm.<CR>", { noremap = true, silent = true })

-- Visually selects pasted text and then re-indents it
vim.keymap.set("n", "<leader>p", "p`[v`]=", { noremap = true, silent = true })

-- Reflow current line
vim.keymap.set('n', 'Q', 'gww', { buffer = true })
vim.keymap.set('v', 'Q', 'gww', { buffer = true })

-- Move lines with one undo step.
function _G.setUndojoinFlag(mode)
  vim.cmd("augroup undojoin_flag")
  vim.cmd("autocmd!")
  if mode == "v" then
    vim.cmd("autocmd CursorMoved * autocmd undojoin_flag CursorMoved * autocmd! undojoin_flag")
  else
    vim.cmd("autocmd CursorMoved * autocmd! undojoin_flag")
  end
  vim.cmd("augroup END")
end

function _G.undojoin()
  if vim.fn.exists("#undojoin_flag#CursorMoved") == 1 then
    vim.cmd("silent! undojoin")
  end
end

vim.keymap.set("n", "<C-M-j>", ":lua undojoin()<CR>:lua vim.cmd('move +1')<CR>==:lua setUndojoinFlag('n')<CR>", { noremap = true, silent = true })
vim.keymap.set("n", "<C-M-k>", ":lua undojoin()<CR>:lua vim.cmd('move -2')<CR>==:lua setUndojoinFlag('n')<CR>", { noremap = true, silent = true })
vim.keymap.set("x", "<C-M-j>", ":lua undojoin()<CR>:lua vim.cmd(\"'<,'>move '>+1\")<CR>gv:lua setUndojoinFlag('v')<CR>gv", { noremap = true, silent = true })
vim.keymap.set("x", "<C-M-k>", ":lua undojoin()<CR>:lua vim.cmd(\"'<,'>move '<-2\")<CR>gv:lua setUndojoinFlag('v')<CR>gv", { noremap = true, silent = true })

-- Commands to append after (and insert before) any text object.
-- https://gist.github.com/wellle/9289224
_G.Append = function(op_type, ...)
  vim.cmd("normal! `]")  -- Jump to the end mark of the previous change
  if op_type == "char" then
    vim.fn.feedkeys("a", "n")
  else
    vim.fn.feedkeys("o", "n")
  end
end

_G.Insert = function(op_type, ...)
  vim.cmd("normal! `[")  -- Jump to the start mark of the previous change
  if op_type == "char" then
    vim.fn.feedkeys("i", "n")
  else
    vim.fn.feedkeys("O", "n")
  end
end

vim.keymap.set("n", ",a", ":set opfunc=v:lua.Append<CR>g@", { silent = true })
vim.keymap.set("n", ",i", ":set opfunc=v:lua.Insert<CR>g@", { silent = true })

--------------------------------------------------------------------------------
-- Abbrevations
--------------------------------------------------------------------------------
vim.cmd("cabbrev help tab help")
vim.cmd("cabbrev Q qa")
vim.cmd("cabbrev cwd %:h/")
vim.cmd("cabbrev File %:f")
vim.cmd("cabbrev ddate <expr> ddate strftime('%Y-%m-%d')")
vim.cmd("cabbrev ddate <expr> ddate strftime('%Y-%m-%d')")

--------------------------------------------------------------------------------
-- Functions and Commands
--------------------------------------------------------------------------------
-- vim.cmd("command! WipeReg for i in range(34,122) | silent! call setreg(nr2char(i), []) | endfor")
-- vim.cmd("command! EnableTabs set autoindent noexpandtab tabstop=4 shiftwidth=4")

--------------------------------------------------------------------------------
-- Auto Commands
--------------------------------------------------------------------------------
local nvimrc_group = vim.api.nvim_create_augroup("nvimrc_group", { clear = true })

-- Save and restore window view when switching buffers
-- local function AutoSaveWinView()
--   if not vim.w.SavedBufView then
--     vim.w.SavedBufView = {}
--   end
--   vim.w.SavedBufView[vim.fn.bufnr("%")] = vim.fn.winsaveview()
-- end
--
-- local function AutoRestoreWinView()
--   local buf = vim.fn.bufnr("%")
--   if vim.w.SavedBufView and vim.w.SavedBufView[buf] then
--     local v = vim.fn.winsaveview()
--     local atStartOfFile = (v.lnum == 1 and v.col == 0)
--     if atStartOfFile and not vim.opt.diff:get() then
--       vim.fn.winrestview(vim.w.SavedBufView[buf])
--     end
--     vim.w.SavedBufView[buf] = nil
--   end
-- end
--
-- vim.api.nvim_create_autocmd("BufLeave", { callback = AutoSaveWinView })
-- vim.api.nvim_create_autocmd("BufEnter", { callback = AutoRestoreWinView })

-- vim.api.nvim_create_autocmd({"CursorHold", "CursorHoldI"}, {
--   group = nvimrc_group,
--   pattern = "*",
--   command = "checktime"
-- })

-- vim.api.nvim_create_autocmd("BufWritePost", {
--   group = nvimrc_group,
--   pattern = vim.fn.expand("$MYVIMRC"),
--   command = "source $MYVIMRC"
-- })

-- Restore last position in buffer
vim.api.nvim_create_autocmd("BufWinEnter", {
  group = nvimrc_group,
  pattern = "*",
  callback = function()
    if vim.fn.line("'\"") <= vim.fn.line("$") then
      vim.cmd("normal! g`\"")
    end
  end,
})

-- vim.api.nvim_create_autocmd("TermOpen", {
--   group = nvimrc_group,
--   pattern = "*",
--   command = "setlocal statusline=%{b:terminal_job_id}: \\ %{b:term_title}"
-- })
--
-- vim.api.nvim_create_autocmd("FileType", {
--   group = nvimrc_group,
--   pattern = "fzf",
--   command = "tnoremap <nowait><buffer> <esc> <c-g>"
-- })

-- vim.api.nvim_create_autocmd("VimResized", {
--   group = nvimrc_group,
--   pattern = "*",
--   command = "wincmd ="
-- })

-- vim.api.nvim_create_autocmd("BufEnter", {
--   group = nvimrc_group,
--   pattern = "*",
--   callback = function()
--     if vim.bo.buftype == 'terminal' then
--       vim.cmd("startinsert")
--     end
--   end,
-- })

-- vim.api.nvim_create_autocmd("BufWritePost", {
--   group = nvimrc_group,
--   pattern = "*",
--   callback = function()
--     if vim.bo.diff then
--       vim.cmd("diffupdate")
--     end
--   end,
-- })

-- vim.api.nvim_create_autocmd("VimEnter", {
--   group = nvimrc_group,
--   pattern = "*",
--   command = "clearjumps"
-- })

-- vim.api.nvim_create_autocmd({"BufRead", "BufNewFile"}, {
--   group = nvimrc_group,
--   pattern = {"*.tmpl", "*.avsc"},
--   command = "set filetype=json"
-- })

-- vim.api.nvim_create_autocmd("QuickFixCmdPost", {
-- group = nvimrc_group,
--   pattern = "*grep
--   command = "cwindow"
-- })

vim.api.nvim_create_autocmd("FileType", {
  group = nvimrc_group,
  pattern = "ctrlsf",
  command = "setlocal cmdheight=1"
})

-- vim.api.nvim_create_autocmd("RecordingEnter", {
--   group = nvimrc_group,
--   pattern = "*",
--   command = "set cmdheight=1"
-- })

-- vim.api.nvim_create_autocmd("RecordingLeave", {
--   group = nvimrc_group,
--   pattern = "*",
--   command = "set cmdheight=0"
-- })
vim.api.nvim_create_autocmd("TextYankPost", {
  callback = function()
    vim.highlight.on_yank({ higroup = "Visual", timeout = 300 })
  end,
  desc = "Highlight yank text"
})

-- Strip trailing whitespace when saving
local function strip_whitespace()
  vim.cmd("%s/ \\+$//ge")
end

vim.api.nvim_create_autocmd("BufWritePre", {
  pattern = {"*.py", "*.lua", "*.yaml", "*.json", "*.nix"},
  callback = strip_whitespace,
  desc = "Strip trailing whitespace on save",
})

-- Disable diagnostics for neovim config files
vim.api.nvim_create_autocmd("BufEnter", {
  callback = function()
    local bufname = vim.api.nvim_buf_get_name(0)
    if bufname:match(vim.fn.expand("~/.dotfiles/nvim")) then
      vim.diagnostic.disable(0)
    end
  end,
  desc = "Disable diagnostics for Neovim config files",
})

-- Clear command line messages after 3 secs
-- vim.api.nvim_create_autocmd("CmdlineLeave", {
--   group = “someGroup”,
--   callback = function()
--     vim.fn.timer_start(3000, function()
--       vim.cmd('echom ""')
--     end)
--   end
-- })

-- Set a meaningful backup name, ex: %home%simon%dev%filename@2015-04-05.14:59
-- vim.api.nvim_create_autocmd("BufWritePre", {
--   pattern = "*",
--   callback = function()
--     vim.opt.backupext = '-' .. os.date("%F.%H:%M") .. '~'
--   end,
-- })

vim.api.nvim_create_autocmd("FileType", {
  pattern = "qf",
  callback = function(ev)
    local mapopts = { buffer = ev.buf, silent = true, noremap = true }
    -- Make q and <Esc> close the list when you're inside the quickfix window
    vim.keymap.set("n", "q", "<cmd>cclose<CR>", mapopts)
    vim.keymap.set("n", "<Esc>", "<cmd>cclose<CR>", mapopts)
  end,
})

-- Load plugins
require("config.lazy")

--------------------------------------------------------------------------------
-- Cursor Agent Float
--------------------------------------------------------------------------------
vim.keymap.set({"n", "t"}, "<F12>", function()
  require("cursor-agent-float").toggle()
end, { noremap = true, silent = true, desc = "Toggle cursor-agent" })

-- vim.keymap.set("n", "<leader>cn", function()
--   require("cursor-agent-float").new_session()
-- end, { noremap = true, silent = true, desc = "New cursor-agent session" })

-- vim.keymap.set("n", "<leader>cr", function()
--   require("cursor-agent-float").restart()
-- end, { noremap = true, silent = true, desc = "Restart cursor-agent" })

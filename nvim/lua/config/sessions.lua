local function find_project_name()
  local name = vim.fn.getcwd()
  if name ~= "" then
    name = string.gsub(name, "/", "")
  end
  return name
end

local function restore_session(name)
  if name ~= "" then
    local session_file = vim.fn.expand("$HOME") .. "/.local/share/nvim/sessions/" .. name .. ".vim"
    if vim.fn.filereadable(session_file) == 1 then
      vim.cmd("source " .. session_file)
    end
  end
end

local function save_session(name)
  if name ~= "" then
    local session_file = vim.fn.expand("$HOME") .. "/.local/share/nvim/sessions/" .. name .. ".vim"
    vim.cmd("mksession! " .. session_file)
  end
end

if vim.fn.argc() == 0 then
  vim.api.nvim_create_autocmd("VimEnter", {
    callback = function()
      restore_session(find_project_name())
    end,
    desc = "Restore session on VimEnter if no arguments provided",
  })
  vim.api.nvim_create_autocmd("VimLeave", {
    callback = function()
      save_session(find_project_name())
    end,
    desc = "Save session on VimLeave if no arguments provided",
  })
end

vim.opt.sessionoptions:remove("options")

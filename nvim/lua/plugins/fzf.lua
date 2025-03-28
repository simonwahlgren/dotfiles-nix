return {
  {
    "junegunn/fzf",
    build = "./install --bin",
    lazy = false,
  },
  {
    "junegunn/fzf.vim",
    dependencies = { "junegunn/fzf" },
    config = function()
      vim.keymap.set("n", "<C-f>", ":Files<CR>", { noremap = true, silent = true })
      vim.keymap.set("n", "<leader>ff", ":Rg! ", { noremap = true, silent = true })
      vim.keymap.set("n", "<leader>fd", ":Files <C-R>=expand('%:h')<CR><CR>", { noremap = true, silent = true })
      vim.keymap.set("n", "<leader>fw", ":Rg! <C-R><C-W><CR>", { noremap = true, silent = true })
      vim.keymap.set("n", "<leader>fe", ":BTags<CR>", { noremap = true, silent = true })
      vim.keymap.set("n", "<leader>ft", ":Tags<CR>", { noremap = true, silent = true })
      vim.keymap.set("n", "<C-b>", ":Buffers<CR>", { noremap = true, silent = true })

      local function build_quickfix_list(lines)
        local qflist = {}
        for _, filename in ipairs(lines) do
          table.insert(qflist, { filename = filename })
        end
        vim.fn.setqflist(qflist)
        vim.cmd("copen")
        vim.cmd("cc")
      end

      vim.g.fzf_action = {
        ["ctrl-q"] = build_quickfix_list,
        ["ctrl-t"] = "tab split",
        ["ctrl-h"] = "split",
        ["ctrl-v"] = "vsplit",
        ["enter"] = "e",
      }

      -- [Tags] Command to generate tags file
      local gitdir = vim.fn.trim(vim.fn.system("git rev-parse --git-dir 2>/dev/null")) .. "/tags"
      vim.o.tags = gitdir
      vim.g.fzf_tags_command = "ctags -f " .. gitdir

      vim.g.fzf_layout = { down = "~100%" }
      vim.g.fzf_history_dir = "~/.local/share/nvim/fzf-history"
      vim.g.fzf_buffers_jump = 1
      vim.g.fzf_files_options = '--preview "bat --color always {} | head -' .. vim.o.lines .. '"'
      vim.g.fzf_preview_window = "right:60%"

      -- Add preview window to Rg command
      vim.cmd([[
        command! -bang -nargs=* Rg call fzf#vim#grep(
        \ 'rg -F --column --line-number --hidden --glob "!.git" --no-heading --color=always --smart-case ' . shellescape(<q-args>), 1,
        \ <bang>0 ? fzf#vim#with_preview('right:60%') : fzf#vim#with_preview('right:60%:hidden', '?'),
        \ <bang>0)
      ]])

      -- Add preview window to the Files command
      vim.cmd([[
        command! -bang -nargs=? -complete=dir Files call fzf#vim#files(<q-args>, fzf#vim#with_preview('right:60%'), <bang>0)
      ]])
    end,
  },
}

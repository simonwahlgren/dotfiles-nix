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
      vim.keymap.set("n", "<leader>ff", ":Rg! ", { noremap = true, silent = false })
      vim.keymap.set("n", "<leader>fd", ":Files <C-R>=expand('%:h')<CR><CR>", { noremap = true, silent = true })
      vim.keymap.set("n", "<leader>fw", ":Rg! <C-R><C-W><CR>", { noremap = true, silent = false })
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

      -- [Tags] Command to generate tags file only if inside a Git repo
      local gitdir = nil
      local gitdir_job = vim.fn.jobstart({ "git", "rev-parse", "--git-dir" }, {
        stdout_buffered = true,
        on_stdout = function(_, data)
          if data and data[1] ~= "" then
            gitdir = vim.fn.trim(data[1])
          end
        end,
        -- on_stderr = function(_, err_data)
        --   if err_data and err_data[1] ~= "" then
        --     vim.notify("Git error: " .. table.concat(err_data, "\n"), vim.log.levels.WARN)
        --   end
        -- end
      })

      -- Wait for job to finish and check exit code
      local status = vim.fn.jobwait({ gitdir_job })[1]
      if status == 0 and gitdir then
        local tags_path = gitdir .. "/tags"
        vim.o.tags = tags_path
        vim.g.fzf_tags_command = "ctags -f " .. tags_path

        vim.api.nvim_create_autocmd("VimEnter", {
          callback = function()
            vim.fn.jobstart(vim.g.fzf_tags_command, { detach = true })
          end,
        })
      end

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

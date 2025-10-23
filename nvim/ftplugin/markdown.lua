vim.api.nvim_create_autocmd('FileType', {
  pattern = 'markdown',
  callback = function()
    vim.opt_local.formatoptions:remove('q') -- disable formatting of comments
    -- vim.opt_local.textwidth = 120
    vim.opt_local.wrap = false
    vim.opt_local.wrapmargin = 0
    vim.opt_local.linebreak = true

    vim.opt_local.smartindent = true
    vim.opt_local.spell = true
    vim.opt_local.spelllang = 'en_us'
    vim.opt_local.expandtab = true
    vim.opt_local.conceallevel = 0
    vim.opt_local.tabstop = 2
    vim.opt_local.shiftwidth = 2

    vim.keymap.set('n', 'j', 'gj', { buffer = true })
    vim.keymap.set('n', 'k', 'gk', { buffer = true })

    vim.keymap.set('n', ',Q', [[:g/- /norm $gq$<CR>''<ESC>]], { buffer = true })
    vim.keymap.set('v', ',Q', [[:g/- /norm $gq$<CR>]], { buffer = true })

    local function embed_screenshot()
      vim.cmd('r!screenshot_to_current_dir.sh -d ' .. vim.fn.expand('%:p:h'))
      vim.cmd([[s#^\(.*\/\)\([^\/]*\)\.png$#![\2](\0)#]])
    end

    local function markdown_preview()
      vim.cmd('AsyncRun! grip ' .. vim.fn.expand('%:p'))
      vim.fn.sleep(1000)
      vim.cmd('silent !xdg-open http://localhost:6419/')
    end

    vim.keymap.set('n', '<leader><F12>', embed_screenshot, { buffer = true })
    vim.keymap.set('n', ',mp', function()
      vim.cmd('silent !pkill grip')
      markdown_preview()
    end, { buffer = true })
    vim.keymap.set('n', ',ms', function()
      vim.cmd('silent !pkill grip')
    end, { buffer = true })
  end,
})

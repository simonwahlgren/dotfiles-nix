-- Cursor Agent floating terminal integration with session management
-- Add this to your init.lua

-- Toggle cursor-agent terminal (resumes previous session for this project)
vim.keymap.set('n', '<leader>ca', function()
  require('cursor-agent-float').toggle()
end, { desc = 'Toggle Cursor Agent terminal' })

-- Restart cursor-agent (same session, useful if terminal got stuck)
vim.keymap.set('n', '<leader>cR', function()
  require('cursor-agent-float').restart()
end, { desc = 'Restart Cursor Agent' })

-- Start a completely new chat session for current project
vim.keymap.set('n', '<leader>cN', function()
  require('cursor-agent-float').new_session()
end, { desc = 'New Cursor Agent session' })

-- Quick ask - prompts for a question about current project
vim.keymap.set('n', '<leader>cq', function()
  local question = vim.fn.input('Ask Cursor Agent: ')
  if question ~= '' then
    require('cursor-agent-float').ask(question)
  end
end, { desc = 'Ask Cursor Agent a question' })

-- Clear all saved sessions (rarely needed)
vim.keymap.set('n', '<leader>cC', function()
  require('cursor-agent-float').clear_all_sessions()
end, { desc = 'Clear all Cursor Agent sessions' })

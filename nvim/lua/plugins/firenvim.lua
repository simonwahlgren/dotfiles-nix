--[[
-- Seems not to work in vivaldi since 2026-04-16
-- Following the troubleshooting https://github.com/glacambre/firenvim/blob/master/TROUBLESHOOTING.md
-- under section "Make sure the browser extension can communicate with Neovim"
-- when inspecting the "background page" and Reload settings in e.g. Github, I get this error
  _generated_background_page.html:1 Uncaught (in promise) Neovim died without answering.
  Promise.then		
  updateSettings	@	background.ts:159
  updateSettings	@	background.ts:315
  (anonymous)	@	background.ts:326
  _generated_background_page.html:1 Unchecked runtime.lastError: Native host has exited.
--]]
return {
  {
    "glacambre/firenvim",
    enable = false,
    build = ":call firenvim#install(0)",
  }
}

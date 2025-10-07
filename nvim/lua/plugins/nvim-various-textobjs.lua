-- nvim-various-textobjs — Default Text Objects & Keybindings
--
-- Text Object             Description                               Keybindings
-- --------------------------------------------------------------------------------------
-- indentation             indent-based block                       ii, ai, aI, [iI]
-- restOfIndentation       remainder of indent block                R
-- greedyOuterIndentation  outer indent (incl. blank lines)          ag, ig
-- subword                 camelCase/snake/kebab part                iS, aS
-- toNextClosingBracket    cursor to next ], ), or }                 C
-- toNextQuotationMark     cursor to next unescaped quote            Q
-- anyQuote                inner/outer around quotes                 iq, aq
-- anyBracket              inner/outer around brackets               io, ao
-- restOfParagraph         like } motion, linewise                   r
-- entireBuffer            whole buffer as text object               gG
-- nearEoL                 cursor to end of line -1                  n
-- lineCharacterwise       current line (charwise)                   i_, a_
-- column                  vertical column selection                 |
-- value                   right side of assignment/value            iv, av
-- key                     left side of assignment/key               ik, ak
-- url                     protocol-based link (e.g., http)          L
-- number                  numeric literal (inner/outer)             in, an
-- diagnostic              Neovim diagnostic (LSP)                   !
-- closedFold              folded block (incl. one line)             iz, az
-- chainMember             part of chain `foo.bar`                   im, am
-- visibleInWindow         all visible lines                         gw
-- restOfWindow            from cursor to bottom of window           gW
-- lastChange              last non-deletion change                  g;
-- notebookCell            cell delimited by ‘# %%’                  iN, aN
-- emoji                   single emoji or glyph                     .
-- argument                comma-separated argument                  i, / a,
-- filepath                filename path (unix)                      iF, aF
-- color                   CSS hex/rgb/hsl or ANSI color             i#, a#
-- doubleSquareBrackets    text inside [[…]]                         iD, aD
-- mdLink (Markdown)       markdown link title                       il, al
-- mdEmphasis (Markdown)   markdown emphasis content                 ie, ae
-- mdFencedCodeBlock       fenced code block                         iC, aC
-- cssSelector (CSS/SCSS)  class selector                            ic, ac
-- htmlAttribute (HTML/XML) attribute value                          ix, ax
-- shellPipe (shell)       segment around pipe                       iP, aP
--
-- Notes:
--  • 'i' = inner (excluding delimiters), 'a' = around (including delimiters).
--  • Some mappings (C, Q) are motions (forward-seeking).
--  • Filetype-specific objects only load in their respective filetypes.
return {
  "chrisgrieser/nvim-various-textobjs",
  opts = {
    keymaps = {
      useDefaults = true
    }
  },
}

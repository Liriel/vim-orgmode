if (!has('nvim') && v:version < 802) || !has('python3')
	" ftplugin/org.vim reports the missing requirements
	finish
endif

" Delete the next line to avoid the special indention of items
if !exists("g:org_indent")
  let g:org_indent = 0
endif

setlocal indentexpr=GetOrgIndent()
setlocal nolisp
setlocal nosmartindent
setlocal autoindent

let s:py_env = 'python3 << EOF'

function! GetOrgIndent()
	if g:org_indent == 0
		return -1
	endif

exe s:py_env
from orgmode._vim import indent_orgmode
indent_orgmode()
EOF

	if exists('b:indent_level')
		let l:tmp = b:indent_level
		unlet b:indent_level
		return l:tmp
	else
		return -1
	endif
endfunction

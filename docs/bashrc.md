```bash
HISTSIZE=10000
HISTTIMEFORMAT="%F %T \$(whoami) "
shopt -s histappend
if [[ $- == *i* ]]
then
    bind '"\e[A": history-search-backward'
    bind '"\e[B": history-search-forward'
fi

if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

PS1="\[\e[37m\][\[\e[32m\]\u\[\e[37m\]@\h \[\e[35m\]\W\[\e[0m\]]\\$ "


```

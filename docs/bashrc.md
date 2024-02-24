```bash
# shell 退出时添加新记录
shopt -s histappend
# 方向键翻阅历史
if [[ $- == *i* ]]
then
    bind '"\e[A": history-search-backward'
    bind '"\e[B": history-search-forward'
fi
```

```conf
# /etc/anacrontab: configuration file for anacron

# See anacron(8) and anacrontab(5) for details.

SHELL=/bin/sh
PATH=/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=root
# the maximal random delay added to the base delay of the jobs
# RANDOM_DELAY=45
# 把最大随机廷迟改为0分钟,不再随机廷迟
RANDOM_DELAY=0
# the jobs will be started during the following hours only
# START_HOURS_RANGE=3-22
#执行时间范围为0-22
START_HOURS_RANGE=0-22

#period in days   delay in minutes   job-identifier   command
# 1     5       cron.daily              nice run-parts /etc/cron.daily
# 把强制延迟也改为0分钟,不再强制廷迟
1       0       cron.daily              nice run-parts /etc/cron.daily
7       25      cron.weekly             nice run-parts /etc/cron.weekly
@monthly 45     cron.monthly            nice run-parts /etc/cron.monthly
```

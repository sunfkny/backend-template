
https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/storage_administration_guide/ch-swapspace

 **Table 15.1. Recommended System Swap Space** 

| Amount of RAM in the system | Recommended swap space     | Recommended swap space if allowing for hibernation |
| :-------------------------- | :------------------------- | :------------------------------------------------- |
| ⩽ 2 GB                      | 2 times the amount of RAM  | 3 times the amount of RAM                          |
| > 2 GB – 8 GB               | Equal to the amount of RAM | 2 times the amount of RAM                          |
| > 8 GB – 64 GB              | At least 4 GB              | 1.5 times the amount of RAM                        |
| > 64 GB                     | At least 4 GB              | Hibernation not recommended                        |

```bash
# Create an empty file:
dd if=/dev/zero of=/swapfile bs=1M count=4096
# Set up the swap file with the command:
mkswap  /swapfile
# Change the security of the swap file so it is not world readable.
chmod 0600 /swapfile
# To enable the swap file at boot time, edit /etc/fstab as root to include the following entry
# /swapfile          swap            swap    defaults        0 0
cat /etc/fstab | grep swapfile
# Regenerate mount units so that your system registers the new /etc/fstab configuration
systemctl daemon-reload
# To activate the swap file immediately
swapon  /swapfile
# To test if the new swap file was successfully created and activated, inspect active swap space
cat /proc/swaps
free -h
```

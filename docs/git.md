```bash
yum install -y centos-release-scl
yum install -y rh-git227
echo '. /opt/rh/rh-git227/enable' >> ~/.bashrc
source ~/.bashrc
git --version  # git version 2.27.0
```

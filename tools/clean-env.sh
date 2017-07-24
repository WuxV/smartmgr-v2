/etc/init.d/smartscsi restart
sh ~/pal.sh target list detail | grep OK | awk '{print $1}' | xargs -I {} sh ~/pal.sh target del {}
sh ~/pal.sh pool   list detail | grep OK | awk '{print $1}' | xargs -I {} sh ~/pal.sh pool del   {}
sh ~/pal.sh disk   list detail | grep OK | awk '{print $1}' | xargs -I {} sh ~/pal.sh disk del   {}
rm /root/workspace/smartmgr-v2/files/conf/test/smartmgr.conf -rf

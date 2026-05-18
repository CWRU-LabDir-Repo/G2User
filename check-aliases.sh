#!/bin/bash
#
# check-aliases.sh
#
# Check and correct aliases.
#

aliases=/home/pi/.bashrc

grep preswap $aliases
if [ $? != 0 ]
then
    sed -i -e '$a \
\
alias preswap="sudo /home/pi/G2User/preswap.sh 2>&1 | sudo tee -a /home/pi/preswap.stat; sudo mv /home/pi/preswap.stat /home/pi/PSWS/Sstat"' $aliases
    echo -n "new "; grep preswap $aliases
fi

grep g2c $aliases
grep -q "alias g2c='python3 " $aliases
if [ $? == 0 ]
then
    sed -i -e "s/alias g2c='python3 \/home\/pi\/G2User\/G2console.py'/alias g2c='\/home\/pi\/G2User\/g2cstart.sh'/g" $aliases
    echo -n "new "; grep g2c $aliases
fi

grep "alias tcl" $aliases
if [ $? != 0 ]
then
    echo "alias tcl='tail --follow=name /home/pi/G2DATA/Slogs/console.log'" >> $aliases
    echo -n "new "; grep "alias tcl" $aliases
fi

grep "alias tdl" $aliases
if [ $? != 0 ]
then
    echo "alias tdl='tail --follow=name /home/pi/G2DATA/Slogs/dc.log'" >> $aliases
    echo -n "new "; grep "alias tdl" $aliases
fi

grep "alias tml" $aliases
if [ $? != 0 ]
then
    echo "alias tml='tail --follow=name /home/pi/G2DATA/Slogs/magdata.log'" >> $aliases
    echo -n "new "; grep "alias tml" $aliases
fi

#echo .bashrc contents:
#cat /home/pi/.bashrc



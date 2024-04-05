# Install, uninstall, or manage the grape2.service systemd service
# which manages the main data collection process "datactrlr"
#
# Must be run as root.
#
# usage:  sudo make

# name of the service to manage
SERVICE=grape2

# directory tree where to install the script
PREFIX=/usr/local


# action when calling with no argument
default: uninstall install enable start


# set the location of the installed script
# uncomment if this customization is needed
#$(SERVICE).service: $(SERVICE).service.in
#	sed 's,PREFIX,$(PREFIX),' $< > $@

install: $(SERVICE).service $(SERVICE).env
	#install --mode=755 $(SERVICE) $(PREFIX)/bin/
	install --mode=600 $(SERVICE).env /etc/default/
	install --mode=644 $(SERVICE).service /usr/lib/systemd/system/
	install -d /var/run/$(SERVICE)
	mkfifo /var/run/$(SERVICE)/datactrlr.fifo


uninstall: disable
	#rm $(PREFIX)/bin/$(SERVICE)
	rm /etc/default/$(SERVICE).env
	rm /usr/lib/systemd/system/$(SERVICE).service
	rm /var/run/$(SERVICE)/datactrlr.fifo

enable: install
	systemctl enable $(SERVICE).service

start: install reload
	systemctl start $(SERVICE).service

restart: install reload
	systemctl restart $(SERVICE).service

reload:
	systemctl daemon-reload

disable: stop
	systemctl disable $(SERVICE).service

stop:
	systemctl stop $(SERVICE).service


version = 0.1.6

.PHONY: all
all: clean docker-build

.PHONY: clean
clean: docker-rmi
	@rm -f *.pdf
	@# rm -f *.html

.PHONE: run
run:
	python3 api.py

.PHONY: docker-build
docker-build:
	sudo docker build . -t htmltopdf -t htmltopdf:${version}

.PHONY: docker-run
docker-run:
	sudo docker run -d --name htmltopdf -p 5000:5000 htmltopdf:${version}

.PHONY: docker-rmi
docker-rmi:
	@# https://www.gnu.org/software/make/manual/html_node/Errors.html#Errors-in-Recipes
	-sudo docker rmi htmltopdf
	sudo docker rmi $$(sudo docker images 'htmltopdf' -a -q)

.PHONY: check-docker-layers
check-docker-layers:
	sudo docker history htmltopdf:${version}


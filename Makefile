version = 0.1.6
image_name = htmltopdf
container_name = htmltopdf

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
	sudo docker build . -t ${image_name} -t ${image_name}:${version}

.PHONY: docker-run
docker-run:
	sudo docker run -d --name ${container_name} -p 5000:5000 ${image_name}:${version}

.PHONY: docker-stop
docker-stop:
	sudo docker rm -f ${container_name}

.PHONY: docker-rmi
docker-rmi:
	@# https://www.gnu.org/software/make/manual/html_node/Errors.html#Errors-in-Recipes
	-sudo docker rmi ${image_name}
	sudo docker rmi $$(sudo docker images '${image_name}' -a -q)

.PHONY: check-docker-layers
check-docker-layers:
	sudo docker history ${image_name}:${version}


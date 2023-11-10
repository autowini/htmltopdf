version = 0.4.3
image_name = htmltopdf
container_name = htmltopdf

.PHONY: all
all: clean

.PHONY: clean
clean: docker-rmi
	@rm -f *.pdf
	@# rm -f *.html

# app 실행
.PHONE: run
run:
	python3 app.py

# Dockerfile 이미지 빌드
.PHONY: docker-build
docker-build:
	sudo docker build . -t ${image_name} -t ${image_name}:${version} # --no-cache

# 빌드된 Docker 이미지로 컨테이너 생성
.PHONY: docker-run
docker-run:
	sudo docker run -d --name ${container_name} -p 5000:5000 -v ${PWD}/logs:/app/logs:rw ${image_name}:${version}

# Docker 컨테이너 중지 및 삭제
.PHONY: docker-stop
docker-stop:
	sudo docker rm -f ${container_name}

# 실행 중인 Docker 컨테이너 로그 확인
.PHONY: docker-logs
docker-logs:
	sudo docker logs -f ${container_name}

# Docker 이미지 삭제
.PHONY: docker-rmi
docker-rmi:
	@# https://www.gnu.org/software/make/manual/html_node/Errors.html#Errors-in-Recipes
	-sudo docker rmi ${image_name}
	sudo docker rmi $$(sudo docker images '${image_name}' -a -q)

# Docker 이미지 레이어 확인
.PHONY: check-docker-layers
check-docker-layers:
	sudo docker history ${image_name}:${version}

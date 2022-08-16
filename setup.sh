if ! type docker > /dev/null
then
  echo "docker does not exist"
  echo "Start installing docker"
  sudo apt-get update
  sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
  sudo apt update
  apt-cache policy docker-ce
  sudo apt install -y docker-ce
fi

if ! type docker-compose > /dev/null
then
  echo "docker-compose does not exist"
  echo "Start installing docker-compose"
  sudo curl -L "https://github.com/docker/compose/releases/download/1.27.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
fi

# Remove existing dangling docker-images
if [ $(docker images --quiet --filter=dangling=true | wc -l) -gt 0 ]
then
  echo "Dangling docker image exists..."
  docker rmi -f $(docker images -f dangling=true -q)
fi

# Remove all running containers and networks
if [ $(docker ps -q -a | wc -l) -gt 0 ]
then
  echo "More than one container is running..."
  docker-compose down
fi

# Build docker containers
docker-compose up -d --build
echo "Build Complete"

# Check running state of all 3 containers
if [ $(docker ps --format "{{.Names}} {{.Status}}" | grep "Up" | wc -l) -ne 3 ]
then
  echo "Build error while running docker-compose"
  exit 1
else
  echo "Deploy Complete"
fi
